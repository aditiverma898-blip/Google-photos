import os
import sys
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure we can import from backend
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db.connection import get_pool
from api.routes import router

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up FastAPI Backend...")
    try:
        app.state.pool = await get_pool()
        logger.info("Connected to SQLite database.")
        try:
            from db.init_db import run_migrations
            from search.seed_data import seed_discovery_database
            await run_migrations(app.state.pool)
            await seed_discovery_database(app.state.pool)
        except Exception as me:
            logger.warning(f"Auto-migration or seeding error: {me}")
    except Exception as e:
        app.state.pool = None
        logger.warning(f"Could not connect to SQLite. Running in mock mode. Error: {e}")
    yield
    # Shutdown
    logger.info("Shutting down FastAPI Backend...")
    if hasattr(app.state, 'pool') and app.state.pool:
        await app.state.pool.close()
        logger.info("Database connection closed.")

app = FastAPI(
    title="Google Photos Discovery Engine API",
    description="API for accessing Google Photos vague retrieval frustration clusters and semantic search.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration - allow all origins including Vercel and localhost
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_origin_regex=r".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(router)

@app.get("/")
async def root():
    return {"message": "Welcome to the Google Photos Discovery Engine API. Check /docs for documentation."}
