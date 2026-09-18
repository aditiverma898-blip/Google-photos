"""
Seed data generator for Photos Discovery Engine.
Inserts realistic ground-truth photos, face tags, pet tags, and spatial/temporal metadata
to support the 25 compound benchmark queries and negative controls.
"""

import json
import logging
import aiosqlite
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

PEOPLE_SEEDS = [
    ("usr_mom", "default_user", "Mom", json.dumps(["mom", "mother", "mummy", "mama"])),
    ("usr_dad", "default_user", "Dad", json.dumps(["dad", "father", "daddy", "papa"])),
    ("usr_sarah", "default_user", "Sarah", json.dumps(["sarah"])),
    ("usr_david", "default_user", "David", json.dumps(["david", "dave"])),
    ("usr_emma", "default_user", "Emma", json.dumps(["emma", "baby emma"])),
    ("usr_grandpa", "default_user", "Grandpa", json.dumps(["grandpa", "grandfather", "granddad"])),
    ("usr_me", "default_user", "Me", json.dumps(["me", "myself", "i"])),
]

PET_SEEDS = [
    ("pet_charlie", "default_user", "Charlie", json.dumps(["charlie", "doggo"]), "dog", "golden_retriever", "golden"),
    ("pet_max", "default_user", "Max", json.dumps(["max"]), "dog", "mixed", "brown"),
    ("pet_luna", "default_user", "Luna", json.dumps(["luna"]), "cat", "domestic_shorthair", "black"),
]

