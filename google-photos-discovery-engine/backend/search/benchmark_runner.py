"""
Benchmark Runner for Photos Discovery Engine.
Runs the 25 labeled test cases across the 4 failure clusters and compound constraints.
"""

import logging
import aiosqlite
from typing import List, Dict, Any
from pydantic import BaseModel
from search.search_engine import HybridSearchOrchestrator

logger = logging.getLogger(__name__)

# The 25 benchmark queries defined in Step 4
BENCHMARK_TEST_SUITE = [
    # Cluster 1: Face Tagging & Entity Constraints
    {
        "id": "C1-01",
        "cluster": "Face Tagging",
        "query": "Mom at the beach in 2018",
        "expected_photo_ids": ["p_mom_beach_2018"],
        "disallowed_photo_ids": ["p_neg_beach_2023_stranger"],
        "criteria": "Photo must feature Mom at a beach taken in 2018; must reject stranger at beach in 2023."
    },
    {
        "id": "C1-02",
        "cluster": "Face Tagging",
        "query": "David graduation party May 2021",
        "expected_photo_ids": ["p_david_grad_2021"],
        "disallowed_photo_ids": [],
        "criteria": "Photo must feature David in graduation context strictly in May 2021."
    },
    {
        "id": "C1-03",
        "cluster": "Face Tagging",
        "query": "Me and Sarah skiing last winter",
        "expected_photo_ids": ["p_sarah_me_ski_2026"],
        "disallowed_photo_ids": [],
        "criteria": "Must require co-presence of both Sarah and Me in ski/snow scene."
    },
    {
        "id": "C1-04",
        "cluster": "Face Tagging",
        "query": "Grandpa in the garden",
        "expected_photo_ids": ["p_grandpa_garden_2023"],
        "disallowed_photo_ids": [],
        "criteria": "Must match Grandpa in garden foliage setting."
    },
    {
        "id": "C1-05",
        "cluster": "Face Tagging",
        "query": "Baby Emma first birthday party",
        "expected_photo_ids": ["p_emma_birthday_2022"],
        "disallowed_photo_ids": [],
        "criteria": "Must match Emma with cake/balloons birthday context."
    },
    {
        "id": "C1-06",
        "cluster": "Face Tagging",
        "query": "Dad cooking in the kitchen Christmas 2019",
        "expected_photo_ids": ["p_dad_cooking_xmas_2019"],
        "disallowed_photo_ids": [],
        "criteria": "Must match Dad cooking strictly around Christmas 2019."
    },

    # Cluster 2: Date Range Constraints
    {
        "id": "C2-01",
        "cluster": "Date Range",
        "query": "Summer 2018 road trip",
        "expected_photo_ids": ["p_roadtrip_2018"],
        "disallowed_photo_ids": [],
        "criteria": "Must bound between June 1 and Aug 31, 2018; road trip visual scene."
    },
    {
        "id": "C2-02",
        "cluster": "Date Range",
        "query": "Halloween photos from 2020",
        "expected_photo_ids": ["p_halloween_2020"],
        "disallowed_photo_ids": [],
        "criteria": "Must bound strictly to Oct 31, 2020."
    },
    {
        "id": "C2-03",
        "cluster": "Date Range",
        "query": "June 2022 wedding",
        "expected_photo_ids": ["p_wedding_2022"],
        "disallowed_photo_ids": [],
        "criteria": "Must bound strictly to June 1 - June 30, 2022 with wedding context."
    },
    {
        "id": "C2-04",
        "cluster": "Date Range",
        "query": "New Year's Eve 2019",
        "expected_photo_ids": ["p_nye_2019"],
        "disallowed_photo_ids": [],
        "criteria": "Must capture overnight transition Dec 31, 2019 to Jan 1, 2020."
    },
    {
        "id": "C2-05",
        "cluster": "Date Range",
        "query": "Receipts from last month",
        "expected_photo_ids": ["p_receipt_aug_2026"],
        "disallowed_photo_ids": [],
        "criteria": "Must resolve relative month to August 2026 and match receipt/document."
    },
    {
        "id": "C2-06",
        "cluster": "Date Range",
        "query": "Spring break 2017",
        "expected_photo_ids": ["p_springbreak_2017"],
        "disallowed_photo_ids": [],
        "criteria": "Must bound to March-April 2017 spring vacation."
    },

    # Cluster 3: Pet Recognition & Breeds
    {
        "id": "C3-01",
        "cluster": "Pet Recognition",
        "query": "Our dog in the snow last winter",
        "expected_photo_ids": ["p_dog_snow_winter_2026"],
        "disallowed_photo_ids": [],
        "criteria": "Must match user's dog in snow environment during winter 2025/2026."
    },
    {
        "id": "C3-02",
        "cluster": "Pet Recognition",
        "query": "Charlie sleeping on the couch",
        "expected_photo_ids": ["p_charlie_couch_2024"],
        "disallowed_photo_ids": [],
        "criteria": "Must match pet Charlie sleeping on sofa/couch."
    },
    {
        "id": "C3-03",
        "cluster": "Pet Recognition",
        "query": "Golden retriever playing fetch at the park",
        "expected_photo_ids": ["p_golden_park_fetch"],
        "disallowed_photo_ids": [],
        "criteria": "Must match golden retriever playing fetch in park."
    },
    {
        "id": "C3-04",
        "cluster": "Pet Recognition",
        "query": "Black cat by the window",
        "expected_photo_ids": ["p_black_cat_window"],
        "disallowed_photo_ids": ["p_neg_black_dog_window"],
        "criteria": "Must match feline Luna by window; must reject black dog sitting by window."
    },
    {
        "id": "C3-05",
        "cluster": "Pet Recognition",
        "query": "Max wearing a birthday hat in 2022",
        "expected_photo_ids": ["p_max_bday_2022"],
        "disallowed_photo_ids": [],
        "criteria": "Must match pet Max in party hat in year 2022."
    },
    {
        "id": "C3-06",
        "cluster": "Pet Recognition",
        "query": "Puppy photos from 2019",
        "expected_photo_ids": ["p_puppy_2019"],
        "disallowed_photo_ids": [],
        "criteria": "Must match puppy photos in 2019."
    },

    # Cluster 4: Location Search & Geo Bounding
    {
        "id": "C4-01",
        "cluster": "Location Search",
        "query": "Eiffel Tower trip in October 2019",
        "expected_photo_ids": ["p_eiffel_oct_2019"],
        "disallowed_photo_ids": ["p_neg_paris_2023"],
        "criteria": "Must match Eiffel Tower / Paris in Oct 2019; must reject 2023 Paris photos."
    },
    {
        "id": "C4-02",
        "cluster": "Location Search",
        "query": "Mom and Dad in Rome",
        "expected_photo_ids": ["p_parents_rome_2021"],
        "disallowed_photo_ids": [],
        "criteria": "Must match Mom and Dad co-present within Rome spatial boundary."
    },
    {
        "id": "C4-03",
        "cluster": "Location Search",
        "query": "Sunset at Venice Beach 2021",
        "expected_photo_ids": ["p_venice_sunset_2021"],
        "disallowed_photo_ids": [],
        "criteria": "Must match Venice Beach coordinates and sunset in 2021."
    },
    {
        "id": "C4-04",
        "cluster": "Location Search",
        "query": "Food photos in Tokyo",
        "expected_photo_ids": ["p_tokyo_food_2023"],
        "disallowed_photo_ids": [],
        "criteria": "Must match ramen/dining photos in Tokyo GPS bounds."
    },
    {
        "id": "C4-05",
        "cluster": "Location Search",
        "query": "Camping in Yosemite last summer",
        "expected_photo_ids": ["p_yosemite_camp_2025"],
        "disallowed_photo_ids": [],
        "criteria": "Must match Yosemite GPS bounds with camping/tent visual context."
    },

    # Cluster 5: Highly Complex 4-Way & 5-Way Compound Queries
    {
        "id": "C5-01",
        "cluster": "Compound Constraints",
        "query": "Mom with Charlie at the beach in Maui in Summer 2018",
        "expected_photo_ids": ["p_mom_charlie_maui_2018"],
        "disallowed_photo_ids": ["p_neg_beach_2023_stranger", "p_mom_beach_2018"],
        "criteria": "5-way joint match: Mom + Charlie + Maui + Summer 2018 + beach."
    },
    {
        "id": "C5-02",
        "cluster": "Compound Constraints",
        "query": "David and our dog hiking in Colorado Fall 2022",
        "expected_photo_ids": ["p_david_dog_colorado_2022"],
        "disallowed_photo_ids": [],
        "criteria": "4-way joint match: David + dog + Colorado + Fall 2022."
    },
]


