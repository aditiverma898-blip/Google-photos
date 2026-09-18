"""
Query Understanding Layer for Photos Discovery Engine.
Parses natural language queries into structured multi-dimensional constraints:
- People / Face identities
- Pets / Breeds / Animal species
- Temporal bounds (start_utc, end_utc)
- Spatial boundaries (bounding box, city, landmark)
- Residual visual prompt (stripped of resolved metadata tokens)
"""

import re
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class PersonConstraint(BaseModel):
    raw_mention: str
    resolved_person_id: Optional[str] = None
    canonical_name: Optional[str] = None
    confidence: float = 1.0

class PetConstraint(BaseModel):
    raw_mention: str
    resolved_pet_id: Optional[str] = None
    species: Optional[str] = None  # 'dog', 'cat', etc.
    breed: Optional[str] = None    # 'golden_retriever', etc.
    color: Optional[str] = None
    confidence: float = 1.0

class TemporalConstraint(BaseModel):
    raw_mention: str
    type: str = "range"  # 'range', 'month', 'year', 'holiday', 'relative'
    start_utc: str       # ISO-8601 string
    end_utc: str         # ISO-8601 string
    granularity: str = "custom"  # 'year', 'season', 'month', 'day'

class SpatialConstraint(BaseModel):
    raw_mention: str
    resolved_place: str
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    landmark: Optional[str] = None
    min_lat: Optional[float] = None
    max_lat: Optional[float] = None
    min_lon: Optional[float] = None
    max_lon: Optional[float] = None

class VisualResidual(BaseModel):
    clean_prompt: str
    detected_tags: List[str] = Field(default_factory=list)

class ParsedQuery(BaseModel):
    raw_query: str
    people: List[PersonConstraint] = Field(default_factory=list)
    pets: List[PetConstraint] = Field(default_factory=list)
    temporal: Optional[TemporalConstraint] = None
    spatial: Optional[SpatialConstraint] = None
    visual_residual: VisualResidual
    execution_strategy: str = "STRICT_FILTER_THEN_RANK"


# -------------------------------------------------------------
# Knowledge Registries & Gazetteers (Default Seed Catalogs)
# -------------------------------------------------------------

KNOWN_PEOPLE_REGISTRY = {
    "usr_mom": {"canonical": "Mom", "aliases": ["mom", "mother", "mummy", "mama"]},
    "usr_dad": {"canonical": "Dad", "aliases": ["dad", "father", "daddy", "papa"]},
    "usr_sarah": {"canonical": "Sarah", "aliases": ["sarah"]},
    "usr_david": {"canonical": "David", "aliases": ["david", "dave"]},
    "usr_emma": {"canonical": "Emma", "aliases": ["emma", "baby emma"]},
    "usr_grandpa": {"canonical": "Grandpa", "aliases": ["grandpa", "grandfather", "granddad"]},
    "usr_me": {"canonical": "Me", "aliases": ["me", "myself", "i"]},
}

KNOWN_PETS_REGISTRY = {
    "pet_charlie": {
        "name": "Charlie",
        "aliases": ["charlie"],
        "species": "dog",
        "breed": "golden_retriever",
        "color": "golden"
    },
    "pet_max": {
        "name": "Max",
        "aliases": ["max"],
        "species": "dog",
        "breed": "mixed",
        "color": "brown"
    },
    "pet_luna": {
        "name": "Luna",
        "aliases": ["luna"],
        "species": "cat",
        "breed": "domestic_shorthair",
        "color": "black"
    }
}

