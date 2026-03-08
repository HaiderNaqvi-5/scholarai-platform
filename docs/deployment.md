# ScholarAI — Deployment & Development Guide

---

## 1. Deployment Architecture

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│ Frontend │────▶│ Backend  │────▶│ Database │
│ (Vercel) │     │ (Docker) │     │(Supabase)│
└──────────┘     └─────┬────┘     └──────────┘
                       │
              ┌────────┼────────┐
              ▼        ▼        ▼
          ┌──────┐ ┌──────┐ ┌───────┐
          │Redis │ │Neo4j │ │MinIO  │
          │      │ │      │ │       │
          └──────┘ └──────┘ └───────┘
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

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    ports: ["9000:9000", "9001:9001"]

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

---

## 3. Implementation Timeline

### 6-Month Plan (Recommended)

| Month | Phase | Key Deliverables |
|---|---|---|
| **1** | Research & Design | Literature review, architecture design, DB schema, API design |
| **2** | Backend Foundation | FastAPI scaffold, auth, DB models, CRUD APIs, Docker |
| **3** | Data + AI Core | Scrapers (3+ sources), LLM extraction, recommendation engine, SHAP |
| **4** | Advanced AI | Interview simulator, SOP assistant, knowledge graph |
| **5** | Blockchain + Frontend | Smart contracts, dashboards, mentorship UI |
| **6** | Testing + Research | E2E testing, user study, model evaluation, paper draft |

### 4-Month Accelerated

| Month | Phase | Deliverables |
|---|---|---|
| **1** | Foundation | DB schema, FastAPI + Next.js scaffold, auth, CRUD |
| **2** | Core AI + Scraping | Scrapers, LLM pipeline, recommendation engine, SHAP |
| **3** | Advanced Features | Interview sim, SOP assistant, blockchain PoC, Neo4j graph |
| **4** | Integration + Polish | Dashboards, analytics, testing, docs, paper draft |

---

## 4. Team Role Distribution

| Role | Responsibilities |
|---|---|
| **AI/ML Engineer** | Recommendation engine, SHAP/LIME, interview simulator, SOP assistant, MLflow |
| **Backend Engineer** | FastAPI, database, auth, Celery, Redis, API development |
| **Data Engineer** | Scrapers, data pipeline, Neo4j knowledge graph, LLM extraction |
| **Blockchain/Frontend** | Solidity contracts, Next.js dashboards, WebRTC, UI/UX |

> [!NOTE]
> **Solo FYP priority order:** (1) Recommendation + XAI, (2) Scraper, (3) Student dashboard, (4) Interview sim. Blockchain/KG → proof-of-concept only.

---

## 5. Risks and Mitigation

| Risk | Severity | Probability | Mitigation |
|---|---|---|---|
| **Data scarcity** | High | High | Synthetic data, documented limitations |
| **Scraper fragility** | Medium | High | LLM extraction, monitoring alerts |
| **Model bias** | High | Medium | SHAP auditing, fairness constraints |
| **Blockchain gas costs** | Low | Low | Polygon L2 ($0.01–0.05/tx) |
| **LLM cost escalation** | Medium | Medium | Response caching, smaller models |
| **Whisper accent issues** | Medium | Medium | Document limitation, fine-tuning |
| **Scope creep** | High | High | Phased delivery, MVP scope defined |
| **KG cold start** | Medium | High | Seed with scraped scholarship data |

---

## 6. Security Architecture

### Authentication & Authorization

| Layer | Implementation |
|---|---|
| AuthN | JWT (access + refresh), bcrypt password hashing |
| AuthZ | Role-based middleware: student / mentor / admin / university |
| Rate Limiting | Redis sliding window: 100 req/min (auth), 20 (anon) |
| Input Validation | Pydantic schemas on all endpoints |

### Data Security

| Concern | Mitigation |
|---|---|
| SQL injection | SQLAlchemy ORM (parameterized queries) |
| XSS | Next.js auto-escape + CSP headers |
| File uploads | MIME validation, 10MB limit, virus scan (ClamAV) |
| Credentials | AES-256 encryption at rest, presigned URLs (1h expiry) |
| API keys | Environment variables only, never in Git |
| Blockchain keys | Hardware-backed secret manager |

### RBAC Matrix

| Endpoint Group | Student | Mentor | Admin | University |
|---|---|---|---|---|
| Profile management | ✅ Own | ✅ Own | ✅ All | ✅ Own |
| Scholarship matching | ✅ | ❌ | ✅ | ❌ |
| Interview simulator | ✅ | ❌ | ✅ | ❌ |
| Credential upload | ✅ | ❌ | ✅ | ❌ |
| Credential verify | ❌ | ❌ | ✅ | ✅ |
| Mentorship | ✅ Request | ✅ Conduct | ✅ Manage | ❌ |
| Admin panel | ❌ | ❌ | ✅ | ❌ |

---

## 7. Research Paper Potential

### Proposed Title

> **"ScholarAI: Explainable Knowledge-Graph-Augmented Scholarship Recommendation with Blockchain Credential Verification"**

### Key Research Questions

1. **RQ1:** Does KG augmentation improve recommendation quality over flat models?  
   → Compare XGBoost alone vs. XGBoost + Neo4j → report P@K, NDCG

2. **RQ2:** Do SHAP explanations improve user trust?  
   → A/B user study: with vs. without explanations → Likert scale

3. **RQ3:** How stable are SHAP explanations across retraining?  
   → 10 retraining runs → report consistency ratio

### Target Venues

| Venue | Type | Fit |
|---|---|---|
| ACM RecSys | Conference | Recommendation + explainability |
| AAAI / IJCAI | Conference | AI in education |
| IEEE Access | Journal | Open-access system papers |
| Expert Systems with Applications | Journal | Applied AI |
| Education and Information Technologies | Journal | EdTech + AI |

### Ethical Considerations

- Bias auditing across demographic groups
- Open-source codebase for transparency
- GDPR-like data handling principles
- AI scores are advisory, not authoritative
