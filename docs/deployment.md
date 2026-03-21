# ScholarAI — Deployment & Development Guide

> Status: Legacy draft (not canonical).
> Canonical deployment and runtime guidance is maintained in docs/scholarai/13_qa_devops_and_risks.md and the root docker-compose.yml.
> This document may reference deferred infrastructure components.

---

## 1. Deployment Architecture

```
┌──────────┐     ┌──────────┐     ┌────────────┐
│ Frontend │────▶│ Backend  │────▶│ PostgreSQL │
│ (Vercel) │     │ (Docker) │     │ (pgvector) │
└──────────┘     └─────┬────┘     └────────────┘
                       │
              ┌────────┼──────────┐
              ▼        ▼          ▼
          ┌──────┐ ┌──────┐ ┌──────────┐
          │Redis │ │Neo4j │ │OpenSearch│
          └──────┘ └──────┘ └──────────┘
```

### Docker Compose (Development)

```yaml
version: "3.9"
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    env_file: .env
    depends_on: [postgres, redis, neo4j]

  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    env_file: .env

  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: scholarai
      POSTGRES_USER: scholarai
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes: ["pgdata:/var/lib/postgresql/data"]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  neo4j:
    image: neo4j:5
    environment:
      NEO4J_AUTH: neo4j/${NEO4J_PASSWORD}
    ports: ["7474:7474", "7687:7687"]

  opensearch:
    image: opensearchproject/opensearch:2.11.0
    environment:
      - discovery.type=single-node
      - DISABLE_SECURITY_PLUGIN=true
    ports: ["9200:9200", "9600:9600"]

  celery-worker:
    build: ./backend
    command: celery -A app.celery_app worker -l info
    depends_on: [redis, postgres]

  celery-beat:
    build: ./backend
    command: celery -A app.celery_app beat -l info
    depends_on: [redis]

volumes:
  pgdata:
```

---

## 2. GitHub Development Strategy

### Branch Strategy

| Branch | Purpose | Merges Into |
|---|---|---|
| `main` | Production-ready | — |
| `develop` | Integration | `main` (release PR) |
| `feature/*` | Individual features | `develop` |
| `bugfix/*` | Bug fixes | `develop` |
| `hotfix/*` | Production hotfixes | `main` + `develop` |

### Commit Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):
- `feat: add scholarship scraper`
- `fix: correct SHAP value calculation`
- `docs: update API documentation`
- `test: add recommendation engine tests`

### PR Workflow

1. Create `feature/xyz` from `develop`
2. Implement → commit → push
3. Open PR → CI runs (lint, test, type check)
4. Code review by ≥ 1 team member
5. Squash merge into `develop`
6. Release PR `develop` → `main` triggers deploy

## 3. Team Structure & Roles (3 Members)

| Role | Core Responsibilities |
|---|---|
| **Data/ML Lead** | Synthetic data generation, XGBoost/SHAP models, Python Playwright scrapers, LangChain prompts. |
| **Backend/Systems Lead** | FastAPI API design, PostgreSQL/Neo4j schemas, pgvector search, Docker orchestration, MLflow. |
| **Frontend/Product Lead** | Next.js architecture, Tailwind UI, dashboard charting, API integration, user flow. |

---

## 4. 16-Week Execution Plan

### Milestone 1: Foundation & Data (Weeks 1-4)
- **Week 1 (Setup)**: Initialize Mono-repo, Docker compose configs (PostgreSQL, Neo4j, Redis, OpenSearch).
- **Week 2 (Schemas)**: Implement SQLAlchemy ORM models and Cypher constraints. Setup Next.js boilerplate.
- **Week 3 (Scraper MVP)**: Playwright scrapers targeting Canada MS DS/AI programs + DAAD.
- **Week 4 (Ingestion)**: Pipeline pulling scraped JSON, generating Pydantic validations, and writing to Neo4j/Postgres. 

### Milestone 2: AI & Retrieval Systems (Weeks 5-8)
- **Week 5 (ML Models)**: Data/ML Lead generates 50k synthetic profiles and trains Stage 3 XGBoost admission model.
- **Week 6 (Explainability)**: Integrate SHAP TreeExplainer. Backend exposes `/api/v1/recommend` endpoint.
- **Week 7 (Stage 1 & 2)**: Complete Neo4j Graph queries (Stage 1 filter) and pgvector semantic search (Stage 2). 
- **Week 8 (Integration Point 1)**: The 3-stage recommendation pipeline returns end-to-end data via API.

### Milestone 3: Applied AI & Features (Weeks 9-12)
- **Week 9 (LangChain RAG)**: Build context retriever using PostgreSQL pgvector. Implement SOP critique agent (Claude).
- **Week 10 (Interview Sim)**: Implement Whisper STT pipeline and GPT-4o evaluation rubrics.
- **Week 11 (Dashboards)**: Frontend Lead completes Student Dashboard UI and match score visualizations.
- **Week 12 (Integration Point 2)**: Mentor and Admin role features connected to API. 

### Milestone 4: Polish, Test & Defense (Weeks 13-16)
- **Week 13 (Testing Phase)**: Pytest coverage for AI endpoints. Cypress E2E tests for Frontend UI flows.
- **Week 14 (Optimization)**: Fix OpenSearch indexing bugs. Latency tuning for LangChain calls (Redis caching).
- **Week 15 (Code Freeze)**: Repository lockdown. Final deployment rehearsal on local Docker swarms.
- **Week 16 (Documentation)**: Final technical design document polishing and academic defense prep.
