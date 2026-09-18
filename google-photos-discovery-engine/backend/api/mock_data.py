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
        "answer_text": "Users struggle to retrieve several specific categories of historical and legacy photos. Foremost among these are large sets of archival or long-stored photos that become untethered or scattered after major cloud syncs, device migrations, or storage clean-up routines. Users also report profound difficulty in retrieving historical photos when searching for specific background objects (such as a specific model of vehicle or equipment) where the primary subject dominates the visual index, as captured in Cluster 1: \"Background Object Recall\", n=269 verified complaints, severity 7.5/10. Furthermore, users struggle to find photos tied to relative timelines or cross-device timelines, such as trying to access legacy images spanning back years (e.g., 2008 archives) or unindexed legacy shared albums, as seen in Cluster 2: \"Relative Time and Space Search\", n=63 verified complaints, severity 8.2/10. Finally, users experience systemic loss and retrieval blocks regarding entire historical libraries (spanning 10+ years) following platform migrations, domain expirations, or account changes, as highlighted in Cluster 0: \"Missing Photos and Albums\", n=1,053 verified complaints, severity 9.0/10.",
        "evidence": {
            "cited_clusters": [
                0,
                1,
                2
            ],
            "verbatim_quotes": [
                "Lost 10+ years of photos yesterday. Need urgent help to get them back",
                "I'd like to access photos from years earlier, 2008 to be exact, and that will definitely take forever to load",
                "Sorry if this has been asked a hundred times but how can I better navigate or troubleshoot the image search? I ask for \"yellow truck\" and it finds 2 out of the 10 different days I had taken pictures of yellow trucks."
            ]
        }
    },
    {
        "question_id": 2,
        "question_text": "What information do people actually remember about a photo?",
        "answer_text": "When attempting to retrieve lost or buried memories, users retain very specific fragments of episodic and semantic memory. Based on the dataset, users frequently remember high-level contextual anchors such as approximate timeframes (e.g., specific years like 2008 or seasonal brackets), album names, and broad scene keywords (such as locations like Japan or specific subjects like pets and people), as demonstrated in Cluster 0: \"Missing Photos and Albums\", n=1,053 verified complaints, severity 9.0/10 and Cluster 1: \"Background Object Recall\", n=269 verified complaints, severity 7.5/10. Additionally, users recall recent download dates, source applications (such as WhatsApp or camera folders), and prominent background objects or distinct attributes (e.g., \"banana yellow\" trucks or specific animals) rather than exact file metadata, as noted in Cluster 2: \"Relative Time and Space Search\", n=63 verified complaints, severity 8.2/10. Users also maintain strong spatial-structural memory of past user interfaces and layout habits, remembering where specific menus or tabs used to live prior to updates, as seen in Cluster 3: \"Aesthetic and Weather Context\", n=33 verified complaints, severity 6.5/10.",
        "evidence": {
            "cited_clusters": [
                0,
                1,
                2,
                3
            ],
            "verbatim_quotes": [
                "Remembered: [\"album name\", \"approximate timeframe\"]",
                "Remembered: [\"person or pet name\", \"scene keywords\", \"location\"]",
                "Remembered: [\"recent download date\", \"source app (WhatsApp/Camera)\"]",
                "Remembered: [\"old tab navigation layout\"]"
            ]
        }
    },
    {
        "question_id": 3,
        "question_text": "What information have they forgotten?",
        "answer_text": "Users consistently fail to recall technical metadata and exact system states necessary for modern retrieval pipelines. Across multiple failure modes, users completely forget exact capture dates, original device filenames, and precise EXIF timestamps, relying instead on relative mental timelines (Cluster 2: \"Relative Time and Space Search\", n=63 verified complaints, severity 8.2/10). Furthermore, users lack awareness of critical background sync states, cloud-to-device linkage behaviors, and storage permissions, frequently leading to accidental deletions or permanent loss when assuming un-synced isolation, as documented in Cluster 0: \"Missing Photos and Albums\", n=1,053 verified complaints, severity 9.0/10. Users also forget the exact primary subjects of photos when focusing entirely on a salient background element or localized object, rendering natural language queries ineffective against primary-subject biased indexes (Cluster 1: \"Background Object Recall\", n=269 verified complaints, severity 7.5/10). Finally, users lose track of newly migrated UI paths, menu structures, and updated app navigation frameworks following major software releases (Cluster 3: \"Aesthetic and Weather Context\", n=33 verified complaints, severity 6.5/10).",
        "evidence": {
            "cited_clusters": [
                0,
                1,
                2,
                3
            ],
            "verbatim_quotes": [
                "Forgotten: [\"sync status\", \"exact device folder\"]",
                "Forgotten: [\"original EXIF capture date\"]",
                "Forgotten: [\"exact date of photo\", \"original filename\"]",
                "Forgotten: [\"newly moved menu locations\"]"
            ]
        }
    },
    {
        "question_id": 4,
        "question_text": "How do users formulate searches when their memory is incomplete?",
        "answer_text": "When faced with incomplete memories, users employ heuristic-driven search strategies. Users heavily rely on coarse date filters, manual scrolling timelines, and broad keyword attempts when semantic engines fail, attempting to bracket the missing timeframe manually (Cluster 0: \"Missing Photos and Albums\", n=1,053 verified complaints, severity 9.0/10 and Cluster 2: \"Relative Time and Space Search\", n=63 verified complaints, severity 8.2/10). When keyword search yields overly broad or irrelevant AI-driven results, users attempt boolean-style or modifier-heavy query phrasing (e.g., combining explicit positive and negative modifiers like specifying specific entities while excluding others), as observed in Cluster 1: \"Background Object Recall\", n=269 verified complaints, severity 7.5/10. Additionally, when modern AI-driven search models fail to surface intuitive results, users resort to manual album browsing, visual scanning through unstructured grids, or even downgrading to legacy application versions to bypass opaque search abstractions, as highlighted in Cluster 3: \"Aesthetic and Weather Context\", n=33 verified complaints, severity 6.5/10.",
        "evidence": {
            "cited_clusters": [
                0,
                1,
                2,
                3
            ],
            "verbatim_quotes": [
                "Strategy: date_filter",
                "Strategy: scrolling_timeline",
                "Search example in Google Fotos where your fotos are: Japan +Hans -Julia",
                "Strategy: album_browsing"
            ]
        }
    },
    {
        "question_id": 5,
        "question_text": "Which retrieval failure cluster causes the highest user churn/frustration?",
        "answer_text": "The retrieval and storage failure cluster that undeniably causes the highest user churn, panic, and extreme frustration is Cluster 0: \"Missing Photos and Albums\", carrying a massive volume of n=1,053 verified complaints and the highest severity score in the dataset at 9.0/10. Unlike aesthetic or background object recall issues where the failure is simply not finding an image, Cluster 0 represents catastrophic data loss events, permanent deletion anxieties, opaque cloud synchronization failures, and account migration lockouts (such as orphaned school domains or botched device cleanups). Users report severe psychological distress (including panic attacks and irreversible loss of decades of irreplaceable family memories) and active platform abandonment, such as executing full Google Takeouts to migrate to competing ecosystems like iCloud or Dropbox. To mitigate this existential churn risk, Google Photos must introduce fail-safe sync confirmations, transparent trash-recovery semantics decoupled from local device galleries, and human-in-the-loop recovery safeguards for cloud storage cleanups.",
        "evidence": {
            "cited_clusters": [
                0
            ],
            "verbatim_quotes": [
                "Lost 10+ years of photos yesterday. Need urgent help to get them back",
                "It took so long to discover where my photos went that I had an anxiety attack.",
                "10,000+ photos missing after Takeout to iCloud. What happened? Like many on this sub, I'm trying to de-Google my life for many reasons."
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
