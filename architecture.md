# Architecture — AI-Powered Discovery Engine
## Google Photos Vague Retrieval (High-Scale, Gemini-Native)

---

## 1. System Overview

The Discovery Engine is an end-to-end data pipeline and analytics platform that:

1. **Ingests** 10,000–12,000 pieces of public user commentary about Google Photos search failures from diverse sources.
2. **Extracts** a strictly typed JSON schema from each narrative using the Gemini Batch API with Structured Outputs.
3. **Embeds & Clusters** the extracted records to surface distinct retrieval-failure patterns.
4. **Synthesizes** AI-generated, evidence-backed answers to five core strategic product questions.
5. **Serves** the results through an interactive web application with three views: Insights Dashboard, Opportunity Table, and Real-Time Testing Input.

---

## 2. High-Level Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          DATA INGESTION LAYER                          │
│                                                                        │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────────┐   │
│  │  Reddit    │  │ App Store  │  │ Google     │  │  YouTube /     │   │
│  │  Scraper   │  │ Scraper    │  │ Help Forum │  │  Social        │   │
│  │  (API)     │  │ (Library)  │  │ Scraper    │  │  Scraper       │   │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └───────┬────────┘   │
│        │               │               │                 │            │
│        └───────────────┴───────┬───────┴─────────────────┘            │
│                                │                                      │
│                    ┌───────────▼───────────┐                          │
│                    │  Raw Data Store       │                          │
│                    │  (.jsonl files)       │                          │
│                    └───────────┬───────────┘                          │
└────────────────────────────────┼──────────────────────────────────────┘
                                 │
┌────────────────────────────────▼──────────────────────────────────────┐
│                      EXTRACTION LAYER (Gemini)                       │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │              Gemini Batch API (gemini-2.0-flash)                │  │
│  │         Structured Outputs — strict JSON Schema                 │  │
│  │                                                                 │  │
│  │   Inputs:  raw_text from .jsonl batches                        │  │
│  │   Outputs: typed extraction records                             │  │
│  │   Filter:  discard non-retrieval narratives                     │  │
│  └──────────────────────────┬──────────────────────────────────────┘  │
└─────────────────────────────┼────────────────────────────────────────┘
                              │
┌─────────────────────────────▼────────────────────────────────────────┐
│                   STORAGE & VECTOR LAYER                             │
│                                                                      │
│  ┌──────────────────────────┐   ┌────────────────────────────────┐   │
│  │ PostgreSQL + pgvector    │   │  Structured Records Table      │   │
│  │                          │   │  (source_platform, photo_type, │   │
│  │  • embedding column      │   │   remembered_attributes,       │   │
│  │    (768-d float[])       │   │   forgotten_attributes,        │   │
│  │  • cosine similarity     │   │   search_strategy,             │   │
│  │    index (IVFFlat/HNSW)  │   │   failure_point, workaround,   │   │
│  │                          │   │   emotional_signal, cluster_id)│   │
│  └──────────────────────────┘   └────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────▼────────────────────────────────────────┐
│              CLUSTERING & SYNTHESIS LAYER                            │
│                                                                      │
│  ┌───────────────────┐   ┌───────────────────────────────────────┐   │
│  │ text-embedding-004│   │  Clustering Engine                    │   │
│  │ (Gemini Embed)    │──▶│  (HDBSCAN primary / K-Means fallback)│   │
│  └───────────────────┘   └──────────────┬────────────────────────┘   │
│                                         │                            │
│                          ┌──────────────▼────────────────────────┐   │
│                          │  AI Synthesis Engine                  │   │
│                          │  (Gemini Pro — summarization pass)    │   │
│                          │  Answers 5 core strategic questions   │   │
│                          └──────────────┬────────────────────────┘   │
└─────────────────────────────────────────┼────────────────────────────┘
                                          │
