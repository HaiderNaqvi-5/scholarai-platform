# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository

ScholarAI — modular monolith for AI-assisted scholarship discovery, eligibility-aware ranking, document feedback, and interview practice. FYP scope: 3 devs, 16 weeks, limited budget. Scope is **Canada-first MS-only (DS/AI/Analytics) plus Fulbright** — enforced in discovery and recommendation flow.

**Source-of-truth hierarchy:**
- Repo governance: `.codex/AGENTS.md` (mission + architecture defaults)
- Agent workflow: `AGENTS.md` (commands + push gate)
- Live implementation status: `docs/scholarai/IMPLEMENTATION_STATUS_REPORT.md`
- Canonical product/architecture docs: `docs/scholarai/01..14*.md`
- Acceptance gates: `docs/scholarai/v0_1_slc_acceptance_checklist.md`
- Legacy `docs/*.md` are transitional — do not treat as current.

## Common commands

### Backend (`backend/`, Python 3.12 recommended)
- Install: `python -m pip install -r backend/requirements.txt`
- Bootstrap DB + seed demo: `cd backend && python scripts/bootstrap_local.py` (Alembic upgrade head w/ retries; seeds demo if `AUTO_SEED_DEMO_DATA=true`)
- Run API: `cd backend && python -m uvicorn app.main:app --reload`
- Celery worker: `celery -A app.tasks.celery_app:celery_app worker -l info`
- Celery beat: `celery -A app.tasks.celery_app:celery_app beat -l info`
- Tests: `pytest backend/tests/unit backend/tests/integration -q`
- Single test: `pytest backend/tests/unit/path/to/test_file.py::test_name -q`
- Compile sanity: `python -m compileall backend/app backend/tests`
- Migrations: `alembic upgrade head` / `alembic revision --autogenerate -m "msg"` (run from `backend/`)
- API rehearsal: `cd backend && python scripts/rehearse_seeded_demo.py`

### Frontend (`frontend/`, Node 20)
- Install: `cd frontend && npm ci`
- Dev: `npm run dev` — http://localhost:3000
- Build: `npm run build`
- Start prod: `npm run start -- --hostname 0.0.0.0 --port 3000`
- Lint: `npm run lint`
- Typecheck: `npm run typecheck` (`tsc --noEmit`)

### Full stack
- `docker compose up --build` then UI at `http://localhost:3000`, API at `http://localhost:8000/health`, Swagger at `http://localhost:8000/docs`.
- After adding/renaming Next.js routes while dev server is running, restart it — stale process serves false 404s.

### Browser smoke (matches CI)
- Install browser once: `python -m playwright install chromium`
- Full suite: `python tests/e2e/playwright/run_smoke_suite.py`
- Demo rehearsal: `python tests/e2e/playwright/rehearse_seeded_demo.py`
- Direct entrypoints: `public_scholarship_browse_smoke.py`, `auth_dashboard_smoke.py`, `seeded_recommendations_smoke.py`, `document_feedback_smoke.py`, `interview_practice_smoke.py`, `curation_smoke.py`

### Docs governance
- `python scripts/docs_governance_check.py` (CI gate).

### Push gate (per `AGENTS.md`)
Before any push to GitHub, run all of: backend unit/integration, KPI regression, frontend lint/typecheck/build, docs governance, browser smoke. Push only after all pass.

### Demo accounts (seeded locally)
- student: `student@example.com` / `strongpass1`
- admin: `admin@example.com` / `strongpass1`

## Architecture

