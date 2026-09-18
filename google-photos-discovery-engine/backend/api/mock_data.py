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
        "question_id": 1,
        "question_text": "What kinds of old photos do users struggle to retrieve?",
        "answer_text": "Users struggle significantly to retrieve older photos that involve complex contextual queries, specific background elements, or those affected by app updates and backup synchronization discrepancies. Specifically, in Cluster 0 ('Missing Photos and Albums', n=1,053 verified complaints, severity score 9.0/10), users report losing access to photos spanning over a decade after phone upgrades, storage cleanups, or app UI updates that scatter folders. Similarly, in Cluster 2 ('Relative Time and Space Search', n=63 verified complaints, severity score 8.2/10), users trying to locate older archives from years like 2008 face extreme friction because timeline scrolling requires massive data loading without efficient relative temporal parsing. Furthermore, users struggle to recall old images when search indices over-index primary subjects while completely ignoring secondary details, as seen in Cluster 1 ('Background Object Recall', n=269 verified complaints, severity score 7.5/10), where simple keyword queries fail to pull up historical photos containing specific objects or text.",
        "evidence": {
            "cited_clusters": [
                0,
                1,
                2
            ],
            "verbatim_quotes": [
                "Lost 10+ years of photos yesterday. Need urgent help to get them back Making this post in the hope that someone at Google or someone that knows someone there might see it and be able to help.",
                "shared photos taking too long to load - How to access them without having to load? My dad shares his phone photos with me through Google Photos, but when I want to access older photos, even if they're from three months ago or less, they have to be uploaded."
            ]
        }
    },
    {
        "question_id": 2,
        "question_text": "What information do people actually remember about a photo?",
        "answer_text": "When attempting to retrieve memories, users reliably remember high-level contextual anchors such as approximate timeframes (e.g., a specific year like 2008 or a life event), general subject categories, prominent background objects or specific keywords, and album names. In Cluster 0 ('Missing Photos and Albums', n=1,053 verified complaints, severity score 9.0/10), users consistently remember album titles and approximate timeframes when attempting to recreate or browse their collections. In Cluster 1 ('Background Object Recall', n=269 verified complaints, severity score 7.5/10), users vividly remember specific background elements, prominent items, or scene keywords (such as a 'yellow truck' or a 'blowtorch') even when they forget the primary subject. In Cluster 2 ('Relative Time and Space Search', n=63 verified complaints, severity score 8.2/10), users anchor their searches around relative milestones or source app origins such as WhatsApp or Camera folders.",
        "evidence": {
            "cited_clusters": [
                0,
                1,
                2
            ],
            "verbatim_quotes": [
                "I ask for \"yellow truck\" and it finds 2 out of the 10 different days I had taken pictures of yellow trucks. They're all banana yellow and the images contain a truck and nothing else.",
                "I want to create a photo album gift of all the pictures I have: Of \"Sue\", or By \"Sue\", and Taken in 2021."
            ]
        }
    },
    {
        "question_id": 3,
        "question_text": "What information have they forgotten?",
        "answer_text": "Users frequently forget exact technical metadata, precise dates, sync statuses, and original file attributes. As demonstrated in Cluster 0 ('Missing Photos and Albums', n=1,053 verified complaints, severity score 9.0/10), users routinely forget cloud sync states, whether deletion propagates across linked gallery apps, and exact device directory paths, leading to accidental catastrophic data loss. In Cluster 2 ('Relative Time and Space Search', n=63 verified complaints, severity score 8.2/10), users forget the original EXIF capture dates of downloaded or transferred media, relying instead on recent download timestamps. Additionally, in Cluster 1 ('Background Object Recall', n=269 verified complaints, severity score 7.5/10), users forget original filenames and exact calendar dates, expecting natural language or semantic search to bridge the gap when exact metadata is absent.",
        "evidence": {
            "cited_clusters": [
                0,
                1,
                2
            ],
            "verbatim_quotes": [
                "Now I'm panicking because I had no idea that deleting them from Google photos would delete them from there as well as I'd tested and was sure they weren't linked.",
                "It was not always true that they have your photos backed up on the cloud when it says so. I used to trust is app for saving and backing up my pictures to the cloud..."
            ]
        }
    },
    {
        "question_id": 4,
        "question_text": "How do users formulate searches when their memory is incomplete?",
        "answer_text": "When memory is incomplete, users rely on heuristic search strategies such as keyword approximations, date filters, manual scrolling through timelines, and attempting boolean-style or multi-term queries. In Cluster 1 ('Background Object Recall', n=269 verified complaints, severity score 7.5/10), users try substituting specific modifiers or descriptive nouns (e.g., searching for 'pickup truck' or 'rattlesnake' when broad terms fail), only to be frustrated by rigid AI indexing. In Cluster 0 ('Missing Photos and Albums', n=1,053 verified complaints, severity score 9.0/10), users attempt complex text queries combining date ranges and negative terms, or resort to manual album browsing when search algorithms return irrelevant semantic matches. In Cluster 2 ('Relative Time and Space Search', n=63 verified complaints, severity score 8.2/10), users fall back on tedious timeline scrolling or keyword guesses based on source apps when relative temporal queries are unsupported.",
        "evidence": {
            "cited_clusters": [
                0,
                1,
                2
            ],
            "verbatim_quotes": [
                "I'll try different phrasing like \" pickup truck\" and it'll actually add a few more trucks but also lose some of the yellow trucks it initially found.",
                "The only way I can ever find these photos is by digging through all 5,000+ photos that I have. Any other app especially the Airbnb app can never find the photos that I starred..."
            ]
        }
    },
    {
        "question_id": 5,
        "question_text": "Which retrieval failure cluster causes the highest user churn/frustration?",
        "answer_text": "The retrieval and management failure cluster that causes the absolute highest user churn, panic, and severe frustration is Cluster 0: 'Missing Photos and Albums' (n=1,053 verified complaints, severity score 9.0/10). With the largest verified complaint volume and the highest severity score in the dataset, this cluster captures catastrophic user pain points where individuals lose years of irreplaceable personal memories (such as family milestones and decade-old archives) due to opaque backup behaviors, unexpected cross-app deletion syncing, and disruptive UI updates. Unlike subtle search relevance issues, failures in Cluster 0 result in permanent loss of trust, account abandonment, and complete platform churn, as users feel actively betrayed by automated storage cleanup prompts that delete local files before confirming secure cloud redundancy.",
        "evidence": {
            "cited_clusters": [
                0,
                1,
                2,
                3
            ],
            "verbatim_quotes": [
                "Lost 10+ years of photos yesterday. Need urgent help to get them back Making this post in the hope that someone at Google or someone that knows someone there might see it and be able to help.",
                "I've lost over half of my pictures because of google photos. Ok, here's your update, no better, even worse. They move pictures, loose pictures, remove pictures from my gallery, WHICH IS WHERE I WANT THEM."
            ]
        }
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