KNOWN_SPATIAL_GAZETTEER = {
    "maui": {
        "resolved_place": "Maui, Hawaii, USA",
        "city": "Maui",
        "state": "Hawaii",
        "country": "USA",
        "min_lat": 20.55, "max_lat": 21.05,
        "min_lon": -156.70, "max_lon": -155.95
    },
    "paris": {
        "resolved_place": "Paris, Île-de-France, France",
        "city": "Paris",
        "country": "France",
        "min_lat": 48.80, "max_lat": 48.92,
        "min_lon": 2.22, "max_lon": 2.47
    },
    "rome": {
        "resolved_place": "Rome, Lazio, Italy",
        "city": "Rome",
        "country": "Italy",
        "min_lat": 41.75, "max_lat": 42.00,
        "min_lon": 12.35, "max_lon": 12.65
    },
    "tokyo": {
        "resolved_place": "Tokyo, Japan",
        "city": "Tokyo",
        "country": "Japan",
        "min_lat": 35.50, "max_lat": 35.85,
        "min_lon": 139.50, "max_lon": 139.95
    },
    "yosemite": {
        "resolved_place": "Yosemite National Park, California, USA",
        "landmark": "Yosemite National Park",
        "state": "California",
        "country": "USA",
        "min_lat": 37.50, "max_lat": 38.00,
        "min_lon": -119.80, "max_lon": -119.20
    },
    "venice beach": {
        "resolved_place": "Venice Beach, Los Angeles, California, USA",
        "landmark": "Venice Beach",
        "city": "Los Angeles",
        "state": "California",
        "country": "USA",
        "min_lat": 33.97, "max_lat": 34.01,
        "min_lon": -118.49, "max_lon": -118.45
    },
    "colorado": {
        "resolved_place": "Colorado, USA",
        "state": "Colorado",
        "country": "USA",
        "min_lat": 37.0, "max_lat": 41.0,
        "min_lon": -109.05, "max_lon": -102.04
    },
    "eiffel tower": {
        "resolved_place": "Eiffel Tower, Paris, France",
        "landmark": "Eiffel Tower",
        "city": "Paris",
        "country": "France",
        "min_lat": 48.855, "max_lat": 48.862,
        "min_lon": 2.290, "max_lon": 2.300
    },
    "seattle": {
        "resolved_place": "Seattle, Washington, USA",
        "city": "Seattle",
        "state": "Washington",
        "country": "USA",
        "min_lat": 47.45, "max_lat": 47.75,
        "min_lon": -122.45, "max_lon": -122.20
    },
    "san francisco": {
        "resolved_place": "San Francisco, California, USA",
        "city": "San Francisco",
        "state": "California",
        "country": "USA",
        "min_lat": 37.70, "max_lat": 37.83,
        "min_lon": -122.52, "max_lon": -122.35
    }
}


# -------------------------------------------------------------
# Parser Implementation
# -------------------------------------------------------------

