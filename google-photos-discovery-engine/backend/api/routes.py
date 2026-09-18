import json
import logging
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from google import genai
import os

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")

class SearchQuery(BaseModel):
    query: str

async def _get_active_pool(request: Request):
    """Safely retrieves or creates the db pool."""
    pool = getattr(request.app.state, "pool", None)
    if not pool:
        from db.connection import get_pool
        from db.init_db import run_migrations
        from search.seed_data import seed_discovery_database
        pool = await get_pool()
        await run_migrations(pool)
        await seed_discovery_database(pool)
        request.app.state.pool = pool
    return pool

def canonicalize_source(raw_src: str | None) -> str | None:
    """Map raw platform names to clean, user-facing canonical source strings."""
    if not raw_src:
        return None
    s = str(raw_src).strip().lower()
    if s in ("", "unknown", "null", "none"):
        return None
    if "reddit" in s:
        return "Reddit"
    if "play" in s:
        return "Play Store"
    if "app_store" in s or "appstore" in s or "ios" in s:
        return "App Store"
    if "youtube" in s:
        return "YouTube Comment"
    if "help" in s or "forum" in s or "support" in s:
        return "Google Support Community"
    if "twitter" in s or s == "x":
        return "Twitter/X"
    return str(raw_src).replace("_", " ").title()

@router.get("/clusters")
async def get_clusters(request: Request):
    """Returns all clusters with their metadata and source-tagged quotes."""
    pool = await _get_active_pool(request)
    if not pool:
        return {"clusters": []}
        
    # Preload quote to source mapping from feedback_records
    quote_source_map = {}
    try:
        async with pool.execute("SELECT raw_text, source, source_platform, id FROM feedback_records") as cursor:
            fb_rows = await cursor.fetchall()
            for f in fb_rows:
                f_dict = dict(f)
                canon = f_dict.get("source") or canonicalize_source(f_dict.get("source_platform"))
                quote_source_map[f_dict["raw_text"]] = (canon, f_dict["id"])
    except Exception as e:
        logger.warning(f"Could not load quote_source_map: {e}")

    async with pool.execute("""
        SELECT cluster_id, label, description, record_count, 
               source_diversity, severity_score, top_failure_points, 
               representative_quotes
        FROM clusters
        ORDER BY severity_score DESC
    """) as cursor:
        rows = await cursor.fetchall()
        
    clusters = []
    missing_source_count = 0
    for r in rows:
        c = dict(r)
        c['source_diversity'] = json.loads(c['source_diversity'])
        c['top_failure_points'] = json.loads(c['top_failure_points'])
        raw_quotes = json.loads(c['representative_quotes'])
        
        formatted_quotes = []
        for q in raw_quotes:
            if isinstance(q, dict):
                text = q.get("text", "")
                src = q.get("source") or canonicalize_source(q.get("source_platform"))
                qid = q.get("id")
            else:
                text = q
                match_info = quote_source_map.get(text)
                src = match_info[0] if match_info else None
                qid = match_info[1] if match_info else None
                
            if not src:
                missing_source_count += 1
                logger.warning(f"[Missing Source] Complaint quote in cluster #{c['cluster_id']} has no source: '{text[:60]}...'. Flagged for backfill.")

            formatted_quotes.append({
                "id": qid,
                "text": text,
                "source": src,
                "cluster_id": c['cluster_id'],
                "cluster_label": c['label'],
                "severity_score": c['severity_score']
            })
            
        c['representative_quotes'] = formatted_quotes
        clusters.append(c)
        
    if missing_source_count > 0:
        logger.warning(f"Total representative complaint quotes missing source across clusters: {missing_source_count}")
        
    return {"clusters": clusters, "missing_source_count": missing_source_count}

