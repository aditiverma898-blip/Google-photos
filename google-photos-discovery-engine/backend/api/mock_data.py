MOCK_CLUSTERS = [
    {
        "cluster_id": 1,
        "label": "Background Object Recall",
        "description": "Users remember a prominent background object but forget the primary subject.",
        "severity_score": 0.75,
        "size": 500,
        "top_failure_points": ["Background objects not indexed", "Primary subject overshadows background"],
        "representative_quotes": [
            {"quote": "I know she was holding a blue coffee mug but searching 'blue mug' gives me nothing.", "source": "Reddit - r/googlephotos"},
            {"quote": "Trying to find the picture with the yellow taxi in the background.", "source": "Google Support Community"}
        ]
    },
    {
        "cluster_id": 2,
        "label": "Relative Time and Space Search",
        "description": "Users search using relative time (e.g., 'after my birthday') or relative locations.",
        "severity_score": 0.82,
        "size": 450,
        "top_failure_points": ["Relative temporal parsing fails", "No support for event-based offsets"],
        "representative_quotes": [
            {"quote": "I want the photos taken a few days after my birthday in Paris.", "source": "App Store"},
            {"quote": "Searching for 'weekend before Halloween' doesn't work.", "source": "Twitter/X"}
        ]
    },
    {
        "cluster_id": 3,
        "label": "Aesthetic and Weather Context",
        "description": "Users search by the mood, weather, or aesthetic of the photo.",
        "severity_score": 0.65,
        "size": 300,
        "top_failure_points": ["Lack of weather metadata indexing", "Emotion and mood are not extracted"],
        "representative_quotes": [
            {"quote": "I'm looking for a rainy day at a cafe, but it just shows me pictures of coffee.", "source": "Reddit - r/googlephotos"},
            {"quote": "Why can't I search for 'gloomy weather' or 'sad mood'?", "source": "Google Support Community"}
        ]
    },
    {
        "cluster_id": 4,
        "label": "Abstract Concept and Meme Retrieval",
        "description": "Users look for memes, screenshots, or abstract ideas rather than physical objects.",
        "severity_score": 0.60,
        "size": 250,
        "top_failure_points": ["OCR text not prioritized for abstract concepts", "Semantic understanding of memes is lacking"],
        "representative_quotes": [
            {"quote": "Trying to find a screenshot of a funny meme about cats, but searching 'cat meme' just shows actual cats.", "source": "App Store"},
            {"quote": "I need the screenshot with the quote about persistence.", "source": "Reddit - r/googlephotos"}
        ]
    },
    {
        "cluster_id": 5,
        "label": "Action and Event-Based Recall",
        "description": "Users remember what was happening in the media (actions/events) but lack text keywords.",
        "severity_score": 0.85,
        "size": 650,
        "top_failure_points": ["Search indexes static nouns over dynamic verbs", "Action and event context not extracted"],
        "representative_quotes": [
            {"quote": "I'm looking for the video where my dog was barking at the TV, but 'barking dog' shows nothing.", "source": "Reddit - r/googlephotos"},
            {"quote": "Can't find that picture of me blowing out candles, 'birthday' just shows cakes without me.", "source": "Play Store"}
        ]
    }
]

MOCK_SYNTHESIS = [
    {
        "question": "What is the most severe vague retrieval frustration?",
        "answer": "Face tagging failures cause the highest emotional distress, as users feel a loss of connection to their loved ones when searches fail.",
        "cited_clusters": [1]
    },
    {
        "question": "How are users attempting to work around these failures?",
        "answer": "Users resort to manually scrolling through thousands of photos by date, or creating manual albums for specific people and pets.",
        "cited_clusters": [1, 2, 3]
    },
    {
        "question": "What are the hidden patterns in how users formulate queries?",
        "answer": "Users naturally formulate queries using a combination of Time + Person + Object (e.g. 'Mom at the beach in 2018'), but the engine struggles to parse all three constraints simultaneously.",
        "cited_clusters": [1, 2, 4]
    }
]

def mock_search_response(query: str):
    return {
        "query": query,
        "is_confident_match": True,
        "threshold": 0.35,
        "nearest_cluster": {
            "cluster_id": 1,
            "label": "Subject & Media Retrieval Difficulties",
            "description": f"User feedback related to searching for subjects like '{query}'.",
            "severity_score": 0.85,
            "distance": 0.2841
        },
        "similar_records": [
            {
                "id": 1,
                "cluster_id": 1,
                "source": "Play Store",
                "source_platform": "play_store",
                "raw_text": f"I tried searching for {query} but Google Photos returned completely unrelated photos or empty results.",
                "failure_point": "Subject recognition failed on vague query",
                "search_strategy": "Vague entity description",
                "distance": 0.2410,
                "is_confident": True
            },
            {
                "id": 2,
                "cluster_id": 1,
                "source": "Reddit",
                "source_platform": "reddit",
                "raw_text": f"Cannot find photos when searching for {query}.",
                "failure_point": "Multi-constraint entity indexing failure",
                "search_strategy": "Subject search",
                "distance": 0.3120,
                "is_confident": True
            }
        ]
    }