class QueryUnderstandingEngine:
    """
    Parses natural language queries into strictly typed multi-dimensional constraints.
    Supports local rule & entity resolution with gazetteer linking.
    """

    def __init__(
        self,
        people_registry: Optional[Dict[str, Any]] = None,
        pets_registry: Optional[Dict[str, Any]] = None,
        spatial_gazetteer: Optional[Dict[str, Any]] = None,
    ):
        self.people_registry = people_registry or KNOWN_PEOPLE_REGISTRY
        self.pets_registry = pets_registry or KNOWN_PETS_REGISTRY
        self.spatial_gazetteer = spatial_gazetteer or KNOWN_SPATIAL_GAZETTEER

    def parse(self, raw_query: str) -> ParsedQuery:
        """Parse raw query into structured constraints and visual residual."""
        normalized = raw_query.strip()
        working_text = f" {normalized} "
        consumed_spans = []

        # 1. Parse People
        people_constraints = []
        # Sort people aliases by length descending to match "baby emma" before "emma"
        all_people = []
        for pid, meta in self.people_registry.items():
            for alias in meta["aliases"]:
                all_people.append((alias, pid, meta["canonical"]))
        all_people.sort(key=lambda x: len(x[0]), reverse=True)

        for alias, pid, canonical in all_people:
            pattern = rf"\b{re.escape(alias)}\b"
            match = re.search(pattern, working_text, re.IGNORECASE)
            if match:
                people_constraints.append(PersonConstraint(
                    raw_mention=match.group(0).strip(),
                    resolved_person_id=pid,
                    canonical_name=canonical,
                    confidence=0.98
                ))
                consumed_spans.append((match.start(), match.end()))
                # Blank out matched span in working text
                working_text = working_text[:match.start()] + (" " * (match.end() - match.start())) + working_text[match.end():]

        # 2. Parse Pets & Animal Entities
        pet_constraints = []
        # Specific registered pet check
        all_pets = []
        for pid, meta in self.pets_registry.items():
            for alias in meta["aliases"]:
                all_pets.append((alias, pid, meta))
        all_pets.sort(key=lambda x: len(x[0]), reverse=True)

        for alias, pid, meta in all_pets:
            pattern = rf"\b{re.escape(alias)}\b"
            match = re.search(pattern, working_text, re.IGNORECASE)
            if match:
                pet_constraints.append(PetConstraint(
                    raw_mention=match.group(0).strip(),
                    resolved_pet_id=pid,
                    species=meta["species"],
                    breed=meta.get("breed"),
                    color=meta.get("color"),
                    confidence=0.96
                ))
                consumed_spans.append((match.start(), match.end()))
                working_text = working_text[:match.start()] + (" " * (match.end() - match.start())) + working_text[match.end():]

        # Generic pet / breed checks (e.g., "our dog", "golden retriever", "black cat", "puppy")
        generic_pet_patterns = [
            (r"\bgolden retriever\b", {"species": "dog", "breed": "golden_retriever"}),
            (r"\bblack cat\b", {"species": "cat", "color": "black"}),
            (r"\bpuppy\b", {"species": "dog", "breed": ""}),
            (r"\bour dog\b", {"species": "dog", "breed": ""}),
            (r"\bour cat\b", {"species": "cat", "breed": ""}),
            (r"\bdog\b", {"species": "dog", "breed": ""}),
            (r"\bcat\b", {"species": "cat", "breed": ""}),
        ]
        for pat, info in generic_pet_patterns:
            match = re.search(pat, working_text, re.IGNORECASE)
            if match and not pet_constraints:
                pet_constraints.append(PetConstraint(
                    raw_mention=match.group(0).strip(),
                    species=info["species"],
                    breed=info.get("breed") or None,
                    color=info.get("color") or None,
                    confidence=0.88
                ))
                working_text = working_text[:match.start()] + (" " * (match.end() - match.start())) + working_text[match.end():]
                break

        # 3. Parse Temporal Constraints
        temporal_constraint = self._parse_temporal(working_text)
        if temporal_constraint:
            # Blank out temporal mention in working text
            pattern = rf"\b{re.escape(temporal_constraint.raw_mention)}\b"
            match = re.search(pattern, working_text, re.IGNORECASE)
            if match:
                working_text = working_text[:match.start()] + (" " * (match.end() - match.start())) + working_text[match.end():]

        # 4. Parse Spatial Constraints
        spatial_constraint = None
        # Check gazetteer sorted by place name length descending
        sorted_places = sorted(self.spatial_gazetteer.items(), key=lambda x: len(x[0]), reverse=True)
        for place_key, geo_info in sorted_places:
            pattern = rf"\b{re.escape(place_key)}\b"
            match = re.search(pattern, working_text, re.IGNORECASE)
            if match:
                spatial_constraint = SpatialConstraint(
                    raw_mention=match.group(0).strip(),
                    resolved_place=geo_info["resolved_place"],
                    city=geo_info.get("city"),
                    state=geo_info.get("state"),
                    country=geo_info.get("country"),
                    landmark=geo_info.get("landmark"),
                    min_lat=geo_info.get("min_lat"),
                    max_lat=geo_info.get("max_lat"),
                    min_lon=geo_info.get("min_lon"),
                    max_lon=geo_info.get("max_lon"),
                )
                working_text = working_text[:match.start()] + (" " * (match.end() - match.start())) + working_text[match.end():]
                break

        # 5. Extract Visual Residual
        # Remove common stop words and prepositions
        stopwords = {
            "in", "at", "on", "from", "with", "the", "a", "an", "and", "of", "by",
            "to", "for", "photos", "photo", "pictures", "picture", "our", "all"
        }
        raw_words = re.findall(r"[A-Za-z0-9_-]+", working_text)
        residual_words = [w for w in raw_words if w.lower() not in stopwords]
        clean_visual_prompt = " ".join(residual_words).strip()

        # Generate visual tags for residual
        detected_tags = [w.lower() for w in residual_words if len(w) > 2]

        return ParsedQuery(
            raw_query=normalized,
            people=people_constraints,
            pets=pet_constraints,
            temporal=temporal_constraint,
            spatial=spatial_constraint,
            visual_residual=VisualResidual(
                clean_prompt=clean_visual_prompt,
                detected_tags=detected_tags
            ),
            execution_strategy="STRICT_FILTER_THEN_RANK"
        )

    def _parse_temporal(self, text: str) -> Optional[TemporalConstraint]:
        """Parses temporal expressions into UTC datetime bounds."""
        t = text.lower()

        # Christmas (e.g., "Christmas 2019")
        m_xmas = re.search(r"\bchristmas\s*(?:photos\s*from\s*)?(20\d\d)\b", t)
        if m_xmas:
            yr = m_xmas.group(1)
            return TemporalConstraint(
                raw_mention=f"Christmas {yr}",
                type="holiday",
                start_utc=f"{yr}-12-24T00:00:00Z",
                end_utc=f"{yr}-12-26T23:59:59Z",
                granularity="day"
            )

        # Halloween (e.g., "Halloween photos from 2020", "Halloween 2020")
        m_halloween = re.search(r"\bhalloween(?:\s+photos\s+from)?\s*(20\d\d)\b", t)
        if m_halloween:
            yr = m_halloween.group(1)
            return TemporalConstraint(
                raw_mention=f"Halloween {yr}",
                type="holiday",
                start_utc=f"{yr}-10-31T00:00:00Z",
                end_utc=f"{yr}-10-31T23:59:59Z",
                granularity="day"
            )

        # New Year's Eve (e.g., "New Year's Eve 2019", "New Years Eve 2019")
        m_nye = re.search(r"\bnew\s*years?(?:\'s)?\s*eve\s*(20\d\d)\b", t)
        if m_nye:
            yr = int(m_nye.group(1))
            return TemporalConstraint(
                raw_mention=f"New Year's Eve {yr}",
                type="holiday",
                start_utc=f"{yr}-12-31T18:00:00Z",
                end_utc=f"{yr+1}-01-01T06:00:00Z",
                granularity="day"
            )

        # Seasons with Year: "Summer 2018", "Spring break 2017", "Fall 2022", "Winter 2019"
        m_season = re.search(r"\b(summer|spring(?:\s+break)?|fall|autumn|winter)\s*(20\d\d)\b", t)
        if m_season:
            season = m_season.group(1).lower()
            yr = m_season.group(2)
            if "summer" in season:
                return TemporalConstraint(
                    raw_mention=f"Summer {yr}",
                    type="range",
                    start_utc=f"{yr}-06-01T00:00:00Z",
                    end_utc=f"{yr}-08-31T23:59:59Z",
                    granularity="season"
                )
            elif "spring" in season:
                return TemporalConstraint(
                    raw_mention=f"{season.title()} {yr}",
                    type="range",
                    start_utc=f"{yr}-03-01T00:00:00Z",
                    end_utc=f"{yr}-05-31T23:59:59Z",
                    granularity="season"
                )
            elif "fall" in season or "autumn" in season:
                return TemporalConstraint(
                    raw_mention=f"Fall {yr}",
                    type="range",
                    start_utc=f"{yr}-09-01T00:00:00Z",
                    end_utc=f"{yr}-11-30T23:59:59Z",
                    granularity="season"
                )
            elif "winter" in season:
                return TemporalConstraint(
                    raw_mention=f"Winter {yr}",
                    type="range",
                    start_utc=f"{int(yr)-1}-12-01T00:00:00Z",
                    end_utc=f"{yr}-02-28T23:59:59Z",
                    granularity="season"
                )

        # Relative Seasons: "last winter", "last summer"
        if "last winter" in t:
            # Anchored to 2025/2026 reference window
            return TemporalConstraint(
                raw_mention="last winter",
                type="relative",
                start_utc="2025-12-01T00:00:00Z",
                end_utc="2026-02-28T23:59:59Z",
                granularity="season"
            )
        if "last summer" in t:
            return TemporalConstraint(
                raw_mention="last summer",
                type="relative",
                start_utc="2025-06-01T00:00:00Z",
                end_utc="2025-08-31T23:59:59Z",
                granularity="season"
            )

        # Month + Year: "June 2022", "May 2021", "October 2019"
        months = {
            "january": 1, "february": 2, "march": 3, "april": 4,
            "may": 5, "june": 6, "july": 7, "august": 8,
            "september": 9, "october": 10, "november": 11, "december": 12
        }
        month_pattern = r"\b(" + "|".join(months.keys()) + r")\s*(20\d\d)\b"
        m_month = re.search(month_pattern, t)
        if m_month:
            m_name = m_month.group(1).lower()
            yr = int(m_month.group(2))
            m_num = months[m_name]
            # End of month days
            days_in_month = [31, 29 if yr % 4 == 0 else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m_num - 1]
            return TemporalConstraint(
                raw_mention=f"{m_name.title()} {yr}",
                type="month",
                start_utc=f"{yr:04d}-{m_num:02d}-01T00:00:00Z",
                end_utc=f"{yr:04d}-{m_num:02d}-{days_in_month:02d}T23:59:59Z",
                granularity="month"
            )

        # Relative month: "last month"
        if "last month" in t:
            return TemporalConstraint(
                raw_mention="last month",
                type="relative",
                start_utc="2026-08-01T00:00:00Z",
                end_utc="2026-08-31T23:59:59Z",
                granularity="month"
            )

        # Standalone Year: "in 2018", "from 2019", "2021"
        m_year = re.search(r"\b(?:in|from|during)?\s*(20\d\d)\b", t)
        if m_year:
            yr = m_year.group(1)
            return TemporalConstraint(
                raw_mention=yr,
                type="year",
                start_utc=f"{yr}-01-01T00:00:00Z",
                end_utc=f"{yr}-12-31T23:59:59Z",
                granularity="year"
            )

        return None