# (photo_id, title, url, captured_at_utc, lat, lon, country, state, city, landmark, visual_tags, ocr_text)
PHOTO_SEEDS = [
    # C1-01: Mom at the beach in 2018
    ("p_mom_beach_2018", "Mom at Maui Beach", "https://images.unsplash.com/photo-beach-mom.jpg",
     "2018-07-15 14:30:00", 20.798, -156.331, "USA", "Hawaii", "Maui", "Wailea Beach",
     json.dumps(["beach", "sand", "ocean", "sunny", "waves"]), ""),

    # C1-02: David graduation party May 2021
    ("p_david_grad_2021", "David College Graduation Party", "https://images.unsplash.com/photo-david-grad.jpg",
     "2021-05-22 17:00:00", 47.606, -122.332, "USA", "Washington", "Seattle", "",
     json.dumps(["graduation", "party", "cap", "gown", "diploma", "celebration"]), "Congratulations David Class of 2021"),

    # C1-03: Me and Sarah skiing last winter
    ("p_sarah_me_ski_2026", "Skiing at Mount Baker", "https://images.unsplash.com/photo-skiing.jpg",
     "2026-01-18 11:15:00", 48.776, -121.814, "USA", "Washington", "Mount Baker", "",
     json.dumps(["skiing", "snow", "mountain", "winter", "slopes", "goggles"]), ""),

    # C1-04: Grandpa in the garden
    ("p_grandpa_garden_2023", "Grandpa with Roses", "https://images.unsplash.com/photo-grandpa-garden.jpg",
     "2023-04-10 10:00:00", 37.774, -122.419, "USA", "California", "San Francisco", "",
     json.dumps(["garden", "plants", "flowers", "roses", "greenery"]), ""),

    # C1-05: Baby Emma first birthday party
    ("p_emma_birthday_2022", "Baby Emma First Birthday", "https://images.unsplash.com/photo-emma-bday.jpg",
     "2022-09-05 15:00:00", 37.774, -122.419, "USA", "California", "San Francisco", "",
     json.dumps(["first", "birthday", "cake", "balloons", "party", "candles"]), "Emma is 1!"),

    # C1-06: Dad cooking in kitchen Christmas 2019
    ("p_dad_cooking_xmas_2019", "Dad Holiday Roast", "https://images.unsplash.com/photo-dad-cooking.jpg",
     "2019-12-25 18:30:00", 47.606, -122.332, "USA", "Washington", "Seattle", "",
     json.dumps(["cooking", "kitchen", "stove", "roast", "holiday", "dinner"]), ""),

    # C2-01: Summer 2018 road trip
    ("p_roadtrip_2018", "Highway 101 Road Trip", "https://images.unsplash.com/photo-roadtrip.jpg",
     "2018-07-08 13:00:00", 36.361, -121.856, "USA", "California", "Big Sur", "",
     json.dumps(["road", "trip", "car", "highway", "scenic", "coast", "driving"]), ""),

    # C2-02: Halloween photos from 2020
    ("p_halloween_2020", "Halloween Jack-o'-Lanterns", "https://images.unsplash.com/photo-halloween.jpg",
     "2020-10-31 20:00:00", 47.606, -122.332, "USA", "Washington", "Seattle", "",
     json.dumps(["halloween", "costume", "party", "pumpkins", "jack-o-lantern"]), "Spooky Night"),

    # C2-03: June 2022 wedding
    ("p_wedding_2022", "Outdoor Garden Wedding", "https://images.unsplash.com/photo-wedding.jpg",
     "2022-06-18 16:30:00", 37.774, -122.419, "USA", "California", "San Francisco", "",
     json.dumps(["wedding", "bride", "groom", "celebration", "flowers", "arch"]), ""),

    # C2-04: New Year's Eve 2019
    ("p_nye_2019", "New Year's Eve Countdown", "https://images.unsplash.com/photo-nye.jpg",
     "2019-12-31 23:45:00", 47.606, -122.332, "USA", "Washington", "Seattle", "Space Needle",
     json.dumps(["new", "years", "eve", "party", "fireworks", "champagne", "midnight"]), "Happy 2020"),

    # C2-05: Receipts from last month
    ("p_receipt_aug_2026", "Hardware Store Receipt", "https://images.unsplash.com/photo-receipt.jpg",
     "2026-08-15 11:20:00", 47.606, -122.332, "USA", "Washington", "Seattle", "",
     json.dumps(["receipt", "invoice", "document", "store", "paper"]), "Total: $42.50 Hardware Depot"),

    # C2-06: Spring break 2017
    ("p_springbreak_2017", "Spring Break Beach Day", "https://images.unsplash.com/photo-springbreak.jpg",
     "2017-03-24 14:00:00", 26.122, -80.137, "USA", "Florida", "Fort Lauderdale", "",
     json.dumps(["vacation", "travel", "party", "beach", "spring", "break", "sun"]), ""),

    # C3-01: Our dog in the snow last winter
    ("p_dog_snow_winter_2026", "Charlie Playing in Deep Snow", "https://images.unsplash.com/photo-dog-snow.jpg",
     "2026-01-20 10:30:00", 48.776, -121.814, "USA", "Washington", "Mount Baker", "",
     json.dumps(["snow", "winter", "playing", "trees", "white"]), ""),

    # C3-02: Charlie sleeping on the couch
    ("p_charlie_couch_2024", "Charlie Afternoon Nap", "https://images.unsplash.com/photo-dog-couch.jpg",
     "2024-03-12 15:00:00", 47.606, -122.332, "USA", "Washington", "Seattle", "",
     json.dumps(["sleeping", "couch", "sofa", "living", "room", "nap", "cozy"]), ""),

    # C3-03: Golden retriever playing fetch at the park
    ("p_golden_park_fetch", "Golden Retriever Fetching Ball", "https://images.unsplash.com/photo-golden-fetch.jpg",
     "2023-06-10 11:00:00", 47.606, -122.332, "USA", "Washington", "Seattle", "Green Lake Park",
     json.dumps(["playing", "fetch", "ball", "park", "grass", "running", "sunny"]), ""),

    # C3-04: Black cat by the window
    ("p_black_cat_window", "Luna Looking Out Window", "https://images.unsplash.com/photo-black-cat.jpg",
     "2024-05-04 14:00:00", 47.606, -122.332, "USA", "Washington", "Seattle", "",
     json.dumps(["window", "daylight", "indoor", "sill", "curtain", "sunlight"]), ""),

    # C3-05: Max wearing a birthday hat in 2022
    ("p_max_bday_2022", "Max Birthday Celebration", "https://images.unsplash.com/photo-max-bday.jpg",
     "2022-11-15 16:00:00", 47.606, -122.332, "USA", "Washington", "Seattle", "",
     json.dumps(["birthday", "party", "hat", "dog", "festive"]), ""),

    # C3-06: Puppy photos from 2019
    ("p_puppy_2019", "Little Charlie as a Puppy", "https://images.unsplash.com/photo-puppy.jpg",
     "2019-03-30 12:00:00", 47.606, -122.332, "USA", "Washington", "Seattle", "",
     json.dumps(["puppy", "cute", "grass", "small", "young", "playful"]), ""),

    # C4-01: Eiffel Tower trip in October 2019
    ("p_eiffel_oct_2019", "Eiffel Tower Autumn Afternoon", "https://images.unsplash.com/photo-eiffel.jpg",
     "2019-10-14 15:30:00", 48.8584, 2.2945, "France", "Île-de-France", "Paris", "Eiffel Tower",
     json.dumps(["eiffel", "tower", "monument", "autumn", "trees", "architecture"]), ""),

    # C4-02: Mom and Dad in Rome
    ("p_parents_rome_2021", "Mom and Dad at the Colosseum", "https://images.unsplash.com/photo-rome.jpg",
     "2021-09-18 16:00:00", 41.8902, 12.4922, "Italy", "Lazio", "Rome", "Colosseum",
     json.dumps(["rome", "italy", "ruins", "monument", "ancient", "vacation"]), ""),

    # C4-03: Sunset at Venice Beach 2021
    ("p_venice_sunset_2021", "Sunset over Venice Boardwalk", "https://images.unsplash.com/photo-venice-sunset.jpg",
     "2021-08-12 19:45:00", 33.985, -118.472, "USA", "California", "Los Angeles", "Venice Beach",
     json.dumps(["sunset", "ocean", "boardwalk", "orange", "sky", "palms"]), ""),

    # C4-04: Food photos in Tokyo
    ("p_tokyo_food_2023", "Ramen Dinner in Shinjuku", "https://images.unsplash.com/photo-tokyo-ramen.jpg",
     "2023-04-08 20:00:00", 35.6938, 139.7034, "Japan", "Kanto", "Tokyo", "Shinjuku",
     json.dumps(["food", "meal", "ramen", "noodles", "sushi", "dish", "bowl", "restaurant"]), "Ichiran Ramen"),

    # C4-05: Camping in Yosemite last summer
    ("p_yosemite_camp_2025", "Campfire under Half Dome", "https://images.unsplash.com/photo-yosemite.jpg",
     "2025-07-20 21:00:00", 37.7456, -119.5936, "USA", "California", "Yosemite", "Yosemite National Park",
     json.dumps(["camping", "tent", "forest", "campfire", "mountains", "stars"]), ""),

    # C5-01: Mom with Charlie at the beach in Maui in Summer 2018
    ("p_mom_charlie_maui_2018", "Mom and Charlie at Kaanapali Beach", "https://images.unsplash.com/photo-mom-charlie-maui.jpg",
     "2018-07-19 15:30:00", 20.923, -156.696, "USA", "Hawaii", "Maui", "Kaanapali Beach",
     json.dumps(["beach", "ocean", "waves", "sand", "sunny", "tropical"]), ""),

    # C5-02: David and our dog hiking in Colorado Fall 2022
    ("p_david_dog_colorado_2022", "David and Charlie Hiking in the Rockies", "https://images.unsplash.com/photo-david-hiking.jpg",
     "2022-10-10 13:00:00", 39.550, -105.782, "USA", "Colorado", "Breckenridge", "Rocky Mountains",
     json.dumps(["hiking", "trail", "mountain", "fall", "aspen", "golden", "trees"]), ""),

    # Negative Control Photos (to prove precision & non-hallucination)
    ("p_neg_beach_2023_stranger", "Unknown person at Miami Beach 2023", "https://images.unsplash.com/photo-stranger.jpg",
     "2023-07-10 12:00:00", 25.761, -80.191, "USA", "Florida", "Miami", "South Beach",
     json.dumps(["beach", "sand", "ocean"]), ""),

    ("p_neg_black_dog_window", "Black Dog sitting by window", "https://images.unsplash.com/photo-black-dog.jpg",
     "2024-05-04 14:00:00", 47.606, -122.332, "USA", "Washington", "Seattle", "",
     json.dumps(["window", "daylight", "indoor"]), ""),

    ("p_neg_paris_2023", "Eiffel Tower in 2023", "https://images.unsplash.com/photo-paris-2023.jpg",
     "2023-04-15 15:00:00", 48.8584, 2.2945, "France", "Île-de-France", "Paris", "Eiffel Tower",
     json.dumps(["eiffel", "tower", "monument"]), ""),
]