┌─────────────────────────────────────────▼────────────────────────────┐
│                        SERVING LAYER (Web App)                       │
│                                                                      │
│       ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐       │
│       │  Insights    │  │ Opportunity  │  │  Real-Time       │       │
│       │  Dashboard   │  │ Table        │  │  Testing Input   │       │
│       │  (Q&A View)  │  │ (Clusters)   │  │  (Live Gemini)   │       │
│       └──────────────┘  └──────────────┘  └──────────────────┘       │
│                                                                      │
│                    React (Vite) + FastAPI Backend                     │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 3. Layer-by-Layer Detail

### 3.1 Data Ingestion Layer

| Source | Method | Target Volume | Key Filters |
|---|---|---|---|
| **Reddit** (`r/googlephotos`, `r/Android`, `r/photography`) | Reddit Data API (OAuth2) — paginated historical pulls | 3,000–4,000 | Threads/comments mentioning search, find, lost, missing |
| **App Stores** (Google Play, Apple App Store) | `google-play-scraper` / `app-store-scraper` npm libraries (Python wrappers) | 3,000–4,000 | 1–3 star reviews; keyword filter: `find`, `search`, `lost`, `remember` |
| **Google Photos Help Community** | HTTP scraper (BeautifulSoup / Playwright) | 2,000–3,000 | Forum threads tagged "search", "missing photos" |
| **YouTube / Social** | YouTube Data API v3 (comment threads on tutorials) + Twitter/X API | 1,000–2,000 | Comments on Google Photos search tutorial videos |

#### Ingestion Design Principles

- **Asynchronous I/O:** All scrapers use `asyncio` + `aiohttp` (or Playwright for JS-rendered pages) to maximize throughput.
- **Rate-Limit Management:** Per-source token-bucket rate limiters. Exponential backoff with jitter on 429 responses.
- **Deduplication:** SHA-256 hash of `(source_platform, raw_text)` written to a Bloom filter to avoid storing duplicates.
- **Output Format:** Each scraper writes to a partitioned `.jsonl` file: `raw_data/{source}/{YYYY-MM-DD}/{batch_id}.jsonl`.
- **Checkpoint & Resume:** Each scraper persists a cursor/offset to allow resumption after interruption.

#### Raw Record Schema (Pre-Extraction)

```json
{
  "source_platform": "reddit",
  "url_id": "https://reddit.com/r/googlephotos/comments/abc123",
  "raw_text": "I know I took a photo of my dog at the beach last summer but...",
  "scraped_at": "2026-09-17T12:00:00Z",
  "metadata": {
    "subreddit": "googlephotos",
    "score": 42,
    "num_replies": 7
  }
}
```

---

### 3.2 Extraction Layer (Gemini Batch API)

#### Pipeline Flow

```
.jsonl batch files
       │
       ▼
┌──────────────────────────────────────────────────┐
│           Batch Preparation Service              │
│  • Reads .jsonl files in chunks of 1,000         │
│  • Constructs Gemini Batch API request payloads  │
│  • Attaches JSON Schema for Structured Outputs   │
└───────────────────┬──────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────┐
│           Gemini Batch API                       │
│  Model: gemini-2.0-flash                         │
│  Mode:  Structured Outputs (responseFormat)      │
│  Cost:  50% discount vs. standard API            │
│  Concurrency: up to 10 concurrent batch jobs     │
└───────────────────┬──────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────┐
│           Post-Processing Service                │
│  • Validates extracted JSON against schema        │
│  • Discards items with is_retrieval_attempt=false │
│  • Writes valid records to PostgreSQL             │
└──────────────────────────────────────────────────┘
```

#### Extraction JSON Schema (Structured Output)

