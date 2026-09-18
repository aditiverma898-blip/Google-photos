import os
import json
import logging
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
logger = logging.getLogger(__name__)

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

CORE_QUESTIONS = [
    {
        "question_id": 1,
        "question_text": "What kinds of old photos do users struggle to retrieve?"
    },
    {
        "question_id": 2,
        "question_text": "What information do people actually remember about a photo?"
    },
    {
        "question_id": 3,
        "question_text": "What information have they forgotten?"
    },
    {
        "question_id": 4,
        "question_text": "How do users formulate searches when their memory is incomplete?"
    },
    {
        "question_id": 5,
        "question_text": "Which retrieval failure cluster causes the highest user churn/frustration?"
    }
]

SYNTHESIS_SCHEMA = {
    "type": "ARRAY",
    "items": {
        "type": "OBJECT",
        "properties": {
            "question_id": {
                "type": "INTEGER",
                "description": "ID of the question being answered."
            },
            "question_text": {
                "type": "STRING",
                "description": "The exact question text."
            },
            "answer_text": {
                "type": "STRING",
                "description": "Detailed, specific, and actionable answer citing cluster data."
            },
            "evidence": {
                "type": "OBJECT",
                "properties": {
                    "cited_clusters": {
                        "type": "ARRAY",
                        "items": {"type": "INTEGER"},
                        "description": "List of cluster IDs cited in the answer."
                    },
                    "verbatim_quotes": {
                        "type": "ARRAY",
                        "items": {"type": "STRING"},
                        "description": "2 to 3 verbatim natural-language user complaint comments from real users. Absolutely NO metadata tags like 'Remembered:' or 'Forgotten:'."
                    }
                },
                "required": ["cited_clusters", "verbatim_quotes"]
            }
        },
        "required": ["question_id", "question_text", "answer_text", "evidence"]
    }
}

SYSTEM_PROMPT = """
You are a principal product research analyst for Google Photos.
Analyze the clustered dataset of real, verified user retrieval failures (is_retrieval_relevant = true) below and provide evidence-backed, rigorous strategic answers to each of the 5 core strategic questions.

CRITICAL RULES FOR METRIC CITATIONS:
1. Exact Cluster Metrics in EVERY Answer:
   In your answer_text for each question, explicitly cite the relevant clusters using their exact Cluster ID, label, verified sample size (n), and severity score matching the live dataset:
   - Cluster 0: "Missing Photos and Albums", n=1,053 verified complaints, severity 9.0/10
   - Cluster 1: "Background Object Recall", n=269 verified complaints, severity 7.5/10
   - Cluster 2: "Relative Time and Space Search", n=63 verified complaints, severity 8.2/10
   - Cluster 3: "Aesthetic and Weather Context", n=33 verified complaints, severity 6.5/10
   (Cluster 5: "Action and Event-Based Recall", n=0 verified complaints, severity 8.5/10 and Cluster 4: "Abstract Concept and Meme Retrieval", n=0 verified complaints, severity 6.0/10 if relevant)

2. ABSOLUTELY NO STALE DATA:
   DO NOT cite numbers from old pilot data (such as n=26, n=34, n=63, n=7, or severity scores like 4.9/10, 5.0/10, 6.1/10). All cited figures MUST strictly match the live numbers above.

3. Verbatim User Complaint Comments (MANDATORY):
   In your 'evidence.verbatim_quotes' array, you MUST provide 2 to 3 real, natural-language complaint quotes directly from user comments (the text in User Complaint: "...").
   STRICT PROHIBITION: NEVER output metadata or analytical labels (such as 'Remembered: [...]', 'Forgotten: [...]', or 'Strategy: [...]') as verbatim quotes. Every single quote MUST be a genuine, human user comment expressing their real-world experience or frustration.

4. Deep Strategic Analysis:
   In 'answer_text', provide comprehensive, actionable answers explaining the root failure modes, user psychological signals, and concrete product recommendations for Google Photos search.
"""

def build_context_prompt(clusters: list[dict]) -> str:
    """Formats cluster metadata and verified quotes into a text blob for Gemini context."""
    context = "### Google Photos Verified Retrieval Failure Clusters Dataset ###\n\n"
    
    for c in clusters:
        cid = c['cluster_id']
        label = c['label']
        desc = c['description']
        n = c.get('verified_n', c.get('record_count', 0))
        sev = c.get('severity_display') or f"{c['severity_score'] * 10:.1f}/10"
        tfp = c.get('top_failure_points', [])
        
        context += f"Cluster ID: {cid}\n"
        context += f"Label: {label}\n"
        context += f"Description: {desc}\n"
        context += f"Verified Sample Size (n): {n} complaints\n"
        context += f"Severity Score: {sev}\n"
        context += f"Top Failure Points: {', '.join(tfp) if isinstance(tfp, list) else tfp}\n"
        
        quotes = c.get('representative_quotes', [])
        if quotes:
            context += "Representative Real User Complaint Comments:\n"
            for q in quotes:
                if isinstance(q, dict):
                    text = q.get("quote") or q.get("text") or ""
                    rem = q.get("remembered") or q.get("remembered_attributes") or ""
                    forg = q.get("forgotten") or q.get("forgotten_attributes") or ""
                    strat = q.get("strategy") or q.get("search_strategy") or ""
                    fail = q.get("failure_point") or ""
                    context += f"- User Complaint: \"{text}\"\n"
                    context += f"  [Analytical context: remembered={rem}, forgotten={forg}, strategy={strat}, failure={fail}]\n"
                else:
                    context += f"- User Complaint: \"{q}\"\n"
        context += "-" * 50 + "\n\n"
        
    context += "### Core Questions to Answer ###\n"
    for q in CORE_QUESTIONS:
        context += f"Q{q['question_id']}: {q['question_text']}\n"
        
    return context

def generate_synthesis(clusters: list[dict]) -> list[dict]:
    """
    Calls Gemini to generate synthesized answers for all core questions based on cluster data.
    Returns a list of parsed Q&A dictionaries matching the schema.
    """
    global client
    if not client:
        load_dotenv()
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        
    if not clusters:
        logger.warning("No clusters provided for synthesis.")
        return []
        
    prompt = build_context_prompt(clusters)
    logger.info("Sending synthesis context to Gemini...")
    
    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=SYNTHESIS_SCHEMA,
                system_instruction=SYSTEM_PROMPT,
                temperature=0.2
            )
        )
        
        parsed_responses = json.loads(response.text)
        logger.info(f"Successfully generated {len(parsed_responses)} synthesized answers.")
        return parsed_responses
        
    except Exception as e:
        logger.error(f"Error during synthesis generation: {e}")
        return []