### Stack
- **Frontend:** Next.js 16 + React 19 + TypeScript + Tailwind 4. Standalone output. Path alias `@/* → src/*`.
- **Backend:** FastAPI modular monolith (`backend/app/`), SQLAlchemy 2 async, Pydantic v2, Alembic, Celery + Redis, pgvector on PostgreSQL 16. Neo4j is provisioned but the Knowledge-Graph Layer is currently a *logical* relational abstraction (per `docs/scholarai/05_system_architecture.md`).
- **Search:** pgvector embeddings on `ScholarshipChunk`; default embedding model `sentence-transformers/all-MiniLM-L6-v2`.
- **Async:** Celery worker + beat. Beat schedule (`backend/app/tasks/celery_app.py`):
  - `nightly-scholarship-ingestion` @ 02:00 UTC
  - `kpi-snapshot-retention-cleanup` (when `KPI_SNAPSHOT_RETENTION_ENABLED=true`)
  - Task includes: `recommendation_tasks`, `scraper_tasks`, `kpi_tasks`.
- **Deploy:** Docker Compose. CI: `.github/workflows/ci.yml` with `backend-sanity`, `kpi-regression`, `frontend-sanity`, `docs-governance`, `browser-smoke` jobs.

### Backend layout (`backend/app/`)
- `main.py` — `create_app()` factory. Mounts `api_v1_router` at `/api/v1`. Lifespan calls `seed_demo_data_if_enabled()`. Global handlers map `ScholarAIException`, validation, SQLAlchemy, and unhandled errors to a uniform `ErrorEnvelope` (`code`, `message`, `request_id`, `status`). X-Request-ID middleware wraps every request.
- `api/v1/__init__.py` — wires the active router set:
  `health`, `auth`, `profile` (+ `profiles` alias), `scholarships`, `saved-opportunities`, `recommendations`, `documents`, `interviews`, `curation`, `mentor` (+ `mentors` alias), `analytics`, `access-control`. `app/api/v2/` exists but is empty — do not assume v2 contracts.
- `services/<domain>/` — one folder per domain (`auth`, `students`, `recommendations`, `documents`, `interview`, `curation`, `ingestion`, `saved_opportunities`, `access_control`). Pattern in `recommendations/`: `service.py` orchestration + helpers `hybrid_retriever.py`, `eligibility.py`, `evaluation.py`, `benchmark_registry.py`. **No formal repository pattern** — services use `AsyncSession` injected via DI from `app/core/dependencies.py` and return Pydantic schemas, never raw ORM models.
- `models/models.py` — single-file ORM. Enums encode the curation state machine: `RecordState ∈ {raw, validated, published, archived}`, `IngestionRunStatus`, `DocumentProcessingStatus`, `InterviewSessionStatus`. `Scholarship` carries provenance (`record_state`, `imported_at`, `provenance_payload`, `source_last_seen_at`, validate/publish/reject audit columns).
- `core/config.py` — Pydantic `Settings` (env-driven). `validate_production_settings()` rejects default `SECRET_KEY`/`NEO4J_PASSWORD`/`DATABASE_URL` when `ENVIRONMENT=production`.
- `tasks/` — Celery app + `recommendation_tasks`, `scraper_tasks`, `kpi_tasks`, `graph_sync_tasks`.
- `backend/legacy/` — quarantined; do not import. `ai_services/` and `setup/` flagged for archive.

### Frontend layout (`frontend/src/`)
- `app/<route>/` — App Router pages: `scholarships` (public), `recommendations`, `dashboard`, `document-feedback`, `interview`, `curation`, `mentor`, `admin`, `owner`, `onboarding`, `profile`, `login`, `signup`. Root `layout.tsx` wraps in `AuthProvider`.
- `lib/api.ts` — single fetch wrapper with Bearer-token injection, `cache: "no-store"`, normalized error parsing. Base URL from `NEXT_PUBLIC_API_BASE_URL` (default `http://localhost:8000/api/v1`).
- `components/auth/auth-provider.tsx` — Context auth. Tokens in `localStorage` (`scholarai.access_token`, `scholarai.refresh_token`, `scholarai.access_token_expires_at`); refresh fires 60s before expiry; cross-tab sync via `storage` event; 401 triggers refresh-and-retry.
- `lib/routes.ts` — role priority routing (student → `/dashboard`, admin → `/curation`, owner → `/owner`, mentor → `/mentor`).
- `lib/types.ts` — frontend type contracts. **No** generated SDK; backend Pydantic schemas are authoritative — types kept in sync by hand (`shared/contracts/README.md`).