# (photo_id, person_id, confidence)
PHOTO_FACE_SEEDS = [
    ("p_mom_beach_2018", "usr_mom", 0.98),
    ("p_david_grad_2021", "usr_david", 0.99),
    ("p_sarah_me_ski_2026", "usr_sarah", 0.97),
    ("p_sarah_me_ski_2026", "usr_me", 0.99),
    ("p_grandpa_garden_2023", "usr_grandpa", 0.96),
    ("p_emma_birthday_2022", "usr_emma", 0.98),
    ("p_dad_cooking_xmas_2019", "usr_dad", 0.99),
    ("p_parents_rome_2021", "usr_mom", 0.97),
    ("p_parents_rome_2021", "usr_dad", 0.98),
    ("p_mom_charlie_maui_2018", "usr_mom", 0.99),
    ("p_david_dog_colorado_2022", "usr_david", 0.98),
]

# (photo_id, pet_id, species, breed, confidence)
PHOTO_PET_SEEDS = [
    ("p_dog_snow_winter_2026", "pet_charlie", "dog", "golden_retriever", 0.98),
    ("p_charlie_couch_2024", "pet_charlie", "dog", "golden_retriever", 0.99),
    ("p_golden_park_fetch", "pet_charlie", "dog", "golden_retriever", 0.96),
    ("p_black_cat_window", "pet_luna", "cat", "domestic_shorthair", 0.97),
    ("p_max_bday_2022", "pet_max", "dog", "mixed", 0.98),
    ("p_puppy_2019", "pet_charlie", "dog", "golden_retriever", 0.92),
    ("p_mom_charlie_maui_2018", "pet_charlie", "dog", "golden_retriever", 0.99),
    ("p_david_dog_colorado_2022", "pet_charlie", "dog", "golden_retriever", 0.97),
    ("p_neg_black_dog_window", None, "dog", "labrador", 0.95),
]


