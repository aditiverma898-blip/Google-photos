"""
Hybrid Search Engine & Query Orchestrator for Photos Discovery.
Coordinates Multi-Index Query Routing, Boolean Constraint Intersection,
Tiered Graceful Degradation, and Diagnostic Result Scoring.
"""

import json
import logging
import aiosqlite
from typing import List, Dict, Any, Optional, Set
from pydantic import BaseModel
from search.query_understanding import QueryUnderstandingEngine, ParsedQuery

logger = logging.getLogger(__name__)

class SearchResultItem(BaseModel):
    photo_id: str
    title: str
    url: str
    captured_at_utc: str
    latitude: Optional[float]
    longitude: Optional[float]
    city: Optional[str]
    state: Optional[str]
    country: Optional[str]
    landmark: Optional[str]
    visual_tags: List[str]
    matched_constraints: List[str]
    score: float
    explanation_badge: str

class SearchResponse(BaseModel):
    query: str
    parsed: ParsedQuery
    execution_tier: str  # TIER_1_EXACT_INTERSECTION, TIER_2_RELAXED_BOUNDS, TIER_3_PARTIAL_FALLBACK
    total_results: int
    results: List[SearchResultItem]
    latency_ms: float = 0.0


class HybridSearchOrchestrator:
    """
    Executes hybrid search across face, pet, temporal, spatial, and visual indices.
    """

    def __init__(self, parser: Optional[QueryUnderstandingEngine] = None):
        self.parser = parser or QueryUnderstandingEngine()

    async def search(
        self,
        db: aiosqlite.Connection,
        query_text: str,
        user_id: str = "default_user",
        min_results: int = 1
    ) -> SearchResponse:
        """
        Executes end-to-end parsed retrieval with graceful tiering.
        """
        import time
        t0 = time.perf_counter()

        parsed = self.parser.parse(query_text)

        # -------------------------------------------------------------
        # 1. Fetch Candidate Photos & Compute Constraint Matches
        # -------------------------------------------------------------
        async with db.execute("""
            SELECT photo_id, user_id, title, url, captured_at_utc,
                   latitude, longitude, country, state, city, landmark,
                   visual_tags, ocr_text
            FROM photos
            WHERE user_id = ?
        """, (user_id,)) as cursor:
            photo_rows = await cursor.fetchall()

        all_photos = [dict(r) for r in photo_rows]
        for p in all_photos:
            p["visual_tags"] = json.loads(p["visual_tags"])

        # Fetch face memberships
        async with db.execute("""
            SELECT photo_id, person_id, confidence
            FROM photo_faces
        """) as cursor:
            face_rows = await cursor.fetchall()
        photo_faces: Dict[str, Set[str]] = {}
        for r in face_rows:
            photo_faces.setdefault(r["photo_id"], set()).add(r["person_id"])

        # Fetch pet memberships
        async with db.execute("""
            SELECT photo_id, pet_id, species, breed, confidence
            FROM photo_pets
        """) as cursor:
            pet_rows = await cursor.fetchall()
        photo_pets: Dict[str, List[Dict[str, Any]]] = {}
        for r in pet_rows:
            photo_pets.setdefault(r["photo_id"], []).append(dict(r))

        # -------------------------------------------------------------
        # 2. Tier 1: Strict Intersection (All high-confidence constraints)
        # -------------------------------------------------------------
        tier1_items = self._evaluate_tier1(
            all_photos, photo_faces, photo_pets, parsed
        )

        if len(tier1_items) >= min_results:
            elapsed = (time.perf_counter() - t0) * 1000
            return SearchResponse(
                query=query_text,
                parsed=parsed,
                execution_tier="TIER_1_EXACT_INTERSECTION",
                total_results=len(tier1_items),
                results=sorted(tier1_items, key=lambda x: x.score, reverse=True),
                latency_ms=round(elapsed, 2)
            )

        # -------------------------------------------------------------
        # 3. Tier 2: Progressive Relaxation (Widen temporal/spatial)
        # -------------------------------------------------------------
        tier2_items = self._evaluate_tier2(
            all_photos, photo_faces, photo_pets, parsed
        )

        if len(tier2_items) >= min_results:
            elapsed = (time.perf_counter() - t0) * 1000
            return SearchResponse(
                query=query_text,
                parsed=parsed,
                execution_tier="TIER_2_RELAXED_BOUNDS",
                total_results=len(tier2_items),
                results=sorted(tier2_items, key=lambda x: x.score, reverse=True),
                latency_ms=round(elapsed, 2)
            )

        # -------------------------------------------------------------
        # 4. Tier 3: Partial Scored Fallback
        # -------------------------------------------------------------
        tier3_items = self._evaluate_tier3(
            all_photos, photo_faces, photo_pets, parsed
        )
        elapsed = (time.perf_counter() - t0) * 1000
        return SearchResponse(
            query=query_text,
            parsed=parsed,
            execution_tier="TIER_3_PARTIAL_FALLBACK",
            total_results=len(tier3_items),
            results=sorted(tier3_items, key=lambda x: x.score, reverse=True),
            latency_ms=round(elapsed, 2)
        )

    def _evaluate_tier1(
        self,
        photos: List[Dict[str, Any]],
        photo_faces: Dict[str, Set[str]],
        photo_pets: Dict[str, List[Dict[str, Any]]],
        parsed: ParsedQuery
    ) -> List[SearchResultItem]:
        """Strict boolean AND intersection of all active constraints."""
        matched = []

        for p in photos:
            pid = p["photo_id"]
            constraints_passed = []
            score = 1.0

            # 1. People check
            if parsed.people:
                person_ids_in_photo = photo_faces.get(pid, set())
                all_people_match = True
                for person in parsed.people:
                    if person.resolved_person_id not in person_ids_in_photo:
                        all_people_match = False
                        break
                    constraints_passed.append(f"person:{person.canonical_name}")
                if not all_people_match:
                    continue

            # 2. Pets check
            if parsed.pets:
                pets_in_photo = photo_pets.get(pid, [])
                pet_matched = False
                for pet_req in parsed.pets:
                    for instance in pets_in_photo:
                        if pet_req.resolved_pet_id and instance.get("pet_id") == pet_req.resolved_pet_id:
                            pet_matched = True
                            constraints_passed.append(f"pet:{instance.get('pet_id')}")
                            break
                        elif pet_req.species and instance.get("species") == pet_req.species:
                            if not pet_req.breed or instance.get("breed") == pet_req.breed:
                                pet_matched = True
                                constraints_passed.append(f"pet:{pet_req.species}")
                                break
                    if pet_matched:
                        break
                if not pet_matched:
                    continue

            # 3. Temporal check
            if parsed.temporal:
                # Format: '2018-07-15 14:30:00' -> compare as ISO/string or timestamp
                photo_time = p["captured_at_utc"].replace(" ", "T")
                if not (photo_time >= parsed.temporal.start_utc[:19] and photo_time <= parsed.temporal.end_utc[:19]):
                    continue
                constraints_passed.append(f"date:{parsed.temporal.raw_mention}")

            # 4. Spatial check
            if parsed.spatial:
                geo_ok = False
                # Check city / country / landmark
                if parsed.spatial.city and p.get("city") and parsed.spatial.city.lower() in p["city"].lower():
                    geo_ok = True
                elif parsed.spatial.country and p.get("country") and parsed.spatial.country.lower() in p["country"].lower():
                    geo_ok = True
                elif parsed.spatial.landmark and p.get("landmark") and parsed.spatial.landmark.lower() in p["landmark"].lower():
                    geo_ok = True
                # Check bounding box
                elif parsed.spatial.min_lat is not None and p.get("latitude") is not None:
                    lat, lon = p["latitude"], p["longitude"]
                    if (parsed.spatial.min_lat <= lat <= parsed.spatial.max_lat and
                        parsed.spatial.min_lon <= lon <= parsed.spatial.max_lon):
                        geo_ok = True

                if not geo_ok:
                    continue
                constraints_passed.append(f"geo:{parsed.spatial.raw_mention}")

            # 5. Visual Residual check
            if parsed.visual_residual.detected_tags:
                tag_overlap = set(parsed.visual_residual.detected_tags).intersection(set(p["visual_tags"]))
                title_words = set(p["title"].lower().split())
                title_overlap = set(parsed.visual_residual.detected_tags).intersection(title_words)
                ocr_words = set(p.get("ocr_text", "").lower().split())
                ocr_overlap = set(parsed.visual_residual.detected_tags).intersection(ocr_words)

                total_overlap = tag_overlap | title_overlap | ocr_overlap

                # If pure visual query with no people/date/geo, require overlap
                has_structured = bool(parsed.people or parsed.pets or parsed.temporal or parsed.spatial)
                if not has_structured and not total_overlap:
                    continue
                if total_overlap:
                    constraints_passed.append(f"visual:{','.join(list(total_overlap)[:2])}")
                    score += len(total_overlap) * 0.2

            matched.append(SearchResultItem(
                photo_id=p["photo_id"],
                title=p["title"],
                url=p["url"],
                captured_at_utc=p["captured_at_utc"],
                latitude=p.get("latitude"),
                longitude=p.get("longitude"),
                city=p.get("city"),
                state=p.get("state"),
                country=p.get("country"),
                landmark=p.get("landmark"),
                visual_tags=p["visual_tags"],
                matched_constraints=constraints_passed,
                score=round(score, 3),
                explanation_badge=f"Exact match ({' + '.join(constraints_passed) if constraints_passed else 'photo'})"
            ))

        return matched

    def _evaluate_tier2(
        self,
        photos: List[Dict[str, Any]],
        photo_faces: Dict[str, Set[str]],
        photo_pets: Dict[str, List[Dict[str, Any]]],
        parsed: ParsedQuery
    ) -> List[SearchResultItem]:
        """Tier 2: Relaxation (expands seasonal date range to full year, or relaxes location radius)."""
        relaxed_matched = []

        for p in photos:
            pid = p["photo_id"]
            constraints_passed = []
            score = 0.85

            # People still mandatory
            if parsed.people:
                person_ids_in_photo = photo_faces.get(pid, set())
                if not all(person.resolved_person_id in person_ids_in_photo for person in parsed.people):
                    continue
                constraints_passed.append(f"person:{parsed.people[0].canonical_name}")

            # Pets still mandatory
            if parsed.pets:
                pets_in_photo = photo_pets.get(pid, [])
                pet_matched = any(
                    (p_req.resolved_pet_id and inst.get("pet_id") == p_req.resolved_pet_id) or
                    (p_req.species and inst.get("species") == p_req.species)
                    for p_req in parsed.pets for inst in pets_in_photo
                )
                if not pet_matched:
                    continue
                constraints_passed.append(f"pet:{parsed.pets[0].raw_mention}")

            # Relaxed temporal: expand window by ± 6 months (year level)
            if parsed.temporal:
                photo_yr = p["captured_at_utc"][:4]
                req_yr = parsed.temporal.start_utc[:4]
                if photo_yr == req_yr:
                    constraints_passed.append(f"date_relaxed:{req_yr}")
                else:
                    continue

            # Relaxed spatial: match state or country
            if parsed.spatial:
                geo_ok = False
                if parsed.spatial.country and p.get("country") and parsed.spatial.country.lower() in p["country"].lower():
                    geo_ok = True
                elif parsed.spatial.state and p.get("state") and parsed.spatial.state.lower() in p["state"].lower():
                    geo_ok = True
                if geo_ok:
                    constraints_passed.append(f"geo_relaxed:{parsed.spatial.raw_mention}")
                else:
                    continue

            relaxed_matched.append(SearchResultItem(
                photo_id=p["photo_id"],
                title=p["title"],
                url=p["url"],
                captured_at_utc=p["captured_at_utc"],
                latitude=p.get("latitude"),
                longitude=p.get("longitude"),
                city=p.get("city"),
                state=p.get("state"),
                country=p.get("country"),
                landmark=p.get("landmark"),
                visual_tags=p["visual_tags"],
                matched_constraints=constraints_passed,
                score=round(score, 3),
                explanation_badge=f"Relaxed match ({' + '.join(constraints_passed)})"
            ))

        return relaxed_matched

    def _evaluate_tier3(
        self,
        photos: List[Dict[str, Any]],
        photo_faces: Dict[str, Set[str]],
        photo_pets: Dict[str, List[Dict[str, Any]]],
        parsed: ParsedQuery
    ) -> List[SearchResultItem]:
        """Tier 3: Weighted partial match with confidence scoring."""
        partial_matched = []

        for p in photos:
            pid = p["photo_id"]
            score = 0.0
            reasons = []

            # 1. Visual overlap
            tag_overlap = set(parsed.visual_residual.detected_tags).intersection(set(p["visual_tags"]))
            if tag_overlap:
                score += 0.40 * (len(tag_overlap) / max(len(parsed.visual_residual.detected_tags), 1))
                reasons.append(f"visual:{','.join(list(tag_overlap)[:2])}")

            # 2. Person match
            if parsed.people:
                person_ids_in_photo = photo_faces.get(pid, set())
                if any(person.resolved_person_id in person_ids_in_photo for person in parsed.people):
                    score += 0.35
                    reasons.append(f"person:{parsed.people[0].canonical_name}")

            # 3. Pet match
            if parsed.pets:
                pets_in_photo = photo_pets.get(pid, [])
                if any(p_req.species and inst.get("species") == p_req.species for p_req in parsed.pets for inst in pets_in_photo):
                    score += 0.30
                    reasons.append(f"pet:{parsed.pets[0].raw_mention}")

            # 4. Date match
            if parsed.temporal:
                photo_time = p["captured_at_utc"].replace(" ", "T")
                if photo_time >= parsed.temporal.start_utc[:19] and photo_time <= parsed.temporal.end_utc[:19]:
                    score += 0.20
                    reasons.append("date:matched")

            # 5. Geo match
            if parsed.spatial:
                if (parsed.spatial.city and p.get("city") and parsed.spatial.city.lower() in p["city"].lower()) or \
                   (parsed.spatial.country and p.get("country") and parsed.spatial.country.lower() in p["country"].lower()):
                    score += 0.15
                    reasons.append("geo:matched")

            if score >= 0.35:
                partial_matched.append(SearchResultItem(
                    photo_id=p["photo_id"],
                    title=p["title"],
                    url=p["url"],
                    captured_at_utc=p["captured_at_utc"],
                    latitude=p.get("latitude"),
                    longitude=p.get("longitude"),
                    city=p.get("city"),
                    state=p.get("state"),
                    country=p.get("country"),
                    landmark=p.get("landmark"),
                    visual_tags=p["visual_tags"],
                    matched_constraints=reasons,
                    score=round(score, 3),
                    explanation_badge=f"Partial match ({' + '.join(reasons)})"
                ))

        return partial_matched
