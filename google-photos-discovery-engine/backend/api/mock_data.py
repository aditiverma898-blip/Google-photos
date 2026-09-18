MOCK_CLUSTERS = [
    {
        "cluster_id": 1,
        "label": "Face Tagging Failures",
        "description": "Users cannot find specific people despite tagging them.",
        "severity_score": 8.5,
        "size": 450,
        "top_failure_points": ["Search by face returns no results", "Wrong person tagged"],
        "representative_quotes": ["I searched for my mom and it showed me my dog.", "Face grouping just stopped working entirely."]
    },
    {
        "cluster_id": 2,
        "label": "Date Range Issues",
        "description": "Searching for photos between specific dates fails.",
        "severity_score": 7.2,
        "size": 320,
        "top_failure_points": ["Cannot search 'Summer 2018'", "Month queries ignored"],
        "representative_quotes": ["When I type 'June 2019' it gives me photos from 2022.", "Why can't I search by year?"]
    },
    {
        "cluster_id": 3,
        "label": "Pet Recognition",
        "description": "Fails to distinguish between similar looking pets.",
        "severity_score": 6.8,
        "size": 210,
        "top_failure_points": ["Cats confused with dogs", "Cannot find specific pet"],
        "representative_quotes": ["It thinks my black cat is a black pillow.", "I have 3 golden retrievers and it thinks they are all the same dog."]
    },
    {
        "cluster_id": 4,
        "label": "Location Search",
        "description": "Searching by city or landmark returns incorrect results.",
        "severity_score": 5.5,
        "size": 150,
        "top_failure_points": ["City name ignored", "GPS coordinates missing"],
        "representative_quotes": ["I searched for 'Paris' and got pictures of my living room.", "Location search is completely broken."]
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
            "severity_score": 8.5,
            "distance": 0.2841
        },
        "similar_records": [
            {
                "id": 1,
                "cluster_id": 1,
                "raw_text": f"I tried searching for {query} but Google Photos returned completely unrelated photos or empty results.",
                "failure_point": "Subject recognition failed on vague query",
                "search_strategy": "Vague entity description",
                "distance": 0.2410,
                "is_confident": True
            },
            {
                "id": 2,
                "cluster_id": 1,
                "raw_text": f"Cannot find photos when searching for {query}.",
                "failure_point": "Multi-constraint entity indexing failure",
                "search_strategy": "Subject search",
                "distance": 0.3120,
                "is_confident": True
            }
        ]
    }
