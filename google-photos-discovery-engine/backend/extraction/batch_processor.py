import os
import json
import asyncio
import glob
import logging
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

BATCH_PROMPT_TEMPLATE = """You are an expert UX data analyst for Google Photos specializing in vague search and retrieval failure analysis.

You are given a list of raw user feedback and complaints. For each item:
1. Determine if it describes an attempt or frustration with finding, searching, locating, or retrieving photos/videos in Google Photos (set is_retrieval_attempt = true/false).
2. If true, extract:
   - photo_type: one of ["document", "screenshot", "old_vacation", "pet", "family_event", "selfie", "landmark", "food", "receipt", "other"]
   - remembered_attributes: list of strings (what the user recalled: person, year, color, object, location)
   - forgotten_attributes: list of strings (what the user couldn't remember: exact date, album, file name)
   - search_strategy: one of ["keyword_search", "scrolling_timeline", "album_browsing", "people_face_search", "location_search", "date_filter", "combined_filters", "google_lens", "other"]
   - failure_point: brief description of where search or retrieval failed
   - workaround: what the user did instead (manual scrolling, gave up, third party app, or empty string)
   - emotional_signal: one of ["frustrated", "angry", "disappointed", "sad", "resigned", "neutral"]
3. If false, set is_retrieval_attempt = false and use defaults.

Return a JSON array of objects with the exact schema, preserving the "id" field to match each input.

Inputs to analyze:
"""

async def extract_batch(records: list[dict], max_retries: int = 3) -> list[dict]:
    """Extracts structured JSON for a batch of 8-10 complaints in a single Gemini call."""
    input_items = []
    lookup = {}
    for idx, r in enumerate(records):
        item_id = str(idx)
        raw_text = r.get("raw_text", "").strip()
        input_items.append({"id": item_id, "text": raw_text})
        lookup[item_id] = r

    prompt = BATCH_PROMPT_TEMPLATE + json.dumps(input_items, ensure_ascii=False)

    for attempt in range(max_retries):
        try:
            response = await client.aio.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )
            parsed_list = json.loads(response.text)
            if not isinstance(parsed_list, list):
                parsed_list = [parsed_list]

            extracted_records = []
            for item in parsed_list:
                item_id = str(item.get("id", ""))
                orig = lookup.get(item_id)
                if not orig:
                    continue

                platform = orig.get("source_platform") or orig.get("source", "play_store")
                if platform in ("appstore", "google_play", "playstore"):
                    platform = "play_store"
                elif platform in ("helpforum", "support", "google_support"):
                    platform = "help_community"
                elif platform not in ("reddit", "play_store", "app_store", "help_community", "youtube", "social"):
                    platform = "play_store"

                url_id = orig.get("url_id") or orig.get("url") or str(hash(orig.get("raw_text", "")))
                
                item["source_platform"] = platform
                item["url_id"] = url_id
                item["raw_text"] = orig.get("raw_text", "")
                extracted_records.append(item)

            return extracted_records

        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                wait = 20.0 * (attempt + 1)
                logger.warning(f"[extraction] 429 quota pause, waiting {wait:.1f}s...")
                await asyncio.sleep(wait)
            elif "503" in err_str or "UNAVAILABLE" in err_str:
                await asyncio.sleep(4.0)
            else:
                logger.error(f"[extraction] Batch error: {e}")
                return []

    return []

async def process_raw_data(raw_data_dir: str, limit: int = None, existing_ids: set = None) -> list[dict]:
    """
    Reads .jsonl files in raw_data_dir, extracts structured data concurrently
    using batch-prompted Gemini 3.5 Flash Lite with rate-limiting.
    Samples evenly across all sources (youtube, reddit, appstore, helpforum).
    """
    seen_urls = set(existing_ids or [])
    sources = ["youtube", "reddit", "helpforum", "appstore"]
    records_by_source = {s: [] for s in sources}
    
    for s in sources:
        s_dir = os.path.join(raw_data_dir, s)
        files = glob.glob(os.path.join(s_dir, "**", "*.jsonl"), recursive=True)
        for filepath in files:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if line.strip():
                        rec = json.loads(line)
                        uid = rec.get("url_id") or rec.get("url")
                        if uid and uid not in seen_urls:
                            records_by_source[s].append(rec)
                            seen_urls.add(uid)

    # Round-robin interleave to guarantee source diversity
    raw_records = []
    max_len = max(len(records_by_source[s]) for s in sources) if any(records_by_source.values()) else 0
    for idx in range(max_len):
        for s in sources:
            if idx < len(records_by_source[s]):
                raw_records.append(records_by_source[s][idx])
                if limit and len(raw_records) >= limit:
                    break
        if limit and len(raw_records) >= limit:
            break
                    
    logger.info(f"Loaded {len(raw_records)} unprocessed raw records across sources for extraction.")
    if not raw_records:
        return []

    # Batch in groups of 8 items per prompt
    batch_size = 8
    record_batches = [raw_records[i:i + batch_size] for i in range(0, len(raw_records), batch_size)]
    
    all_extracted = []
    total_processed = 0

    for idx, batch in enumerate(record_batches):
        logger.info(f"[extraction] Processing batch {idx + 1}/{len(record_batches)} ({len(batch)} records)...")
        extracted = await extract_batch(batch)
        all_extracted.extend(extracted)
        total_processed += len(batch)
        
        # Pacing delay between batch calls to remain smoothly within RPM limit
        await asyncio.sleep(2.5)

    return all_extracted
