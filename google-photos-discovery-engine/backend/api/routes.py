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
        pool = await get_pool()
        await run_migrations(pool)
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
        
    async with pool.execute("""
        SELECT cluster_id, label, description, severity_score, top_failure_points
        FROM clusters
        ORDER BY severity_score DESC
    """) as cursor:
        rows = await cursor.fetchall()
        
    clusters = []
    missing_source_count = 0
    for r in rows:
        c = dict(r)
        c['top_failure_points'] = json.loads(c.get('top_failure_points', '[]'))
        cid = c['cluster_id']
        
        # 1. Real Record Count and Relevance states
        async with pool.execute("""
            SELECT count(*), 
                   SUM(CASE WHEN is_retrieval_relevant = 1 THEN 1 ELSE 0 END),
                   SUM(CASE WHEN is_retrieval_relevant = 0 THEN 1 ELSE 0 END),
                   SUM(CASE WHEN is_retrieval_relevant IS NULL THEN 1 ELSE 0 END)
            FROM feedback_records WHERE cluster_id = ?
        """, (cid,)) as cursor:
            row = await cursor.fetchone()
            c['record_count'] = row[0]
            c['confirmed_relevant'] = row[1] or 0
            c['confirmed_irrelevant'] = row[2] or 0
            c['unverified'] = row[3] or 0
            
        # 2. Real Source Diversity
        async with pool.execute("SELECT source, source_platform, count(*) as cnt FROM feedback_records WHERE cluster_id = ? GROUP BY source, source_platform", (cid,)) as cursor:
            src_rows = await cursor.fetchall()
            
        s_div = {}
        for sr in src_rows:
            canon = sr[0] or canonicalize_source(sr[1])
            if canon:
                s_div[canon] = s_div.get(canon, 0) + sr[2]
        
        # Calculate percentages for the frontend
        total_cluster_records = sum(s_div.values()) or 1
        s_div_percentages = {s: round((cnt / total_cluster_records) * 100, 1) for s, cnt in s_div.items()}
        c['source_diversity'] = s_div_percentages
        
        # 3. Representative Quotes
        async with pool.execute("""
            SELECT id, raw_text, source, source_platform, remembered_attributes, 
                   forgotten_attributes, search_strategy, failure_point, workaround, 
                   emotional_signal 
            FROM feedback_records 
            WHERE cluster_id = ? AND length(raw_text) > 40 
            LIMIT 3
        """, (cid,)) as cursor:
            quote_rows = await cursor.fetchall()
            
        formatted_quotes = []
        for qr in quote_rows:
            qr_dict = dict(qr)
            canon = qr_dict.get("source") or canonicalize_source(qr_dict.get("source_platform"))
            
            if not canon:
                missing_source_count += 1
                logger.warning(f"[Missing Source] Complaint quote in cluster #{cid} has no source: '{qr_dict.get('raw_text', '')[:60]}...'. Flagged for backfill.")
                
            formatted_quotes.append({
                "id": qr_dict.get("id"),
                "text": qr_dict.get("raw_text"),
                "source": canon,
                "cluster_id": cid,
                "cluster_label": c['label'],
                "severity_score": c['severity_score'],
                "remembered_attributes": qr_dict.get("remembered_attributes"),
                "forgotten_attributes": qr_dict.get("forgotten_attributes"),
                "search_strategy": qr_dict.get("search_strategy"),
                "failure_point": qr_dict.get("failure_point"),
                "workaround": qr_dict.get("workaround"),
                "emotional_signal": qr_dict.get("emotional_signal")
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

@router.get("/coverage")
async def get_coverage(request: Request):
    """Returns total corpus size and counts grouped by source."""
    pool = await _get_active_pool(request)
    if not pool:
        try:
            from api.mock_data import MOCK_COVERAGE
            return MOCK_COVERAGE
        except Exception:
            return {"total_corpus": 0, "source_counts": {}}
        
    async with pool.execute("SELECT source, count(*) as cnt FROM feedback_records GROUP BY source") as cursor:
        counts_raw = await cursor.fetchall()
        
    source_counts = {}
    for r in counts_raw:
        src = r[0]
        cnt = r[1]
        if src:
            canon = canonicalize_source(src)
            if canon:
                source_counts[canon] = source_counts.get(canon, 0) + cnt
            
    async with pool.execute("SELECT SUM(CASE WHEN is_retrieval_relevant = 1 THEN 1 ELSE 0 END) FROM feedback_records") as cursor:
        relevant_complaints = (await cursor.fetchone())[0] or 0
        
    return {
        "total_corpus": sum(source_counts.values()),
        "source_counts": source_counts,
        "relevant_complaints": relevant_complaints
    }

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
        
    SIMILARITY_THRESHOLD = 0.45

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
        async with pool.execute("SELECT id, cluster_id, source, source_platform, raw_text, remembered_attributes, forgotten_attributes, search_strategy, failure_point, workaround, emotional_signal, embedding FROM feedback_records WHERE embedding IS NOT NULL") as cursor:
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


@router.get("/pipeline-funnel")
async def get_pipeline_funnel(request: Request):
    """
    Returns pipeline diagnostic funnel data:
    Raw Ingested -> Evaluated by LLM -> Passed Relevance -> Extracted -> Embedded -> Clustered -> Breakdown.
    """
    from scripts.pipeline_funnel_diagnostic import get_funnel_data
    return get_funnel_data()

@router.get("/evidence")
async def get_evidence(
    request: Request,
    page: int = 1,
    limit: int = 25,
    search: str | None = None,
    source: str | None = None,
    cluster_id: int | None = None,
    emotion: str | None = None
):
    """
    Returns paginated scraped evidence records from the full 12,000+ dataset,
    modeled after the Myntra Discovery Engine Evidence Explorer.
    """
    pool = await _get_active_pool(request)
    limit = max(1, min(100, limit))
    page = max(1, page)
    offset = (page - 1) * limit

    conditions = []
    params = []

    if search:
        conditions.append("(raw_text LIKE ? OR failure_point LIKE ? OR photo_type LIKE ?)")
        search_param = f"%{search.strip()}%"
        params.extend([search_param, search_param, search_param])

    if source and source.lower() != "all":
        conditions.append("source = ?")
        params.append(source)

    if cluster_id is not None:
        conditions.append("cluster_id = ?")
        params.append(cluster_id)

    if emotion and emotion.lower() != "all":
        conditions.append("emotional_signal = ?")
        params.append(emotion.lower())

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    # Total matching count
    count_sql = f"SELECT count(*) FROM feedback_records {where_clause}"
    async with pool.execute(count_sql, params) as cursor:
        total = (await cursor.fetchone())[0]

    # Cluster name mapping
    cluster_names = {
        0: "Missing Photos and Albums",
        1: "Broken Photo Search Functionality",
        2: "Difficulty locating recently added media",
        3: "Frustrating UI and Search Redesign"
    }

    # Fetch paginated rows
    data_sql = f"""
        SELECT id, source, raw_text, photo_type, search_strategy,
               failure_point, emotional_signal, cluster_id, created_at
        FROM feedback_records
        {where_clause}
        ORDER BY id ASC
        LIMIT ? OFFSET ?
    """
    fetch_params = params + [limit, offset]
    async with pool.execute(data_sql, fetch_params) as cursor:
        rows = [dict(r) for r in await cursor.fetchall()]

    for r in rows:
        r["cluster_name"] = cluster_names.get(r.get("cluster_id"), f"Cluster #{r.get('cluster_id')}")

    # Aggregates across full corpus
    async with pool.execute("SELECT source, count(*) FROM feedback_records GROUP BY source") as cursor:
        source_counts = dict(await cursor.fetchall())

    async with pool.execute("SELECT cluster_id, count(*) FROM feedback_records GROUP BY cluster_id") as cursor:
        cluster_counts = dict(await cursor.fetchall())

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit if total > 0 else 1,
        "records": rows,
        "total_corpus": sum(source_counts.values()),
        "source_counts": source_counts,
        "cluster_counts": cluster_counts
    }



