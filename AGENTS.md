# AGENTS.md — AI-First Feature Request Tracker (BiteFlight PoC)

## Project Rules

### Prompt Logging

Every time you receive a new instruction or prompt, append it to prompts.txt in the project root with a timestamp (ISO 8601) and a brief summary of what you did in response. Create the file if it doesn't exist. Keep this log updated throughout all sessions.

---

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

### 1. Submit a Feature Request (Page 1 — Customer)
- Customers submit free-text feature requests via a form.
- Each request captures: submitter name (optional), customer segment, title, description, timestamp.
- AI processing on ingest (Huey background task): extract structured fields (category, tags, sentiment, urgency) via GPT-4o-mini and generate an embedding via text-embedding-3-large.

### 2. Product Roadmap & Voting (Page 2 — Customer)
- Customers view a **curated roadmap** of RoadmapItems grouped by status (Shipped, In Progress, Planned).
- Displayed as a vertical timeline with quarter labels and target dates.
- Vote button (HTMX POST, updates count without page reload).
- Session-based voting: one vote per RoadmapItem per browser session.
- Customers vote on **RoadmapItems only** (curated by product team), not raw FeatureRequests.

### 3. Internal Roadmap Editor (Page 3 — Internal)
- Create, edit, reorder, and delete RoadmapItems.
- Set status, target date, and link feature requests.

### 4. Company Goals & Mission (Page 4 — Internal)
- Singleton model for mission statement and goals.
- These feed into AI report generation as context.

### 5. AI Reports & Chat (Page 5 — Internal)
- Chat interface with SSE streaming (StreamingHttpResponse + EventSource JS).
- Pre-loaded prompt with company goals, cluster summaries, and aggregate stats.
- Follow-up questions use RAG: embed user question, pgvector cosine similarity for top 20 matching requests, inject as context.
- Markdown rendering for AI responses.
- Session history saved and reloadable.

### 6. Cluster Viewer (Page 6 — Internal)
- Trigger HDBSCAN clustering over stored embeddings.
- AI-generated cluster labels and summaries (GPT-4o-mini).
- Grid of clusters with request count, avg sentiment, total votes.
- Click cluster to see sample feature requests.

---

## Technical Architecture

### Stack

| Layer              | Technology                  | Rationale                                                    |
|--------------------|-----------------------------|--------------------------------------------------------------|
| **Backend**        | Django 5.1                  | Backend + frontend in one, mature ORM, admin                 |
| **Database**       | PostgreSQL 16 + pgvector    | Relational data + vector similarity search in one store      |
| **AI Models**      | OpenAI (text-embedding-3-large, gpt-4o-mini, gpt-6-sol) | Embeddings, extraction, report generation |
| **Task Queue**     | django-huey + Redis         | Lightweight background jobs for AI processing on ingest      |
| **Frontend**       | Django templates + HTMX     | Server-rendered HTML with partial updates, no JS framework   |
| **Styling**        | Tailwind CSS (CDN)          | Fast prototyping, no build tooling                           |
| **Containers**     | Docker Compose              | PostgreSQL+pgvector, Redis, Django, Huey worker              |

### Data Models

```
FeatureRequest
  id: UUID
  title: str
  description: text
  submitter_name: str (optional, no auth)
  segment: enum(user, driver, merchant)
  status: enum(new, under_review, planned, in_progress, shipped, declined)
  category: str (AI-assigned)
  tags: JSONField (AI-assigned)
  sentiment: float (AI-assigned, -1 to 1)
  urgency: float (AI-assigned, 0 to 1)
  embedding: vector(1536) — text-embedding-3-large truncated to 1536 dims
  created_at, updated_at: timestamps

Vote
  id: UUID
  roadmap_item: FK -> RoadmapItem
  session_key: str (Django session key, no auth)
  unique_together: (roadmap_item, session_key)

RoadmapItem
  id: UUID
  title: str
  description: text
  status: enum(planned, in_progress, shipped)
  target_date: date (optional)
  order: int
  vote_count: int (denormalized)
  linked_requests: M2M -> FeatureRequest
  quarter_label: computed property (e.g. "Q1 2027")

CompanyGoals (singleton, pk=1)
  mission: text
  goals: text
  updated_at: timestamp

ChatSession
  id: UUID
  title: str
  system_prompt: text (snapshot of goals + context)

ChatMessage
  id: UUID
  session: FK -> ChatSession
  role: enum(system, user, assistant)
  content: text

ClusteringRun
  id: UUID
  status: str (pending, running, completed, failed)
  num_clusters, num_requests_processed: int

Cluster
  id: UUID
  run: FK -> ClusteringRun
  label: str (AI-generated)
  summary: text (AI-generated)
  theme: str
  request_count: int
  avg_sentiment: float
  total_votes: int

ClusterMembership
  cluster: FK -> Cluster
  request: FK -> FeatureRequest
  similarity_score: float
```

### Key Design Decisions

