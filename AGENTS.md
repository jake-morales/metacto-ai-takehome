# AGENTS.md — AI-First Feature Request Tracker (BiteFlight PoC)

## Project Overview

An AI-first feature request tracking system, built as a proof of concept in the context of **BiteFlight**, a food delivery company. The system ingests feature requests from three customer types (users, drivers, merchants), uses AI to deduplicate, cluster, and prioritize them, and surfaces actionable insights for internal product teams.

### Design goal

Scale to **hundreds of thousands** of feature requests with fast analysis and report generation.

---

## Domain Context

**BiteFlight** is a food delivery platform with three customer segments:

| Segment      | Description                                      | Example requests                                           |
|--------------|--------------------------------------------------|------------------------------------------------------------|
| **Users**    | End consumers who order food                     | "Let me schedule orders in advance", "Add allergy filters" |
| **Drivers**  | Delivery couriers who fulfill orders             | "Show estimated tip before accepting", "Route optimization" |
| **Merchants**| Restaurants / stores that list items on the platform | "Bulk menu upload", "Real-time order analytics"            |

Each segment has distinct pain points; the system must capture, tag, and reason about requests per-segment and cross-segment.

---

## Core Capabilities

### 1. Submit a Feature Request
- Customers submit free-text feature requests via an API.
- Each request captures: submitter identity, customer segment, free-text description, optional category/tags, timestamp.
- AI processing on ingest: extract structured fields (intent, affected area, sentiment, urgency signals) and generate an embedding for similarity search.

### 2. View & Discover Existing Requests
- Customers can browse and search feature requests.
- **Semantic search** (vector similarity) so users find related requests even with different wording.
- Filter/facet by: segment, status, category, popularity, date range.
- AI-generated summaries for clusters of similar requests.

### 3. Express Interest / Support
- Customers can upvote or "+1" an existing request.
- Track interest signals: vote count, unique voter segments, velocity of votes over time.
- Support actions feed into prioritization scoring.

### 4. Internal Product Team Insights
- **AI-powered grouping**: automatically cluster related requests using embeddings + clustering algorithms.
- **Prioritization scoring**: combine vote count, segment diversity, recency, sentiment, and strategic alignment into a composite score.
- **Report generation**: on-demand or scheduled reports summarizing top themes, emerging trends, segment-specific priorities, and recommended actions.
- Reports must generate quickly even at scale (target: seconds, not minutes).

---

## Technical Architecture

### Stack Recommendations

| Layer              | Technology                  | Rationale                                                    |
|--------------------|-----------------------------|--------------------------------------------------------------|
| **Backend API**    | Python (FastAPI)            | Async-native, fast, great AI/ML library ecosystem            |
| **Database**       | PostgreSQL + pgvector       | Relational data + vector similarity search in one store      |
| **AI/Embeddings**  | Claude API (via Anthropic SDK) for analysis; an embedding model for vectors | Structured extraction, summarization, report generation |
| **Task Queue**     | Background tasks (FastAPI BackgroundTasks or Celery for heavier loads) | Async AI processing on ingest without blocking requests |
| **Frontend**       | React (Vite) or simple API-only for PoC | Keep PoC scope manageable; API-first design                 |

### Data Model (Core Entities)

```
FeatureRequest
  id: UUID
  title: str (AI-extracted or user-provided)
  description: text
  submitter_id: str
  segment: enum(user, driver, merchant)
  status: enum(new, under_review, planned, in_progress, shipped, declined)
  category: str (AI-assigned)
  tags: str[]
  embedding: vector(1536)
  sentiment: float
  urgency: float
  created_at: timestamp
  updated_at: timestamp

Vote
  id: UUID
  request_id: FK -> FeatureRequest
  voter_id: str
  voter_segment: enum(user, driver, merchant)
  created_at: timestamp

Cluster
  id: UUID
  label: str (AI-generated)
  summary: text (AI-generated)
  theme: str
  request_ids: UUID[]
  score: float (prioritization composite)
  created_at: timestamp
  updated_at: timestamp

Report
  id: UUID
  type: enum(segment_summary, trend_analysis, full_prioritization)
  content: jsonb
  generated_at: timestamp
  parameters: jsonb (filters used to generate)
```

### Key Design Decisions for Scale

1. **Embeddings at ingest**: compute and store embeddings when a request is created (async background task) so search and clustering read pre-computed vectors.
2. **pgvector for similarity**: avoids a separate vector DB dependency; PostgreSQL handles both relational queries and ANN search. Use IVFFlat or HNSW indexes for fast retrieval at scale.
3. **Pre-computed clusters**: run clustering periodically (or on-demand) rather than on every query. Store cluster assignments so reports pull from materialized results.
4. **Incremental processing**: new requests get assigned to the nearest existing cluster (or flagged for re-clustering) rather than re-clustering the entire dataset.
5. **Caching for reports**: cache generated reports with TTL; invalidate on significant data changes.