@router.get("/clusters/{cluster_id}/records")
async def get_cluster_records(request: Request, cluster_id: int):
    """Returns raw feedback records associated with a specific cluster."""
    pool = await _get_active_pool(request)
    if not pool:
        return {"records": []}
        
    async with pool.execute("""
        SELECT id, cluster_id, source, source_platform, raw_text, photo_type, 
               remembered_attributes, forgotten_attributes, 
               search_strategy, failure_point, workaround, emotional_signal
        FROM feedback_records
        WHERE cluster_id = ?
        ORDER BY created_at DESC
    """, (cluster_id,)) as cursor:
        rows = await cursor.fetchall()
        
    records = []
    missing_source_count = 0
    for r in rows:
        item = dict(r)
        canonical_src = item.get("source") or canonicalize_source(item.get("source_platform"))
        if not canonical_src:
            missing_source_count += 1
            logger.warning(f"[Missing Source] Complaint record #{item['id']} has no source platform (raw='{item.get('source_platform')}'). Flagged for backfill.")
        item["source"] = canonical_src
        records.append(item)
        
    if missing_source_count > 0:
        logger.warning(f"Cluster #{cluster_id} has {missing_source_count} records missing source values.")
        
    return {"records": records, "missing_source_count": missing_source_count}

@router.get("/synthesis")
async def get_synthesis(request: Request):
    """Returns all AI-synthesized strategic Q&A pairs from database."""
    pool = request.app.state.pool
    if pool:
        try:
            async with pool.execute("""
                SELECT question_id, question_text, answer_text, evidence 
                FROM synthesis_answers 
                ORDER BY question_id ASC
            """) as cursor:
                rows = await cursor.fetchall()
                if rows:
                    res = []
                    for r in rows:
                        item = dict(r)
                        try:
                            item['evidence'] = json.loads(item['evidence'])
                        except Exception:
                            pass
                        res.append(item)
                    return {"synthesis": res}
        except Exception as e:
            logger.warning(f"Failed to load synthesis from DB: {e}")

    try:
        from api.mock_data import MOCK_SYNTHESIS
        return {"synthesis": MOCK_SYNTHESIS}
    except Exception:
        return {"synthesis": []}

@router.post("/test-search")
async def test_search(request: Request, query_data: SearchQuery):
    """
    Semantic search endpoint for user complaints.
    1. Embeds the user's query using Gemini (or falls back gracefully).
    2. Computes cosine distance against cluster centroids in NumPy.
    3. Computes cosine distance against feedback_records in NumPy.
    4. Gated by calibrated similarity threshold.
    """
    import numpy as np
    pool = await _get_active_pool(request)
    if not pool:
        from api.mock_data import mock_search_response
        return mock_search_response(query_data.query)
        
    SIMILARITY_THRESHOLD = 0.35

    # Attempt embedding with Gemini
    api_key = os.getenv("GEMINI_API_KEY")
    query_embedding = None
    if api_key:
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.embed_content(
                model="gemini-embedding-2",
                contents=query_data.query
            )
            if response and response.embeddings:
                query_embedding = response.embeddings[0].values
        except Exception as e:
            logger.warning(f"Gemini embed_content failed: {e}")

    # If embedding failed or no key, fall back to mock search response
    if not query_embedding:
        logger.info("Using mock/lexical fallback for complaint search")
        from api.mock_data import mock_search_response
        return mock_search_response(query_data.query)

    try:
        q_vec = np.array(query_embedding, dtype=np.float32)
        q_norm = float(np.linalg.norm(q_vec))
        if q_norm < 1e-9:
            q_norm = 1.0

        # 2. Find Closest Cluster (Cosine Distance via NumPy)
        async with pool.execute("SELECT cluster_id, label, description, severity_score, centroid FROM clusters WHERE centroid IS NOT NULL") as cursor:
            cluster_rows = await cursor.fetchall()

        nearest_cluster = None
        min_cluster_dist = float("inf")
        for r in cluster_rows:
            c_dict = dict(r)
            centroid_blob = c_dict.pop("centroid", None)
            if centroid_blob:
                c_vec = np.frombuffer(centroid_blob, dtype=np.float32)
                c_norm = float(np.linalg.norm(c_vec))
                sim = float(np.dot(q_vec, c_vec)) / max(q_norm * c_norm, 1e-9)
                dist = max(0.0, 1.0 - sim)
                if dist < min_cluster_dist:
                    min_cluster_dist = dist
                    c_dict["distance"] = round(dist, 4)
                    nearest_cluster = c_dict

        is_confident_match = bool(
            nearest_cluster and nearest_cluster.get("distance", 1.0) <= SIMILARITY_THRESHOLD
        )

        # 3. Find Top 5 Similar Records (Cosine Distance via NumPy)
        async with pool.execute("SELECT id, cluster_id, source, source_platform, raw_text, failure_point, search_strategy, embedding FROM feedback_records WHERE embedding IS NOT NULL") as cursor:
            records_rows = await cursor.fetchall()

        records_with_dist = []
        missing_source_count = 0
        for r in records_rows:
            item = dict(r)
            emb_blob = item.pop("embedding", None)
            if emb_blob:
                r_vec = np.frombuffer(emb_blob, dtype=np.float32)
                r_norm = float(np.linalg.norm(r_vec))
                sim = float(np.dot(q_vec, r_vec)) / max(q_norm * r_norm, 1e-9)
                dist = max(0.0, 1.0 - sim)
                item["distance"] = round(dist, 4)
                item["is_confident"] = bool(dist <= SIMILARITY_THRESHOLD)
                
                canonical_src = item.get("source") or canonicalize_source(item.get("source_platform"))
                if not canonical_src:
                    missing_source_count += 1
                    logger.warning(f"[Missing Source] Nearest complaint record #{item['id']} has no source platform (raw='{item.get('source_platform')}'). Flagged for backfill.")
                item["source"] = canonical_src
                records_with_dist.append(item)

        records_with_dist.sort(key=lambda x: x["distance"])
        similar_records = records_with_dist[:5]

        if missing_source_count > 0:
            logger.warning(f"Total candidate complaints evaluated missing source: {missing_source_count}")

        return {
            "query": query_data.query,
            "is_confident_match": is_confident_match,
            "threshold": SIMILARITY_THRESHOLD,
            "nearest_cluster": nearest_cluster,
            "similar_records": similar_records
        }
            
    except Exception as e:
        logger.error(f"Semantic search failed: {e}")
        from api.mock_data import mock_search_response
        return mock_search_response(query_data.query)


