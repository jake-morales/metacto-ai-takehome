# BiteFlight Feature Tracker

An AI-first feature request tracking system for BiteFlight. Customers (users, drivers, merchants) submit and vote on feature requests. Internal product teams cluster requests with AI, generate reports, and manage the roadmap.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- An [OpenAI API key](https://platform.openai.com/api-keys)

## Setup

1. **Copy the environment file and add your API key:**

   ```bash
   cp .env.example .env
   ```

   Open `.env` and set your OpenAI API key:

   ```
   OPENAI_API_KEY=sk-...
   ```

2. **Build and start all services:**

   ```bash
   docker-compose up --build
   ```

   This starts four services:
   - `db` — PostgreSQL 16 with pgvector
   - `redis` — Redis (background job queue)
   - `web` — Django app at [http://localhost:8000](http://localhost:8000)
   - `worker` — Huey background worker (embeddings, AI extraction)

3. **Run database migrations** (first time only, in a new terminal):

   ```bash
   docker-compose exec web python manage.py migrate
   ```

4. **Create a Django admin user** (optional):

   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

The app is now running at **http://localhost:8000**.

## Pages

### Customer-facing
| Page | URL | Description |
|---|---|---|
| Submit Request | `/submit/` | Submit a new feature request |
| Roadmap & Voting | `/roadmap/` | View the roadmap and vote on items |

### Internal Product Team
| Page | URL | Description |
|---|---|---|
| AI Reports & Chat | `/internal/reports/` | Generate AI reports, ask follow-up questions |
| Cluster Viewer | `/internal/clusters/` | View AI-grouped feature request themes |
| Edit Roadmap | `/internal/roadmap/` | Add and manage roadmap items |
| Goals & Mission | `/internal/goals/` | Set company goals used for AI reports |

Django admin is available at `/admin/`.

## Stopping the App

Stop all services (containers remain, data is preserved):

```bash
docker-compose stop
```

Stop and remove containers (data is preserved in the `pgdata` volume):

```bash
docker-compose down
```

Stop and remove everything including the database volume (⚠️ deletes all data):

```bash
docker-compose down -v
```

## Restarting

```bash
docker-compose up
```

No need to rebuild unless dependencies change. To rebuild after a `requirements.txt` change:

```bash
docker-compose up --build
```
