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

@router.get("/clusters")
async def get_clusters(request: Request):
    """Returns all clusters with their metadata."""
    pool = await _get_active_pool(request)
    if not pool:
        return {"clusters": []}
        
    async with pool.execute("""
        SELECT cluster_id, label, description, record_count, 
               source_diversity, severity_score, top_failure_points, 
               representative_quotes
        FROM clusters
        ORDER BY severity_score DESC
    """) as cursor:
        rows = await cursor.fetchall()
        
    clusters = []
    for r in rows:
        c = dict(r)
        c['source_diversity'] = json.loads(c['source_diversity'])
        c['top_failure_points'] = json.loads(c['top_failure_points'])
        c['representative_quotes'] = json.loads(c['representative_quotes'])
        clusters.append(c)
        
    return {"clusters": clusters}

@router.get("/clusters/{cluster_id}/records")
async def get_cluster_records(request: Request, cluster_id: int):
    """Returns raw feedback records associated with a specific cluster."""
    pool = request.app.state.pool
    if not pool:
        return {"records": []}
        
    async with pool.execute("""
        SELECT id, source_platform, raw_text, photo_type, 
               remembered_attributes, forgotten_attributes, 
               search_strategy, failure_point, workaround, emotional_signal
        FROM feedback_records
        WHERE cluster_id = ?
        ORDER BY created_at DESC
    """, (cluster_id,)) as cursor:
        rows = await cursor.fetchall()
        return {"records": [dict(r) for r in rows]}

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
    1. Embeds the user's query using Gemini.
    2. Uses sqlite-vec to find the closest matching cluster.
    3. Uses a calibrated 0.35 cosine distance threshold to gate confident matches vs out-of-domain.
    4. Finds the top similar historical user complaints with confidence tags.
    """
    pool = await _get_active_pool(request)
    if not pool:
        raise HTTPException(status_code=503, detail="Database not ready")
        
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    import struct
    
    SIMILARITY_THRESHOLD = 0.35

    try:
        # 1. Embed Query
        logger.info(f"Generating embedding for query: '{query_data.query}'")
        response = client.models.embed_content(
            model="gemini-embedding-2",
            contents=query_data.query
        )
        query_embedding = response.embeddings[0].values
        query_blob = struct.pack(f"{len(query_embedding)}f", *query_embedding)
        
        # 2. Find Closest Cluster (Cosine Distance)
        async with pool.execute("""
            SELECT cluster_id, label, description, severity_score,
                   vec_distance_cosine(centroid, ?) AS distance
            FROM clusters
            WHERE centroid IS NOT NULL
            ORDER BY distance ASC
            LIMIT 1
        """, (query_blob,)) as cursor:
            cluster_row = await cursor.fetchone()
            
        nearest_cluster = dict(cluster_row) if cluster_row else None
        
        # Determine confidence based on 0.35 threshold
        is_confident_match = bool(
            nearest_cluster and nearest_cluster.get("distance") is not None and nearest_cluster["distance"] <= SIMILARITY_THRESHOLD
        )
        
        # 3. Find Top 5 Similar Records (Cosine Distance)
        async with pool.execute("""
            SELECT id, cluster_id, raw_text, failure_point, search_strategy,
                   vec_distance_cosine(embedding, ?) AS distance
            FROM feedback_records
            WHERE embedding IS NOT NULL
            ORDER BY distance ASC
            LIMIT 5
        """, (query_blob,)) as cursor:
            records_rows = await cursor.fetchall()
            
        similar_records = []
        for r in records_rows:
            item = dict(r)
            item["is_confident"] = bool(item.get("distance") is not None and item["distance"] <= SIMILARITY_THRESHOLD)
            similar_records.append(item)
        
        return {
            "query": query_data.query,
            "is_confident_match": is_confident_match,
            "threshold": SIMILARITY_THRESHOLD,
            "nearest_cluster": nearest_cluster,
            "similar_records": similar_records
        }
            
    except Exception as e:
        logger.error(f"Semantic search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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