# -------------------------------------------------------------
# Photos Discovery Engine: Hybrid Retrieval & Benchmark Routes
# -------------------------------------------------------------

class PhotoSearchRequest(BaseModel):
    query: str
    user_id: str = "default_user"

@router.post("/photos/search")
async def search_photos(request: Request, body: PhotoSearchRequest):
    """
    Executes hybrid search across face, pet, temporal, spatial, and visual indices
    with tiered graceful degradation.
    """
    pool = await _get_active_pool(request)
    from search.search_engine import HybridSearchOrchestrator
    orchestrator = HybridSearchOrchestrator()
    response = await orchestrator.search(pool, body.query, body.user_id)
    return response.model_dump()

@router.post("/photos/parse")
async def parse_photo_query(body: PhotoSearchRequest):
    """
    Directly tests the Query Understanding NLU parser.
    Extracts people, pets, temporal bounds, spatial bounds, and visual residual.
    """
    from search.query_understanding import QueryUnderstandingEngine
    parser = QueryUnderstandingEngine()
    parsed = parser.parse(body.query)
    return parsed.model_dump()

@router.get("/photos/benchmark")
async def get_benchmark_results(request: Request):
    """
    Executes the 25-query benchmark test suite across all 4 clusters
    and returns pass/fail statistics, precision, recall, and latency.
    """
    pool = await _get_active_pool(request)
    from search.benchmark_runner import run_benchmark
    results = await run_benchmark(pool)
    return results

@router.get("/photos/catalog")
async def get_photo_catalog(request: Request):
    """Returns the indexed photos, people, and pets catalog."""
    pool = await _get_active_pool(request)
        
    async with pool.execute("SELECT * FROM photos ORDER BY captured_at_utc DESC") as cursor:
        photos = [dict(r) for r in await cursor.fetchall()]
        for p in photos:
            p["visual_tags"] = json.loads(p["visual_tags"])
            
    async with pool.execute("SELECT * FROM people") as cursor:
        people = [dict(r) for r in await cursor.fetchall()]
        for p in people:
            p["aliases"] = json.loads(p["aliases"])
            
    async with pool.execute("SELECT * FROM pets") as cursor:
        pets = [dict(r) for r in await cursor.fetchall()]
        for p in pets:
            p["aliases"] = json.loads(p["aliases"])
            
    return {
        "total_photos": len(photos),
        "photos": photos,
        "people": people,
        "pets": pets
    }