```json
{
  "type": "object",
  "properties": {
    "is_retrieval_attempt": {
      "type": "boolean",
      "description": "True if the text describes a specific attempt to find/retrieve a photo in Google Photos."
    },
    "source_platform": {
      "type": "string",
      "enum": ["reddit", "play_store", "app_store", "help_community", "youtube", "social"]
    },
    "url_id": {
      "type": "string",
      "description": "Original URL or unique identifier of the source item."
    },
    "raw_text": {
      "type": "string",
      "description": "The original user complaint verbatim."
    },
    "photo_type": {
      "type": "string",
      "enum": ["document", "screenshot", "old_vacation", "pet", "family_event", "selfie", "landmark", "food", "receipt", "other"],
      "description": "Category of media the user is looking for."
    },
    "remembered_attributes": {
      "type": "array",
      "items": { "type": "string" },
      "description": "What the user successfully recalled (visual features, event, people, approximate time)."
    },
    "forgotten_attributes": {
      "type": "array",
      "items": { "type": "string" },
      "description": "What the user explicitly lacked (exact date, location name, file type, album)."
    },
    "search_strategy": {
      "type": "string",
      "enum": ["keyword_search", "scrolling_timeline", "album_browsing", "people_face_search", "location_search", "date_filter", "combined_filters", "google_lens", "other"],
      "description": "How the user attempted the search with incomplete memory."
    },
    "failure_point": {
      "type": "string",
      "description": "Why the app failed them (zero results, irrelevant results, too many results, crashed, etc.)."
    },
    "workaround": {
      "type": "string",
      "description": "What the user did instead (manual scroll, gave up, used another app, asked someone)."
    },
    "emotional_signal": {
      "type": "string",
      "enum": ["frustrated", "angry", "disappointed", "sad", "resigned", "neutral"],
      "description": "Emotional intensity / stakes of the lost photo."
    }
  },
  "required": [
    "is_retrieval_attempt", "source_platform", "url_id", "raw_text",
    "photo_type", "remembered_attributes", "forgotten_attributes",
    "search_strategy", "failure_point", "workaround", "emotional_signal"
  ]
}
```

#### Gemini System Prompt (Extraction)

```
You are a data extraction agent specializing in user-experience failure analysis for
Google Photos. You are given a raw user complaint about photo search or retrieval.

Your task:
1. Determine if this text describes a SPECIFIC attempt to find or retrieve a photo
   in Google Photos. Set is_retrieval_attempt accordingly.
2. If yes, extract every field in the output schema from the narrative.
   - For remembered_attributes and forgotten_attributes, be exhaustive — extract
     every detail the user mentions (or implies they lack).
   - For photo_type, infer the closest category from the user's description.
   - For emotional_signal, assess the overall tone and stakes described.
3. If no, set is_retrieval_attempt to false and fill remaining fields with
   sensible defaults.

Be precise. Do not hallucinate attributes the user did not mention.
```

---

### 3.3 Storage & Vector Layer

#### Database Schema (PostgreSQL + pgvector)

```sql
-- Enable the pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Core extracted records table
CREATE TABLE feedback_records (
    id                    BIGSERIAL PRIMARY KEY,
    source_platform       VARCHAR(20)   NOT NULL,
    url_id                TEXT          NOT NULL UNIQUE,
    raw_text              TEXT          NOT NULL,
    photo_type            VARCHAR(30)   NOT NULL,
    remembered_attributes JSONB         NOT NULL,  -- string array
    forgotten_attributes  JSONB         NOT NULL,  -- string array
    search_strategy       VARCHAR(30)   NOT NULL,
    failure_point         TEXT          NOT NULL,
    workaround            TEXT,
    emotional_signal      VARCHAR(20)   NOT NULL,
    cluster_id            INTEGER,                  -- assigned after clustering
    embedding             vector(768),              -- text-embedding-004 output
    created_at            TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

-- HNSW index for fast cosine-similarity nearest-neighbour queries
CREATE INDEX idx_feedback_embedding
    ON feedback_records
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Cluster metadata table
CREATE TABLE clusters (
    cluster_id        INTEGER PRIMARY KEY,
    label             TEXT          NOT NULL,       -- human-readable cluster name
    description       TEXT,                         -- AI-generated summary
    record_count      INTEGER       NOT NULL,
    source_diversity  JSONB         NOT NULL,       -- { "reddit": 120, "play_store": 85, ... }
    severity_score    FLOAT         NOT NULL,       -- 0.0 – 1.0 composite severity proxy
    top_failure_points JSONB        NOT NULL,       -- top-5 failure descriptions
    representative_quotes JSONB     NOT NULL,       -- 5-10 verbatim user quotes
    centroid          vector(768)                   -- cluster centroid for assignment
);

-- Synthesis results table
CREATE TABLE synthesis_answers (
    question_id     SERIAL PRIMARY KEY,
    question_text   TEXT    NOT NULL,
    answer_text     TEXT    NOT NULL,               -- AI-generated answer
    evidence        JSONB   NOT NULL,               -- cited cluster IDs, quotes, metrics
    generated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Ingestion tracking table
CREATE TABLE ingestion_log (
    id              BIGSERIAL PRIMARY KEY,
    source_platform VARCHAR(20) NOT NULL,
    batch_file      TEXT        NOT NULL,
    records_scraped INTEGER     NOT NULL,
    records_valid   INTEGER     NOT NULL,
    started_at      TIMESTAMPTZ NOT NULL,
    completed_at    TIMESTAMPTZ
);
```

