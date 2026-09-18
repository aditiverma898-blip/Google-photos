"""
Comprehensive Test Suite for Photos Discovery Engine.
Verifies Query Understanding, Hybrid Multi-Index Retrieval,
Tiered Graceful Degradation, and executes the 25 Labeled Benchmark Queries.
"""

import pytest
import aiosqlite
from db.connection import get_pool
from db.init_db import run_migrations
from search.seed_data import seed_discovery_database
from search.query_understanding import QueryUnderstandingEngine
from search.search_engine import HybridSearchOrchestrator
from search.benchmark_runner import run_benchmark, BENCHMARK_TEST_SUITE

import asyncio

async def _init_test_db():
    pool = await get_pool()
    await run_migrations(pool)
    await seed_discovery_database(pool)
    return pool

# -------------------------------------------------------------
# 1. Query Understanding Tests
# -------------------------------------------------------------

def test_query_understanding_people():
    parser = QueryUnderstandingEngine()
    parsed = parser.parse("Mom and Dad cooking in kitchen")
    assert len(parsed.people) == 2
    names = {p.canonical_name for p in parsed.people}
    assert "Mom" in names and "Dad" in names
    assert "cooking" in parsed.visual_residual.detected_tags

def test_query_understanding_pets():
    parser = QueryUnderstandingEngine()
    parsed = parser.parse("Charlie sleeping on the couch")
    assert len(parsed.pets) == 1
    assert parsed.pets[0].resolved_pet_id == "pet_charlie"
    assert "sleeping" in parsed.visual_residual.detected_tags

def test_query_understanding_temporal_seasons():
    parser = QueryUnderstandingEngine()
    parsed = parser.parse("Summer 2018 road trip")
    assert parsed.temporal is not None
    assert parsed.temporal.start_utc.startswith("2018-06-01")
    assert parsed.temporal.end_utc.startswith("2018-08-31")

def test_query_understanding_spatial():
    parser = QueryUnderstandingEngine()
    parsed = parser.parse("Sunset in Maui")
    assert parsed.spatial is not None
    assert parsed.spatial.city == "Maui"
    assert parsed.spatial.country == "USA"
    assert "sunset" in parsed.visual_residual.detected_tags

def test_query_understanding_compound_5way():
    parser = QueryUnderstandingEngine()
    parsed = parser.parse("Mom with Charlie at the beach in Maui in Summer 2018")
    assert len(parsed.people) == 1 and parsed.people[0].canonical_name == "Mom"
    assert len(parsed.pets) == 1 and parsed.pets[0].resolved_pet_id == "pet_charlie"
    assert parsed.spatial is not None and parsed.spatial.city == "Maui"
    assert parsed.temporal is not None and parsed.temporal.start_utc.startswith("2018-06-01")
    assert "beach" in parsed.visual_residual.detected_tags


# -------------------------------------------------------------
# 2. Hybrid Retrieval Tests
# -------------------------------------------------------------

def test_face_tagging_precision_and_negative_control():
    async def _test():
        db = await _init_test_db()
        orchestrator = HybridSearchOrchestrator()
        res = await orchestrator.search(db, "Mom at the beach in 2018")
        assert res.total_results >= 1
        hit_ids = [r.photo_id for r in res.results]
        assert "p_mom_beach_2018" in hit_ids
        # Negative control: stranger at beach in 2023 MUST NOT match
        assert "p_neg_beach_2023_stranger" not in hit_ids
    asyncio.run(_test())

def test_pet_fine_grained_species_separation():
    async def _test():
        db = await _init_test_db()
        orchestrator = HybridSearchOrchestrator()
        res = await orchestrator.search(db, "Black cat by the window")
        hit_ids = [r.photo_id for r in res.results]
        assert "p_black_cat_window" in hit_ids
        # Negative control: black dog MUST NOT match cat query
        assert "p_neg_black_dog_window" not in hit_ids
    asyncio.run(_test())

def test_date_range_strict_interval():
    async def _test():
        db = await _init_test_db()
        orchestrator = HybridSearchOrchestrator()
        res = await orchestrator.search(db, "Eiffel Tower trip in October 2019")
        hit_ids = [r.photo_id for r in res.results]
        assert "p_eiffel_oct_2019" in hit_ids
        # Negative control: Eiffel Tower in 2023 must NOT match Oct 2019
        assert "p_neg_paris_2023" not in hit_ids
    asyncio.run(_test())

def test_compound_5way_retrieval():
    async def _test():
        db = await _init_test_db()
        orchestrator = HybridSearchOrchestrator()
        res = await orchestrator.search(db, "Mom with Charlie at the beach in Maui in Summer 2018")
        assert res.total_results >= 1
        assert res.execution_tier == "TIER_1_EXACT_INTERSECTION"
        top_hit = res.results[0]
        assert top_hit.photo_id == "p_mom_charlie_maui_2018"
        assert "Wailea" in top_hit.landmark or "Kaanapali" in top_hit.landmark or "Maui" in top_hit.city
    asyncio.run(_test())

# -------------------------------------------------------------
# 3. Full Benchmark Suite: All 25 Labeled Queries
# -------------------------------------------------------------

def test_full_benchmark_suite():
    async def _test():
        db = await _init_test_db()
        benchmark_report = await run_benchmark(db)
        summary = benchmark_report["summary"]
        print("\nBenchmark Summary:", summary)
        print("Cluster Breakdown:", benchmark_report["cluster_breakdown"])

        assert summary["total_queries"] == len(BENCHMARK_TEST_SUITE)
        assert summary["failed"] == 0
        assert summary["pass_rate_pct"] == 100.0
        assert summary["status"] == "PASS"
    asyncio.run(_test())