async def run_benchmark(db: aiosqlite.Connection) -> Dict[str, Any]:
    """Runs all 25 benchmark queries and collects precision, recall, and pass rates."""
    orchestrator = HybridSearchOrchestrator()
    results = []
    cluster_stats = {}

    for item in BENCHMARK_TEST_SUITE:
        cluster = item["cluster"]
        if cluster not in cluster_stats:
            cluster_stats[cluster] = {"total": 0, "passed": 0}
        cluster_stats[cluster]["total"] += 1

        search_res = await orchestrator.search(db, item["query"])
        retrieved_ids = [r.photo_id for r in search_res.results]

        # Check expected hits
        expected_hit = any(eid in retrieved_ids for eid in item["expected_photo_ids"])

        # Check negative controls (must NOT be in retrieved top results)
        neg_pass = True
        for disallowed in item["disallowed_photo_ids"]:
            if disallowed in retrieved_ids:
                neg_pass = False
                break

        passed = expected_hit and neg_pass
        if passed:
            cluster_stats[cluster]["passed"] += 1

        results.append({
            "test_id": item["id"],
            "cluster": item["cluster"],
            "query": item["query"],
            "passed": passed,
            "execution_tier": search_res.execution_tier,
            "total_found": search_res.total_results,
            "retrieved_ids": retrieved_ids[:3],
            "expected_ids": item["expected_photo_ids"],
            "latency_ms": search_res.latency_ms,
            "criteria": item["criteria"],
            "parsed_constraints": {
                "people": [p.canonical_name for p in search_res.parsed.people],
                "pets": [p.raw_mention for p in search_res.parsed.pets],
                "temporal": search_res.parsed.temporal.raw_mention if search_res.parsed.temporal else None,
                "spatial": search_res.parsed.spatial.raw_mention if search_res.parsed.spatial else None,
                "visual": search_res.parsed.visual_residual.clean_prompt
            }
        })

    total_tests = len(BENCHMARK_TEST_SUITE)
    total_passed = sum(1 for r in results if r["passed"])
    avg_latency = sum(r["latency_ms"] for r in results) / total_tests if total_tests > 0 else 0.0

    return {
        "summary": {
            "total_queries": total_tests,
            "passed": total_passed,
            "failed": total_tests - total_passed,
            "pass_rate_pct": round((total_passed / total_tests) * 100, 1),
            "avg_latency_ms": round(avg_latency, 2),
            "status": "PASS" if total_passed == total_tests else "FAIL"
        },
        "cluster_breakdown": cluster_stats,
        "details": results
    }
