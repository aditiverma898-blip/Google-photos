import os
import json
import logging
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

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
                        "description": "Verbatim user quotes supporting the answer."
                    }
                },
                "required": ["cited_clusters", "verbatim_quotes"]
            }
        },
        "required": ["question_id", "question_text", "answer_text", "evidence"]
    }
}

SYSTEM_PROMPT = """
You are a product research analyst for Google Photos.
Analyze the clustered dataset of user retrieval failures below and provide evidence-backed answers to each of the 5 core strategic questions.

CRITICAL RULES:
- Ground your answers strictly in the provided cluster metadata and representative quotes.
- In your answer_text, cite the cluster ID, sample size (n), and severity score.
- Ensure 'verbatim_quotes' are EXACT matches to the provided text.
- Do not hallucinate external context.
"""

def build_context_prompt(clusters: list[dict]) -> str:
    """Formats cluster metadata into a text blob for Gemini context."""
    context = "### Google Photos Retrieval Failure Clusters Dataset ###\n\n"
    
    for c in clusters:
        context += f"Cluster ID: {c['cluster_id']}\n"
        context += f"Label: {c['label']}\n"
        context += f"Description: {c['description']}\n"
        context += f"Record Count (n): {c['record_count']}\n"
        context += f"Severity Score: {c['severity_score'] * 10:.1f}/10\n"
        context += f"Top Failure Points: {', '.join(c['top_failure_points'])}\n"
        context += "Representative Quotes:\n"
        for q in c['representative_quotes']:
            context += f"- \"{q}\"\n"
        context += "-" * 40 + "\n\n"
        
    context += "### Core Questions to Answer ###\n"
    for q in CORE_QUESTIONS:
        context += f"Q{q['question_id']}: {q['question_text']}\n"
        
    return context

def generate_synthesis(clusters: list[dict]) -> list[dict]:
    """
    Calls Gemini to generate synthesized answers for all core questions based on cluster data.
    Returns a list of parsed Q&A dictionaries matching the schema.
    """
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