### Module boundaries
| Module | Routes | Owns | Must not own |
|--------|--------|------|--------------|
| `auth` | `/auth/*` | JWT tokens, role checks, session lifecycle | Scholarship data |
| `students` | `/profile` | Profile CRUD | Recommendations |
| `scholarships` | `/scholarships/*` | Discovery, detail, publication workflow | Document feedback |
| `recommendations` | `/recommendations` | Eligibility → retrieval → rerank → explanation | Curation writes |
| `documents` | `/documents/*` | Upload lifecycle, grounded feedback | Scholarship truth |
| `interviews` | `/interviews/*` | Practice sessions, rubric outputs | Student scoring logic |
| `curation` | `/curation/*` | raw → validated → published, ingestion review | Recommendation ranking |
| `access_control` | `/access-control/*` | Owner role mgmt + audited reverts | Domain data |

### Recommendation pipeline
Stages from `docs/scholarai/08_recommendation_and_ml.md`:
0. Scope filter (published, MS, DS/AI/Analytics, Canada+Fulbright)
1. KG eligibility filter (citizenship/GPA/language/field/degree)
2. pgvector similarity rerank
3. ML rerank — **Estimated Scholarship Fit Score**, not acceptance prediction
4. Explanation generation

**Current runtime: Phase 1 active.** Stages 0–2 wired (relational eligibility graph + pgvector retrieval). Stage 3 uses calibrated heuristic rerank with guardrail floor/cap + policy version, plus rules-only fallback parity. Benchmark dataset registry + `GET /api/v1/recommendations/benchmarks` and `POST /api/v1/recommendations/benchmarks/{dataset_id}/evaluate`. KPI snapshot recording + MRR@K instrumentation live. **Never present scores as causal/acceptance probabilities.**

### Curation state machine
`Source registry → fetch → parse → schema validate → normalize → dedupe → review queue → curator decision → published`. States `raw → validated → published` enforced in DB and curation routes. Public `/scholarships` returns **published only**. Dedup keys: `source_record_hash`, `source_url`, `(normalized title, provider, deadline)`.

### RBAC
Six-role bundle: `ENDUSER_STUDENT`, `INTERNAL_USER`, `DEV`, `ADMIN`, `UNIVERSITY`, `OWNER`. Capability-based authorization matrix; institution-scoped university access; compatibility-window migration from legacy role claims to capability claims. Owner governance via `/api/v1/access-control/*` (managed-user listing, role updates, audited role reverts).

## Backend conventions

### Service layer
```python
class <Domain>Service:
    def __init__(self, db: AsyncSession): self.db = db
    async def method(self, payload: SchemaIn) -> SchemaOut: ...
```
- Always `await` SQLAlchemy calls; never mix sync + async.
- Domain errors raise `ScholarAIException` with `ErrorCode` enum + status code (no generic `Exception`).
- Services return Pydantic schemas, never ORM models.

### API routes
- One `APIRouter` per domain in `backend/app/api/v1/routes/<domain>.py`.
- Dependencies injected via `Depends()`.
- List endpoints normalize to `{ items: [...], total: int }`.
- Errors flow through the global `ErrorEnvelope` handler.

### Schemas
- Request/response in `backend/app/schemas/`.
- Pydantic `BaseModel` with `Field(..., description=...)` for OpenAPI.
- Domain enums in `backend/app/models/models.py`.

## Phase 2 API surface (Canada-first fixed)
- `POST /api/v1/documents` — accepts optional scholarship grounding identifiers.
- `POST /api/v1/documents/{id}/feedback` — returns explicit grounded-context partitions: validated scholarship facts, retrieved writing guidance, generated guidance, limitations.
- `POST /api/v1/interviews` — accepts `practice_mode` + optional `scholarship_id`.
- `GET /api/v1/interviews/{id}` — returns session history + rubric trend summary used by adaptive follow-up.
- Invalid grounding identifiers fail cleanly with structured errors.