---

## AI Integration Points

| Operation                  | Model / Approach                          | When it runs              |
|----------------------------|-------------------------------------------|---------------------------|
| Extract structured fields  | Claude API (structured output)            | On request submission     |
| Generate embedding         | Embedding model (e.g., voyage, or OpenAI ada) | On request submission     |
| Find similar requests      | pgvector cosine similarity search         | On search / discovery     |
| Cluster requests           | HDBSCAN or K-means on embeddings          | Periodic batch job        |
| Generate cluster summaries | Claude API                                | After clustering          |
| Prioritization scoring     | Weighted formula + Claude for qualitative assessment | On-demand / scheduled   |
| Report generation          | Claude API (structured output → formatted report) | On-demand / scheduled   |

---

## API Design (Key Endpoints)

```
POST   /api/requests              — Submit a new feature request
GET    /api/requests              — List/search requests (filters, pagination, semantic search)
GET    /api/requests/{id}         — Get single request with vote count
POST   /api/requests/{id}/vote    — Vote for a request
DELETE /api/requests/{id}/vote    — Remove vote

GET    /api/clusters              — List clusters with summaries and scores
GET    /api/clusters/{id}         — Get cluster detail with member requests
POST   /api/clusters/refresh      — Trigger re-clustering

POST   /api/reports/generate      — Generate a report (params: type, filters)
GET    /api/reports               — List generated reports
GET    /api/reports/{id}          — Get a specific report

GET    /api/insights/trending     — Trending requests / emerging themes
GET    /api/insights/segments     — Per-segment breakdown
```

---

## Project Structure

```
biteflight-feature-tracker/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── config.py            # Settings & environment config
│   │   ├── models/              # SQLAlchemy / Pydantic models
│   │   │   ├── request.py
│   │   │   ├── vote.py
│   │   │   ├── cluster.py
│   │   │   └── report.py
│   │   ├── api/                 # Route handlers
│   │   │   ├── requests.py
│   │   │   ├── votes.py
│   │   │   ├── clusters.py
│   │   │   ├── reports.py
│   │   │   └── insights.py
│   │   ├── services/            # Business logic
│   │   │   ├── ai.py            # Claude API integration
│   │   │   ├── embeddings.py    # Embedding generation & search
│   │   │   ├── clustering.py    # Clustering logic
│   │   │   ├── scoring.py       # Prioritization scoring
│   │   │   └── reports.py       # Report generation
│   │   ├── db/                  # Database setup & migrations
│   │   │   ├── session.py
│   │   │   └── migrations/
│   │   └── tasks/               # Background task definitions
│   │       └── ingest.py
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                    # Optional for PoC
│   └── ...
├── docker-compose.yml           # PostgreSQL + pgvector + app
├── seed_data/                   # Sample BiteFlight feature requests
│   └── requests.json
├── AGENTS.md
├── CLAUDE.md
└── README.md
```

---

## Implementation Priorities (PoC Phases)

### Phase 1 — Foundation
- [ ] Project scaffolding (FastAPI, PostgreSQL + pgvector, Docker Compose)
- [ ] Data models and migrations
- [ ] CRUD endpoints for feature requests
- [ ] Voting system

### Phase 2 — AI Layer
- [ ] Embedding generation on ingest (background task)
- [ ] Semantic search endpoint
- [ ] AI field extraction on submission (category, sentiment, urgency via Claude)
- [ ] Similar request detection (suggest duplicates before submission)

### Phase 3 — Clustering & Insights
- [ ] Batch clustering job on stored embeddings
- [ ] AI-generated cluster labels and summaries
- [ ] Prioritization scoring formula
- [ ] Trending/insights endpoints

### Phase 4 — Reporting
- [ ] Report generation via Claude (structured output)
- [ ] Segment-specific and cross-segment reports
- [ ] Caching layer for generated reports

### Phase 5 — Polish & Scale Testing
- [ ] Seed data generator (hundreds of thousands of realistic BiteFlight requests)
- [ ] Performance benchmarks (search latency, clustering time, report generation time)
- [ ] Frontend (if in scope)

---

## Conventions & Constraints

- **Python 3.11+** with type hints throughout.
- **Async/await** for all I/O-bound operations.
- Use **Pydantic v2** for request/response schemas.
- Use **SQLAlchemy 2.0** async style for ORM.
- All AI calls must be **non-blocking** (async or background tasks).
- Environment variables for all secrets and config (API keys, DB connection strings).
- Keep AI prompts in dedicated files or constants, not inline in business logic.
- Tests use **pytest** with **pytest-asyncio**.
