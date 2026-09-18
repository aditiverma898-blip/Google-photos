# Google Photos Discovery Engine

An end-to-end AI-powered insights engine designed to scrape, extract, cluster, and synthesize vague retrieval frustration points from users trying (and failing) to find their photos.

## Architecture

This project is divided into 5 core pipelines:
1. **Ingestion**: Scrapes raw user complaints from Reddit (via Apify).
2. **Extraction**: Uses Gemini 2.0 Flash to strictly parse raw text into structured JSON schemas (intent, search strategy, workaround).
3. **Clustering**: Generates embeddings using `text-embedding-004` and dynamically clusters them using UMAP + HDBSCAN.
4. **Synthesis**: Pipes massive context windows back into Gemini to generate strategic Q&As.
5. **API & UI**: A FastAPI backend and React frontend to explore the clusters and perform semantic search.

## Setup

### Option 1: Docker (Recommended)

1. Rename `backend/.env.example` to `backend/.env` and add your `GEMINI_API_KEY`.
2. Run the entire stack:
   ```bash
   docker-compose up --build
   ```
3. Open `http://localhost:5173` to view the Frontend.
4. Open `http://localhost:8000/docs` to view the Backend API documentation.

### Option 2: Local Development

#### Prerequisites
- PostgreSQL 16+ with `pgvector` extension enabled.
- Python 3.12+
- Node.js 18+

#### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env # Add your API keys
```

Ensure your local PostgreSQL has `pgvector` enabled:
```sql
CREATE EXTENSION vector;
```

#### Running the Pipeline
You can run the end-to-end pipeline to scrape, extract, and cluster data:
```bash
python backend/scripts/run_pipeline.py
```

#### Starting the Servers
**Backend:**
```bash
cd backend
uvicorn api.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Testing

```bash
# Backend API Tests
pytest backend/tests/test_api.py

# Frontend E2E Tests
python frontend/tests/e2e_test.py
```
