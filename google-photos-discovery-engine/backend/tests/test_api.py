import pytest
from httpx import AsyncClient, ASGITransport
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from api.main import app

@pytest.mark.asyncio
async def test_read_root():
    """Test the root endpoint."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert "message" in response.json()

@pytest.mark.asyncio
async def test_get_clusters():
    """Test the clusters endpoint."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/clusters")
    assert response.status_code == 200
    data = response.json()
    assert "clusters" in data
    assert isinstance(data["clusters"], list)

@pytest.mark.asyncio
async def test_get_synthesis():
    """Test the AI synthesis endpoint."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/synthesis")
    assert response.status_code == 200
    data = response.json()
    assert "synthesis" in data
    assert isinstance(data["synthesis"], list)

@pytest.mark.asyncio
async def test_photos_parse_endpoint():
    """Test the photo query understanding endpoint."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/photos/parse", json={"query": "Mom with Charlie at the beach in Maui in Summer 2018"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["people"]) == 1
    assert data["people"][0]["canonical_name"] == "Mom"
    assert len(data["pets"]) == 1
    assert data["pets"][0]["resolved_pet_id"] == "pet_charlie"
    assert data["spatial"]["city"] == "Maui"
    assert data["temporal"]["raw_mention"] == "Summer 2018"

@pytest.mark.asyncio
async def test_photos_search_endpoint():
    """Test the hybrid photos search endpoint."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/photos/search", json={"query": "Mom at the beach in 2018"})
    assert response.status_code == 200
    data = response.json()
    assert data["total_results"] >= 1
    assert data["execution_tier"] == "TIER_1_EXACT_INTERSECTION"
    top_hit = data["results"][0]
    assert top_hit["photo_id"] == "p_mom_beach_2018"

@pytest.mark.asyncio
async def test_photos_benchmark_endpoint():
    """Test the benchmark runner endpoint."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/photos/benchmark")
    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["total_queries"] == 25
    assert data["summary"]["pass_rate_pct"] == 100.0
    assert data["summary"]["status"] == "PASS"

@pytest.mark.asyncio
async def test_cluster_detail_records_populated():
    """Verify Bug 1 fix: cluster detail endpoint returns non-empty records."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        for cid in [1, 2, 3, 4]:
            res = await ac.get(f"/api/clusters/{cid}/records")
            assert res.status_code == 200
            data = res.json()
            assert "records" in data
            assert len(data["records"]) > 0, f"Cluster #{cid} should have records populated"

@pytest.mark.asyncio
async def test_search_threshold_gating():
    """Verify Bug 2 fix: 0.35 distance threshold correctly gates confident vs out-of-domain."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. In-domain query (should be confident match)
        res_in = await ac.post("/api/test-search", json={"query": "search by tagged face returns no results"})
        assert res_in.status_code == 200
        data_in = res_in.json()
        assert data_in["is_confident_match"] is True
        assert data_in["nearest_cluster"]["cluster_id"] == 1
        assert data_in["nearest_cluster"]["distance"] <= 0.35

        # 2. Out-of-domain query (should be rejected by 0.35 threshold)
        res_out = await ac.post("/api/test-search", json={"query": "i cant find green saree"})
        assert res_out.status_code == 200
        data_out = res_out.json()
        assert data_out["is_confident_match"] is False
        assert data_out["nearest_cluster"]["distance"] > 0.35