#### Why PostgreSQL + pgvector?

| Criterion | PostgreSQL + pgvector | Dedicated Vector DB (Pinecone/Qdrant) |
|---|---|---|
| Operational complexity | Single database for relational + vector | Two systems to manage |
| Cost at 10–12K vectors | Free / minimal | Free tier may suffice, but adds integration |
| Hybrid queries (filter + ANN) | Native SQL `WHERE` + `ORDER BY embedding <=> $1` | Requires metadata filter API |
| Ecosystem | Mature, well-understood | Newer, less tooling |
| **Decision** | **Primary choice** | Fallback if vector query latency > 200ms at scale |

---

### 3.4 Clustering & Synthesis Layer

#### 3.4.1 Embedding Generation

```
Extracted Records (failure_point + search_strategy concatenation)
        │
        ▼
  Gemini text-embedding-004 API
  (batch embed, 768-dimensional output)
        │
        ▼
  Store embeddings in feedback_records.embedding
```

- **Input text for embedding:** Concatenation of `failure_point` and `search_strategy` fields — these are the most discriminating attributes for clustering retrieval failures.
- **Batch size:** 100 texts per API call (Gemini embedding batch limit).
- **Output:** 768-dimensional float vector per record.

#### 3.4.2 Clustering Pipeline

```
┌────────────────────────────────────────────────────┐
│                Clustering Pipeline                  │
│                                                    │
│  1. Load all 768-d embeddings from PostgreSQL      │
│  2. Dimensionality reduction: UMAP (n=50)          │
│  3. Primary clustering: HDBSCAN                    │
│     • min_cluster_size = 30                        │
│     • min_samples = 10                             │
│     • metric = cosine                              │
│  4. Fallback: If HDBSCAN produces < 5 clusters    │
│     → K-Means (k = silhouette-optimized, 8–20)    │
│  5. Assign cluster_id to each record               │
│  6. Compute cluster metrics:                       │
│     • record_count                                 │
│     • source_diversity (count per platform)        │
│     • severity_score (composite of emotional       │
│       signal distribution + workaround = "gave_up")│
│  7. Generate cluster labels via Gemini             │
│     (pass top-10 representative records per        │
│      cluster to gemini-2.0-flash for labeling)     │
│  8. Write cluster metadata to clusters table       │
└────────────────────────────────────────────────────┘
```

#### 3.4.3 Severity Score Computation

```python
severity_score = (
    0.40 * emotional_weight      # weighted avg of emotional signals in cluster
  + 0.30 * workaround_weight     # fraction of "gave_up" workarounds
  + 0.20 * frequency_weight      # cluster_size / total_records (normalized)
  + 0.10 * source_diversity_weight  # num distinct sources (normalized)
)
```

| Emotional Signal | Weight |
|---|---|
| angry | 1.0 |
| frustrated | 0.8 |
| sad | 0.7 |
| disappointed | 0.5 |
| resigned | 0.4 |
| neutral | 0.1 |

