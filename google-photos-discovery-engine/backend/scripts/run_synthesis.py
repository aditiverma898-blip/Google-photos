import os
import sys
import json
import asyncio
import logging

# Ensure we can import from backend
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db.connection import get_pool
from synthesis.synthesizer import generate_synthesis

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

async def run_synthesis_pipeline():
    """Fetches cluster data, runs AI synthesis, and stores answers."""
    pool = await get_pool()
    
    try:
        # 1. Fetch Cluster Metadata
        logger.info("Fetching cluster metadata from database...")
        async with pool.execute("""
            SELECT cluster_id, label, description, record_count, 
                   severity_score, top_failure_points, representative_quotes
            FROM clusters
        """) as cursor:
            rows = await cursor.fetchall()
            
        if not rows:
            logger.error("No clusters found in the database. Cannot run synthesis.")
            return
            
        clusters = []
        for r in rows:
            c_dict = dict(r)
            c_dict['top_failure_points'] = json.loads(c_dict['top_failure_points'])
            c_dict['representative_quotes'] = json.loads(c_dict['representative_quotes'])
            clusters.append(c_dict)
            
        logger.info(f"Loaded {len(clusters)} clusters for synthesis context.")
        
        # 2. Run Synthesis Generation
        logger.info("Starting AI Synthesis Engine. This may take a moment...")
        loop = asyncio.get_event_loop()
        answers = await loop.run_in_executor(None, lambda: generate_synthesis(clusters))
        
        if not answers:
            logger.error("Synthesis generation failed or returned empty.")
            return
            
        # 3. Store Results
        logger.info("Clearing old synthesis answers...")
        await pool.execute("DELETE FROM synthesis_answers")
        
        insert_query = """
        INSERT INTO synthesis_answers (question_id, question_text, answer_text, evidence)
        VALUES (?, ?, ?, ?)
        """
        
        for ans in answers:
            await pool.execute(
                insert_query,
                (
                    ans['question_id'],
                    ans['question_text'],
                    ans['answer_text'],
                    json.dumps(ans['evidence'])
                )
            )
        await pool.commit()
        logger.info(f"Successfully stored {len(answers)} synthesized answers in the database.")
            
        # Print a quick summary to terminal
        print("\n=== AI Synthesis Summary ===")
        for ans in answers:
            print(f"\nQ{ans['question_id']}: {ans['question_text']}")
            print(f"Answer: {ans['answer_text'][:100]}...")
        print("============================\n")

    finally:
        await pool.close()

if __name__ == "__main__":
    asyncio.run(run_synthesis_pipeline())