1. **Embeddings at ingest**: compute and store embeddings when a request is created (Huey background task) so search and clustering read pre-computed vectors.
2. **pgvector for similarity**: avoids a separate vector DB dependency; PostgreSQL handles both relational queries and ANN search. HNSW index for fast retrieval (limited to 2000 dims, so embeddings truncated to 1536).
3. **Pre-computed clusters**: run clustering on-demand rather than on every query. Store cluster assignments so reports pull from materialized results.
4. **SSE for chat streaming**: Django StreamingHttpResponse with text/event-stream content type; OpenAI stream=True forwards chunks as SSE events. Frontend uses EventSource.
5. **Session-based voting**: no authentication required; uses Django session keys for vote deduplication.
6. **Two visual themes**: Customer pages use orange/amber with top navbar; Internal pages use indigo/slate with sidebar navigation.

---

## Project Structure

```
metacto-ai-takehome/
├── manage.py
├── biteflight/                  # Django project config
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── core/                        # Shared: base templates, pgvector migration
│   ├── migrations/
│   │   └── 0001_enable_pgvector.py
│   └── templatetags/
│       └── markdown_extras.py
├── features/                    # Feature requests + voting
│   ├── models.py                # FeatureRequest, Vote
│   ├── forms.py                 # FeatureRequestForm
│   ├── views.py                 # Submit, roadmap, vote
│   ├── tasks.py                 # Huey: embedding + extraction
│   └── urls.py
├── roadmap/                     # Internal roadmap management
│   ├── models.py                # RoadmapItem
│   ├── forms.py
│   ├── views.py
│   └── urls.py
├── goals/                       # Company goals (singleton)
│   ├── models.py                # CompanyGoals
│   ├── forms.py
│   ├── views.py
│   └── urls.py
├── reports/                     # AI reports & chat
│   ├── models.py                # ChatSession, ChatMessage
│   ├── views.py                 # Chat + SSE streaming
│   └── urls.py
├── clusters/                    # Clustering & viewer
│   ├── models.py                # ClusteringRun, Cluster, ClusterMembership
│   ├── views.py
│   ├── tasks.py                 # Huey: run clustering
│   └── urls.py
├── ai_services/                 # Pure Python module (not a Django app)
│   ├── client.py                # OpenAI client singleton
│   ├── embeddings.py            # Generate & search embeddings
│   ├── extraction.py            # Extract category/sentiment/urgency
│   ├── clustering.py            # HDBSCAN clustering
│   ├── reports.py               # RAG context assembly + streaming
│   └── prompts.py               # All prompt templates
├── templates/
│   ├── core/
│   │   ├── base.html            # Root (loads Tailwind CDN, HTMX)
│   │   ├── base_customer.html   # Orange/amber, top navbar
│   │   └── base_internal.html   # Indigo/slate, sidebar
│   ├── features/
│   │   ├── submit.html          # Page 1
│   │   ├── roadmap.html         # Page 2 (timeline)
│   │   └── partials/
│   │       └── vote_button.html
│   ├── roadmap/
│   │   ├── edit.html            # Page 3
│   │   └── partials/
│   ├── goals/
│   │   └── edit.html            # Page 4
│   ├── reports/
│   │   ├── chat.html            # Page 5
│   │   └── partials/
│   └── clusters/
│       ├── list.html            # Page 6
│       ├── detail.html
│       └── partials/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env
├── AGENTS.md
├── CLAUDE.md
└── README.md
```

---

## AI Integration Points

| Operation                  | Model                              | When it runs              |
|----------------------------|------------------------------------|---------------------------|
| Extract structured fields  | OpenAI gpt-4o-mini                 | On request submission (Huey task) |
| Generate embedding         | OpenAI text-embedding-3-large (1536 dims) | On request submission (Huey task) |
| Find similar requests      | pgvector cosine similarity search  | On search / RAG context   |
| Cluster requests           | HDBSCAN on embeddings              | Manual trigger from UI    |
| Generate cluster labels    | OpenAI gpt-4o-mini                 | After clustering          |
| Report generation / chat   | OpenAI gpt-6-sol (streamed SSE)    | On-demand in chat         |

---

## URL Routing

```
/                           → Redirect to /submit/
/submit/                    → Page 1: Submit feature request
/roadmap/                   → Page 2: Customer roadmap + voting
/internal/roadmap/          → Page 3: Internal roadmap editor
/internal/goals/            → Page 4: Company goals editor
/internal/reports/          → Page 5: AI reports & chat
/internal/clusters/         → Page 6: Cluster viewer
/admin/                     → Django admin
```

---

## Docker Compose Services

| Service  | Image                    | Port  |
|----------|--------------------------|-------|
| db       | pgvector/pgvector:pg16   | 5432  |
| redis    | redis:7-alpine           | 6379  |
| web      | Custom (Dockerfile)      | 8000  |
| worker   | Custom (Huey consumer)   | —     |

---

## Conventions & Constraints

- **Django 5.1** with Python 3.11+.
- **No authentication** — this is a demo/PoC.
- Environment variables for all secrets and config (`.env` file).
- AI prompts stored in `ai_services/prompts.py`, not inline.
- All AI calls are **non-blocking** (Huey background tasks or SSE streaming).
- Tailwind CSS via CDN — no build step.
- HTMX for interactive updates without full page reloads.