#### 3.4.4 AI Synthesis Engine

```
┌─────────────────────────────────────────────────────────┐
│                 Synthesis Workflow                       │
│                                                         │
│  Input:  All cluster metadata + top quotes per cluster  │
│  Model:  gemini-2.0-flash (or gemini-1.5-pro for depth) │
│  Prompt: "Analyze the following cluster dataset and     │
│           provide evidence-backed answers to each of    │
│           the 5 strategic questions. Cite cluster IDs,  │
│           record counts, and verbatim user quotes."     │
│                                                         │
│  Questions:                                             │
│   Q1: What kinds of old photos do users struggle to     │
│       retrieve?                                         │
│   Q2: What information do people actually remember      │
│       about a photo?                                    │
│   Q3: What information have they forgotten?             │
│   Q4: How do users formulate searches when their memory │
│       is incomplete?                                    │
│   Q5: Which retrieval failure cluster causes the        │
│       highest user churn/frustration?                   │
│                                                         │
│  Output: Structured answer per question, stored in      │
│          synthesis_answers table                         │
└─────────────────────────────────────────────────────────┘
```

---

### 3.5 Serving Layer (Web Application)

#### Technology Choice: React (Vite) + FastAPI

| Concern | Technology | Rationale |
|---|---|---|
| Frontend | React 18 + Vite + Recharts/D3 | Rich interactivity, component reuse, modern DX |
| Backend API | FastAPI (Python) | Async-native, automatic OpenAPI docs, direct Gemini SDK access |
| Deployment | Vercel (frontend) + Railway/Render (backend) | Zero-config deploys, free tiers available |

#### Application Views

##### View 1: Insights Dashboard

