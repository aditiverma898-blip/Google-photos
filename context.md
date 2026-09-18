**Build Spec: AI-Powered Discovery Engine — Google Photos Vague Retrieval (High-Scale, Gemini-Native)**

**1. Context (for the builder agent)**
I am a PM working on Google Photos Core Experience. Users frequently remember a photo exists but cannot recall the exact metadata (date, location, album) required for traditional search to succeed. I need a high-scale research tool that mines 10,000+ public user complaints about Google Photos retrieval failures. This engine must extract structured failure patterns and use the aggregated dataset to explicitly answer core product questions. The deliverable is a queryable dataset, a synthesized insights dashboard, and an interactive testing front-end.

**2. Problem Statement**
Build a high-volume data pipeline that ingests 10,000 to 12,000 pieces of public user commentary regarding Google Photos search failures. The system must use the Gemini API ecosystem to extract a strictly typed schema from each narrative, cluster these records to identify distinct retrieval-failure patterns, and generate an AI-synthesized report that explicitly answers predefined strategic questions about user memory, forgotten information, and search behavior.

**3. Inputs to Ingest (Target: 10,000 - 12,000 items)**
To achieve the 10k+ volume, the ingestion engine must utilize batching, handle pagination, and manage rate limits across multiple sources:

* **Reddit:** r/googlephotos, r/Android, r/photography (Use Reddit API to pull historical search threads).
* **App Stores:** Google Play Store and Apple App Store reviews (Use scraper libraries, filtering for 1-3 star reviews containing keywords like "find", "search", "lost", "remember").
* **Google Photos Help Community:** Scrape support forum threads regarding search and missing photos.
* **Social/YouTube:** Extract comments from Google Photos search tutorials and generic social complaints.

**4. Required Extraction Schema (Per Feedback Item)**
Process every raw text item through the **Gemini Batch API** (using `gemini-1.5-flash` or `gemini-2.0-flash`) leveraging **Structured Outputs**. Pass a strict JSON Schema `responseFormat` to guarantee predictable type-safe extraction. Discard items that do not describe a specific retrieval attempt.

* **`source_platform` & `url_id`:** Origin of the data.
* **`raw_text`:** The original user snippet.
* **`photo_type`:** The category of media the user is looking for (e.g., document, old vacation, pet, screenshot) to answer what kinds of photos users struggle with.
* **`remembered_attributes`:** What the user successfully recalled (e.g., visual features, event, people).
* **`forgotten_attributes`:** What the user explicitly lacked (e.g., exact year, location name, file type).
* **`search_strategy`:** How they attempted the search with their incomplete memory (e.g., scrolling, keyword guessing, filtering).
* **`failure_point`:** Why the app failed them (e.g., returned zero results, returned 1,000 irrelevant results).
* **`workaround` & `emotional_signal`:** What they did instead and the stakes of the lost photo.

**5. Clustering, Synthesis & Q&A Layer**

* **Vectorization:** Embed the structured records (specifically the failure points and search strategies) using Gemini's `text-embedding-004` model. Cluster the resulting embeddings using HDBSCAN or K-means.
* **Cluster Metrics:** Compute frequency, source diversity, and a severity proxy for each cluster.
* **AI Synthesis Engine:** The workflow must include a final Gemini summarization step that analyzes the entire clustered dataset to generate explicit, evidence-backed answers to these core questions:
  * *What kinds of old photos do users struggle to retrieve?*
  * *What information do people actually remember about a photo?*
  * *What information have they forgotten?*
  * *How do users formulate searches when their memory is incomplete?*
  * *Which retrieval failure cluster causes the highest user churn/frustration?*



**6. Output / Deliverable Requirements**
The workflow must be deployed as a testable web application (Streamlit or React) featuring three distinct views:

* **The Insights Dashboard:** A top-level view where the AI engine directly answers the 5 core questions listed above, citing specific cluster data and verbatim quotes as evidence.
* **The Opportunity Table:** A ranked, explorable view of the clustered retrieval failures (frequency, severity, and drill-down into raw user quotes).
* **Real-Time Testing Input:** A text box where a user (or grader) can paste a new raw complaint. The engine must dynamically run the Gemini extraction schema, display the parsed JSON, and assign it to the closest existing cluster.

**7. Suggested Scalable Gemini Stack**

* **Ingestion & Queue:** Python asynchronous scrapers saving directly to `.jsonl` files for batch processing.
* **Extraction:** **Gemini Batch API** with Structured Outputs. Batching provides a highly cost-effective way (50% standard rate discount) to process 10,000+ items asynchronously without hitting standard rate limits.
* **Storage & Vector Search:** PostgreSQL with `pgvector` or a dedicated vector database (Pinecone/Qdrant) to handle the `text-embedding-004` vectors efficiently.
* **Serving:** Streamlit or Vercel/React.

**8. Definition of Done**

* 10,000+ real retrieval-failure items ingested, parsed, and stored.
* The web app explicitly features the AI-generated answers to the core strategic questions, backed by data metrics.
* The interactive "Test the Engine" feature works in real-time.
* The exact system prompt and JSON Schema used for the Gemini extraction step are clearly documented and accessible in the UI (required for the 1-slide explanation deliverable).