## Implementation status (live — see `IMPLEMENTATION_STATUS_REPORT.md` for evidence links)

### Done
- FastAPI modular monolith + Alembic migration-driven bootstrap + seeded demo dataset + rehearsal scripts.
- CI sanity + KPI regression + browser-smoke gates.
- Auth: register/login/me/refresh; access-token + refresh; frontend session persistence; protected/admin/owner route guards.
- Public scholarship browse/search/filters/detail; profile save+load; functional onboarding.
- Recommendation API + stage-aware explanation; pgvector retrieval; calibrated heuristic rerank; rules-only fallback parity; benchmark registry + evaluate endpoints; KPI snapshots; MRR@K.
- Saved opportunities + tracker status transitions (saved/in-progress/applied/closed) on dashboard.
- Document submission + scholarship-grounded bounded feedback with explicit grounded-context partitions.
- Interview mode-aware sessions, adaptive weakest-dimension follow-up, structured rubric, history/trend summary, deterministic action-plan items.
- Curation: raw/validated/published handling; review/edit/approve/reject/publish/unpublish; audit-log foundation.
- Ingestion: source-registry runs, capture path, parsing, raw-record creation, retry API/UI, diagnostics filtering, queue assignment, bulk retry, captured HTML snapshot management.
- Role homes (student/admin/owner/mentor/test-user) all complete in v0.1 acceptance checklist.
- Acceptance: SLC-CORE-004/005, SLC-ROLE-001..005, SLC-OPS-003, SLC-TRUST-001..003, SLC-UI-001..003 marked Complete.

### Remaining
- Recommendation: continuous online drift monitoring; ongoing calibration ops + alerting loops.
- Grounding depth: expand bounded guidance library; raise citation density across broader scholarship coverage.
- Long-horizon coaching: richer multi-session interview plans; voice path; AI-generated longitudinal intervention automation.
- Ingestion coverage: parser coverage still heuristic and narrow; deeper parser resilience; broader provider expansion (DAAD deferred).
- API contracts: detail responses, pagination metadata, route naming still diverge from `10_backend_api_and_repo.md` (e.g. `profile` vs docs label `profiles`).
- Async orchestration for larger document-feedback jobs.
- DevOps: release management, rollback drills, production-like hardening.
- Open SLC IDs without execution evidence yet: SLC-CORE-001/002/003, SLC-OPS-001/002.
- `shared/` and `infra/` remain documentation scaffolding only.
- Deferred: broad geography, marketplace/mentor commerce, partner APIs, institution analytics, tenant partitioning, graph experimentation, ML reranking ablations, larger judged-set evaluation tooling.

### Next 3 priorities (per status report)
1. Expand grounding depth + citation density across broader scholarship coverage.
2. Expand recommendation benchmark dataset coverage; calibrate rerank weights with judged samples.
3. Strengthen ingestion coverage (richer parsers + captured HTML snapshot management).

## Critical rules
- Structured validated data is authoritative for eligibility, deadlines, funding rules. RAG is advisory; never the authority for scholarship rules.
- Public `/scholarships` returns **published only**.
- Eligibility = relational queries through the Knowledge-Graph Layer, not AI guesses.
- Do not import from `backend/legacy/`, `ai_services/`, `setup/`.
- Backend Pydantic schemas are the authoritative API contract; `frontend/src/lib/types.ts` is hand-synced.
- New feature = new service module inside the FastAPI app, not a new deployable.
- Use pgvector for MVP; do not introduce a separate search engine without justification.
- When updating runtime behavior, update `docs/scholarai/IMPLEMENTATION_STATUS_REPORT.md` in the same PR.