async def seed_discovery_database(db: aiosqlite.Connection):
    """Inserts or updates seed records in database."""
    # 1. Seed People
    await db.executemany("""
        INSERT OR REPLACE INTO people (person_id, user_id, canonical_name, aliases)
        VALUES (?, ?, ?, ?)
    """, PEOPLE_SEEDS)

    # 2. Seed Pets
    await db.executemany("""
        INSERT OR REPLACE INTO pets (pet_id, user_id, name, aliases, species, breed, color)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, PET_SEEDS)

    # 3. Seed Photos
    await db.executemany("""
        INSERT OR REPLACE INTO photos (
            photo_id, title, url, captured_at_utc, latitude, longitude,
            country, state, city, landmark, visual_tags, ocr_text
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, PHOTO_SEEDS)

    # 4. Seed Photo Faces
    await db.execute("DELETE FROM photo_faces")
    await db.executemany("""
        INSERT INTO photo_faces (photo_id, person_id, confidence)
        VALUES (?, ?, ?)
    """, PHOTO_FACE_SEEDS)

    # 5. Seed Photo Pets
    await db.execute("DELETE FROM photo_pets")
    await db.executemany("""
        INSERT INTO photo_pets (photo_id, pet_id, species, breed, confidence)
        VALUES (?, ?, ?, ?, ?)
    """, PHOTO_PET_SEEDS)

    await db.commit()
    logger.info("Discovery engine photo catalog seeded successfully.")