```
┌─────────────────────────────────────────────────────┐
│                 INSIGHTS DASHBOARD                   │
│                                                     │
│  ┌───────────────────────────────────────────────┐  │
│  │  Q1: What kinds of old photos...?             │  │
│  │  ─────────────────────────────────            │  │
│  │  [AI-generated answer paragraph]              │  │
│  │  📊 Evidence: Cluster 3 (n=842), Cluster 7... │  │
│  │  💬 "I know I took a beach photo last..."     │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
│  ┌───────────────────────────────────────────────┐  │
│  │  Q2: What do people remember...?              │  │
│  │  ...                                          │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
│  (Q3, Q4, Q5 cards follow the same pattern)         │
│                                                     │
│  ┌───────────────────────────────────────────────┐  │
│  │  📈  Aggregate Stats Bar                      │  │
│  │  Total Records: 10,247 | Clusters: 14         │  │
│  │  Sources: Reddit 38% | Play Store 32% | ...   │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

##### View 2: Opportunity Table

```
┌──────────────────────────────────────────────────────────────────┐
│                    OPPORTUNITY TABLE                              │
│                                                                  │
│  Rank │ Cluster Label        │ Count │ Severity │ Top Source    │
│  ─────┼──────────────────────┼───────┼──────────┼──────────────│
│   1   │ Old vacation photos  │  842  │  0.91    │ Reddit       │
│   2   │ Document/receipt     │  731  │  0.87    │ Play Store   │
│   3   │ Pet photos           │  623  │  0.82    │ Help Forum   │
│   ...                                                            │
│                                                                  │
│  [Click any row to expand → raw quotes, attribute breakdown]     │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  Expanded: "Old vacation photos" (Cluster #1)            │    │
│  │  Remembered: visual scene (72%), people (58%), season    │    │
│  │  Forgotten:  exact year (89%), location name (67%)       │    │
│  │  Strategy:   scrolling_timeline (45%), keyword (33%)     │    │
│  │  Quotes: "I scrolled for 20 minutes looking for..."      │    │
│  └──────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
```

##### View 3: Real-Time Testing Input

```
┌─────────────────────────────────────────────────────┐
│              TEST THE ENGINE                         │
│                                                     │
│  ┌───────────────────────────────────────────────┐  │
│  │  Paste a raw user complaint here:             │  │
│  │  ┌─────────────────────────────────────────┐  │  │
│  │  │  [text area]                            │  │  │
│  │  └─────────────────────────────────────────┘  │  │
│  │                        [ ▶ Analyze ]          │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
│  ┌───────────────────────────────────────────────┐  │
│  │  Extracted Schema (live Gemini response):     │  │
│  │  {                                            │  │
│  │    "photo_type": "old_vacation",              │  │
│  │    "remembered_attributes": ["beach", ...],   │  │
│  │    "search_strategy": "scrolling_timeline",   │  │
│  │    ...                                        │  │
│  │  }                                            │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
│  ┌───────────────────────────────────────────────┐  │
│  │  Nearest Cluster: #1 "Old vacation photos"   │  │
│  │  Cosine similarity: 0.87                      │  │
│  │  Cluster severity: 0.91                       │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

---

### 3.6 API Design (FastAPI Backend)

#### Core Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/insights` | Returns all 5 synthesized answers with evidence |
| `GET` | `/api/clusters` | Returns ranked list of all clusters with metrics |
| `GET` | `/api/clusters/{cluster_id}` | Returns cluster detail: quotes, attribute breakdown |
| `GET` | `/api/clusters/{cluster_id}/records` | Paginated raw records for a cluster |
| `POST` | `/api/analyze` | Accepts raw text → runs live Gemini extraction → returns parsed JSON + nearest cluster |
| `GET` | `/api/stats` | Aggregate statistics (total records, source distribution, cluster count) |
| `GET` | `/api/schema` | Returns the exact JSON Schema and system prompt used for Gemini extraction |

#### `/api/analyze` Request / Response

```json
// REQUEST
POST /api/analyze
{
  "raw_text": "I remember taking a photo of my daughter's birthday cake last year but I can't find it..."
}

// RESPONSE
{
  "extraction": {
    "is_retrieval_attempt": true,
    "photo_type": "family_event",
    "remembered_attributes": ["birthday cake", "daughter", "last year"],
    "forgotten_attributes": ["exact date", "location"],
    "search_strategy": "keyword_search",
    "failure_point": "returned irrelevant results",
    "workaround": "manual scrolling",
    "emotional_signal": "frustrated"
  },
  "nearest_cluster": {
    "cluster_id": 5,
    "label": "Family event photos",
    "cosine_similarity": 0.84,
    "severity_score": 0.78
  }
}
```

---

## 4. Data Flow (End-to-End Pipeline)

```mermaid
flowchart TD
    A["Async Scrapers<br/>(Reddit, App Store, Help Forum, YouTube)"] -->|".jsonl files"| B["Raw Data Store<br/>(partitioned .jsonl)"]
    B -->|"Batch chunks of 1,000"| C["Gemini Batch API<br/>(gemini-2.0-flash + Structured Outputs)"]
    C -->|"Validated JSON records"| D["PostgreSQL<br/>(feedback_records table)"]
    D -->|"failure_point + search_strategy"| E["Gemini text-embedding-004<br/>(768-d vectors)"]
    E -->|"Store embedding column"| D
    D -->|"All embeddings"| F["UMAP + HDBSCAN<br/>(Clustering Pipeline)"]
    F -->|"cluster_id per record"| D
    F -->|"Cluster metadata"| G["clusters table"]
    G -->|"All cluster data + quotes"| H["Gemini Synthesis<br/>(Answer 5 core questions)"]
    H -->|"Answers + evidence"| I["synthesis_answers table"]
    D & G & I -->|"FastAPI queries"| J["FastAPI Backend"]
    J -->|"REST API"| K["React Frontend<br/>(3 views)"]
```

---

## 5. Directory / Project Structure

```
google-photos-discovery-engine/
├── README.md
├── context.md
├── architecture.md
│
├── backend/
│   ├── pyproject.toml                 # Python deps (fastapi, google-genai, asyncpg, scikit-learn, hdbscan, umap-learn)
│   ├── .env.example                   # GEMINI_API_KEY, DATABASE_URL
│   │
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── base_scraper.py            # Abstract async scraper with rate limiting
│   │   ├── reddit_scraper.py
│   │   ├── appstore_scraper.py
│   │   ├── helpforum_scraper.py
│   │   ├── youtube_scraper.py
│   │   └── run_ingestion.py           # Orchestrator: runs all scrapers, writes .jsonl
│   │
│   ├── extraction/
│   │   ├── __init__.py
│   │   ├── schema.py                  # JSON Schema definition + system prompt
│   │   ├── batch_processor.py         # Gemini Batch API wrapper
│   │   └── validator.py              # Post-extraction validation & filtering
│   │
│   ├── clustering/
│   │   ├── __init__.py
│   │   ├── embedder.py                # Gemini text-embedding-004 batch client
│   │   ├── cluster_engine.py          # UMAP + HDBSCAN / K-Means pipeline
│   │   ├── metrics.py                 # Severity score, source diversity computation
│   │   └── labeler.py                 # Gemini-based cluster label generation
│   │
│   ├── synthesis/
│   │   ├── __init__.py
│   │   └── synthesizer.py             # Gemini summarization — 5 core questions
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI app entry point
│   │   ├── routes/
│   │   │   ├── insights.py            # GET /api/insights
│   │   │   ├── clusters.py            # GET/POST /api/clusters
│   │   │   ├── analyze.py             # POST /api/analyze (real-time)
│   │   │   └── stats.py               # GET /api/stats, /api/schema
│   │   └── models.py                  # Pydantic request/response models
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── connection.py              # asyncpg connection pool
│   │   └── migrations/
│   │       └── 001_init.sql           # CREATE TABLE statements
│   │
│   └── data/
│       └── raw/                       # .jsonl output from scrapers
│           ├── reddit/
│           ├── appstore/
│           ├── helpforum/
│           └── youtube/
│
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── api/
│       │   └── client.js              # Axios/fetch wrapper for FastAPI
│       ├── components/
│       │   ├── InsightCard.jsx         # Single Q&A insight card
│       │   ├── ClusterTable.jsx        # Sortable, expandable cluster table
│       │   ├── ClusterDetail.jsx       # Drill-down view for a single cluster
│       │   ├── AnalyzeInput.jsx        # Real-time testing text area
│       │   ├── StatsBar.jsx            # Aggregate statistics bar
│       │   └── SchemaViewer.jsx        # Displays JSON Schema + system prompt
│       ├── pages/
│       │   ├── DashboardPage.jsx       # Insights Dashboard (View 1)
│       │   ├── OpportunityPage.jsx     # Opportunity Table (View 2)
│       │   └── TestPage.jsx            # Real-Time Testing (View 3)
│       └── styles/
│           ├── index.css               # Global styles, design tokens
│           └── components/             # Component-level CSS modules
│
└── scripts/
    ├── run_pipeline.py                 # End-to-end: ingest → extract → embed → cluster → synthesize
    ├── seed_db.py                      # Seed DB with sample data for development
    └── export_report.py               # Export synthesis answers as PDF/Markdown
```

---

## 6. Execution Pipeline (Ordered Workflow)

| Phase | Step | Tool / Service | Est. Duration | Notes |
|---|---|---|---|---|
| **1. Ingest** | Run all 4 scrapers concurrently | `run_ingestion.py` | 2–6 hours | Rate-limited; writes ~12K raw records |
| **2. Extract** | Batch-process .jsonl through Gemini | Gemini Batch API | 1–3 hours | 50% cost discount; 10 concurrent batches |
| **3. Validate** | Filter non-retrieval items | `validator.py` | < 5 min | Expect ~15–20% discard rate |
| **4. Store** | Insert valid records into PostgreSQL | `asyncpg` | < 5 min | Bulk `COPY` for speed |
| **5. Embed** | Generate 768-d vectors | `text-embedding-004` | 30–60 min | Batch embed 100 at a time |
| **6. Cluster** | UMAP → HDBSCAN | `cluster_engine.py` | < 10 min | CPU-bound; ~10K × 768 matrix |
| **7. Label** | Generate cluster labels | Gemini Flash | < 5 min | 1 API call per cluster |
| **8. Synthesize** | Answer 5 core questions | Gemini Flash/Pro | < 5 min | Single large-context call |
| **9. Serve** | Start FastAPI + React dev servers | `uvicorn` + `vite dev` | Immediate | Ready for testing |

**Total estimated pipeline runtime: 4–10 hours** (dominated by ingestion and extraction).

---

## 7. Environment & Configuration

### Required API Keys / Secrets

| Variable | Source | Purpose |
|---|---|---|
| `GEMINI_API_KEY` | Google AI Studio | Batch extraction, embedding, synthesis, real-time analysis |
| `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET` | Reddit Developer Portal | Reddit API access |
| `DATABASE_URL` | PostgreSQL provider | `postgresql+asyncpg://user:pass@host:5432/discovery_engine` |
| `YOUTUBE_API_KEY` | Google Cloud Console | YouTube Data API v3 |

### Python Dependencies (Core)

```
google-genai >= 1.0.0
fastapi >= 0.115.0
uvicorn >= 0.30.0
asyncpg >= 0.30.0
aiohttp >= 3.10.0
praw >= 7.7.0            # Reddit API
google-play-scraper >= 1.2.0
beautifulsoup4 >= 4.12.0
playwright >= 1.45.0
scikit-learn >= 1.5.0
hdbscan >= 0.8.0
umap-learn >= 0.5.0
numpy >= 1.26.0
pandas >= 2.2.0
```

---

## 8. Key Design Decisions & Trade-offs

| Decision | Choice | Rationale |
|---|---|---|
| **Batch vs. Online extraction** | Gemini Batch API | 50% cost reduction; no rate-limit pressure at 10K+ scale |
| **Embedding model** | `text-embedding-004` | Native Gemini ecosystem; 768-d is sufficient for clustering |
| **Clustering algorithm** | HDBSCAN (primary) | Density-based = automatic cluster count; handles noise well |
| **Vector storage** | pgvector (single DB) | Reduces operational complexity; sufficient at 10K vector scale |
| **Frontend framework** | React + Vite | Richer interactivity than Streamlit for the three-view requirement |
| **Backend framework** | FastAPI | Async-native Python; direct Gemini SDK access; auto-generated docs |
| **Embedding input** | `failure_point` + `search_strategy` | These fields most discriminate failure *type*; including `raw_text` would add noise |

---

## 9. Scalability & Failure Handling

### Rate Limiting & Backoff

- All external API calls use a per-source `asyncio.Semaphore` + token-bucket rate limiter.
- Exponential backoff with jitter (base = 1s, max = 60s, factor = 2) on HTTP 429 / 503 responses.
- Gemini Batch API jobs are polled every 30 seconds; failed batches are automatically retried up to 3 times.

### Data Integrity

- `.jsonl` files are append-only and immutable after scraping completes.
- PostgreSQL `url_id UNIQUE` constraint prevents duplicate extraction records.
- SHA-256 content hashing in Bloom filter catches near-duplicate raw texts before extraction.

### Monitoring

- Ingestion progress logged to `ingestion_log` table (records scraped vs. valid per batch).
- Pipeline orchestrator (`run_pipeline.py`) prints phase-level progress and estimated time remaining.

---

## 10. Security & Compliance

| Concern | Mitigation |
|---|---|
| **Data is public** | All ingested data comes from publicly accessible sources (Reddit, app stores, forums, YouTube) |
| **PII in complaints** | Extraction schema does not capture user names or emails; raw_text may contain incidental PII — apply regex-based PII scrubber before storage |
| **API key management** | Keys stored in `.env` (gitignored), never committed; use secret manager in production |
| **Rate limit compliance** | All scrapers respect `robots.txt` and API ToS rate limits |
