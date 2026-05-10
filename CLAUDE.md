# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository

ScholarAI — modular monolith for AI-assisted scholarship discovery, eligibility-aware ranking, document feedback, and interview practice. FYP scope: 3 devs, 16 weeks, limited budget. Scope is **Canada-first MS-only (DS/AI/Analytics) plus Fulbright** — enforced in discovery and recommendation flow.

The user-facing brand of the new frontend is **GrantPath**. Backend, repo, and internal docs continue to use **ScholarAI**.

**Source-of-truth hierarchy:**
- Repo governance: `.codex/AGENTS.md` (mission + architecture defaults)
- Agent workflow: `AGENTS.md` (commands + push gate)
- Live implementation status: `docs/scholarai/IMPLEMENTATION_STATUS_REPORT.md`
- Canonical product/architecture docs: `docs/scholarai/01..14*.md`
- Acceptance gates: `docs/scholarai/v0_1_slc_acceptance_checklist.md`
- Frontend plan + sprints: `frontend/README.md` (S1 done; S2–S10 listed)
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

### Frontend (`frontend/`, Node 20+ or Bun)
The greenfield rebuild on `feat/frontend-greenfield` uses **Bun** as the canonical package manager and runtime. `npm` still works for any team member without Bun installed.

Bun (preferred):
- Install: `cd frontend && bun install`
- Dev: `bun dev` — http://localhost:3000
- Build: `bun run build`
- Start prod: `bun run start --hostname 0.0.0.0 --port 3000`
- Lint: `bun run lint`
- Typecheck: `bunx --bun tsc --noEmit`

npm fallback:
- `cd frontend && npm install && npm run dev` (also `build`, `lint`).

### Full stack
- `docker compose up --build` then UI at `http://localhost:3000`, API at `http://localhost:8000/health`, Swagger at `http://localhost:8000/docs`.
- After adding/renaming Next.js routes while dev server is running, restart it — stale process serves false 404s.

### Browser smoke (matches CI)
- Install browser once: `python -m playwright install chromium`
- Full suite: `python tests/e2e/playwright/run_smoke_suite.py`
- Demo rehearsal: `python tests/e2e/playwright/rehearse_seeded_demo.py`
- Direct entrypoints: `public_scholarship_browse_smoke.py`, `auth_dashboard_smoke.py`, `seeded_recommendations_smoke.py`, `document_feedback_smoke.py`, `interview_practice_smoke.py`, `curation_smoke.py`

> NOTE: existing browser-smoke selectors target the *previous* frontend layout. They will be re-pointed at the greenfield routes during sprint S10 (polish + E2E). Until then, expect smoke failures on the greenfield branch and skip the gate locally.

### Docs governance
- `python scripts/docs_governance_check.py` (CI gate).

### Push gate (per `AGENTS.md`)
Before any push to GitHub, run all of: backend unit/integration, KPI regression, frontend lint/typecheck/build, docs governance, browser smoke. Push only after all pass. (Browser-smoke gate temporarily relaxed on `feat/frontend-greenfield` until S10.)

### Demo accounts (seeded locally)
- student: `student@example.com` / `strongpass1`
- admin: `admin@example.com` / `strongpass1`

## Architecture

### Stack
- **Frontend:** Next.js 16 + React 19 + TypeScript + Tailwind 4. Path alias `@/* → src/*`. shadcn-style primitives over Radix; Lucide icons; Sora display + IBM Plex Sans body + IBM Plex Mono data fonts via `next/font`. The pre-greenfield frontend (single `lib/api.ts`, per-route admin/owner/mentor pages, GrantPath AI brand metadata) was wiped in `feat/frontend-greenfield`.
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

### Frontend layout (`frontend/src/`, S1 greenfield)

```
app/
  layout.tsx                  fonts, providers
  globals.css                 Tailwind 4 @theme tokens
  page.tsx                    marketing landing (logged-out)
  login/                      auth (Suspense-wrapped useSearchParams)
  signup/
  onboarding/                 4-step wizard, localStorage draft autosave
  (student)/                  role-guarded student shell
    feed/                     POST /recommendations live
    discover/                 placeholder → S3
    scholarships/[id]/        placeholder → S3
    saved/                    placeholder → S3 (kanban)
    documents/, documents/new, documents/[id]
    interviews/, interviews/[id]
    profile/, settings/
  (mentor)/                   role-guarded mentor shell
    mentor/queue/             placeholder → S7
    mentor/documents/[id]/
  (admin)/                    role-guarded admin shell
    admin/, admin/ingestion(/[id]), admin/curation(/[id])
    admin/users/, admin/audit/, admin/rec-eval/
components/
  ui/                         Button, Input, Label, Card, Badge, Skeleton
  shell/                      AppShell, Sidebar, TopBar, PlaceholderRoute
lib/
  api/
    client.ts                 fetch wrapper + bearer + silent refresh + 401 retry
    types.ts                  hand-synced backend Pydantic shapes
    endpoints/                auth, profile, scholarships, recommendations,
                              saved, documents, interviews, curation, mentors,
                              access-control, analytics
    index.ts                  barrel re-export (`endpoints.<domain>.<method>`)
  auth/
    AuthProvider.tsx          context, login/signup/logout/refreshUser
    RoleGuard.tsx             hasRole(), ROLE_GROUPS = {student,mentor,admin,owner}
  theme/tokens.ts             colour, spacing, radii, shadows, fonts
  utils.ts                    cn(), formatDeadline(), formatAmount()
```

- **localStorage tokens** under `grantpath.access_token` / `grantpath.refresh_token` / `grantpath.access_expires_at` (was `scholarai.*`).
- **API base URL** from `NEXT_PUBLIC_API_BASE_URL` (default `http://localhost:8000/api/v1`).
- **No generated SDK.** Backend Pydantic schemas remain the authoritative API contract; `frontend/src/lib/api/types.ts` is hand-synced and replaces the previous `frontend/src/lib/types.ts`.

### Frontend UX rules (hard constraints; reviewer rejects PRs that violate)

1. **Validated facts visually distinct from AI-generated content.** Validated → `validated.500` left border + "Verified" badge + source link. AI-generated → `generated.500` left border + Sparkles (Lucide) icon + 1-line provenance. Never mix in a single paragraph.
2. **No emoji as UI.** Lucide SVG icons only.
3. **No streaming-text theatre on REST data.** Recommendations and scholarship payloads render once.
4. **Skeleton once per route load.** No spinner-on-every-card. List re-fetches update in place.
5. **Optimistic mutations** on save toggle, kanban status change, profile edit. Rollback toast on failure.
6. **`/` focuses search anywhere.** `Esc` closes any drawer.
7. **Errors say what to do next.** "Couldn't load. [Retry]" — never bare "Network error".
8. **Latency budgets:** LCP < 1.8s on `/feed` (3G simulated); INP < 200ms on save toggle, kanban drag, filter change.
9. **Bundle budget:** initial JS ≤ 180KB gzipped per route. Tree-shake Radix; no full-barrel imports.
10. **44×44 minimum tap targets** on every primary action. `prefers-reduced-motion` respected globally.

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

Frontend mirrors with `ROLE_GROUPS` in `frontend/src/lib/auth/RoleGuard.tsx`:
- `student` ⊇ ENDUSER_STUDENT, INTERNAL_USER, DEV, ADMIN, OWNER
- `mentor` ⊇ MENTOR, ADMIN, OWNER
- `admin` ⊇ ADMIN, OWNER
- `owner` ⊇ OWNER

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

### Test health snapshot (verified 2026-05-10 on `main@5549d52`)
- `pytest backend/tests/unit` — **118 passed**, 0 failed (29.3s)
- `pytest backend/tests/integration` — **50 passed**, 0 failed (5.3s)
- `python -m compileall backend/app backend/tests` — clean
- `python scripts/docs_governance_check.py` — 0 terminology / link / canonical-tail failures
- Rerun: `pytest backend/tests/unit backend/tests/integration -q && python scripts/docs_governance_check.py`

### Done

**Backend / platform:**
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
- Acceptance: SLC-CORE-004/005, SLC-ROLE-001..005, SLC-OPS-003, SLC-TRUST-001..003, SLC-UI-001..003 marked Complete.

**Frontend (greenfield, on `feat/frontend-greenfield`, commit `f01bc08`):**
- **S1 Foundation** — `bun run lint` clean, `bun run build` green, 22 routes generated.
- Theme tokens (warm paper palette + validated/generated/caution/danger semantics) wired into Tailwind 4 `@theme`.
- Sora / IBM Plex Sans / IBM Plex Mono via `next/font`.
- REST client with bearer-token injection, silent refresh 60s before expiry, single 401 retry, typed `ApiError`.
- Endpoint modules for all 13 backend v1 routers.
- AuthProvider + RoleGuard with student/mentor/admin/owner role groups.
- shadcn-style primitives over Radix (Button, Input, Label, Card, Badge, Skeleton). Lucide icons only.
- AppShell with role-aware Sidebar + TopBar. KPI alert polling (60s) on admin shell. `/` focuses search.
- Marketing landing, login (Suspense-wrapped), signup, 4-step onboarding wizard with localStorage autosave.
- Live `/feed` page wired to `POST /recommendations` with stage chips + supporting/limiting factor lists.
- Placeholder routes for every flow F2–F8b so navigation never 404s.

### Remaining

**Backend:**
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

**Frontend (sprint plan, see `frontend/README.md`):**
- **S2 Auth + Onboarding polish** — feed empty state, profile edit page wired to `PUT /profile`.
- **S3 Discover + Saved** — sticky filter bar, `ScholarshipCard`, kanban tracker with optimistic drag.
- **S4 Recommendations** — full `RecommendationCard` with stage chips, supporting/limiting factor expansion, `EligibilityMatrix`.
- **S5 Documents** — upload + grounding selector + four-partition `FeedbackPartition` (validated / retrieved / generated / limitations).
- **S6 Interviews** — adaptive Q/A loop + `RubricRadar` (recharts) + coaching analytics line charts.
- **S7 Mentor** — pending queue + split-pane review form (summary/strengths/revision_priorities/caution_notes).
- **S8 Admin / Curation** — ingestion run management (retry, bulk-retry, snapshot viewer) + curation state-machine UI.
- **S9 Owner / Health** — RBAC role mutation modal, audit log table with revert, KPI alert banner, analytics dashboard.
- **S10 Polish** — a11y axe-core gate, responsive matrix (375/768/1024/1440), Playwright E2E for F1–F3, RBAC matrix test, browser-smoke selectors re-pointed to greenfield routes.

### Known low-priority issues (from 2026-05-10 audit + greenfield rebuild)
- `backend/tests/unit/test_document_service.py:286` — `test_retrieve_bounded_guidance_expands_degree_and_field_dimensions` carries `@pytest.mark.asyncio` but is sync; pytest-asyncio warns and skips the async path. Drop the decorator or make the test `async def`.
- Local `.venv` drifts from `backend/requirements.txt` pins (Python 3.14 + fastapi 0.135 + sqlalchemy 2.0.48 vs pinned Python 3.12 + fastapi 0.115 + sqlalchemy 2.0.35). CI uses Python 3.12; local devs should rebuild with `py -3.12 -m venv .venv312 && .venv312\Scripts\python -m pip install -r backend/requirements.txt`.
- Greenfield rebuild lives on `feat/frontend-greenfield`. Old per-route admin/curation/owner pages were removed in favour of `(admin)/admin/*`, `(mentor)/mentor/*`, `(student)/*` group-routed shells.
- Frontend type contracts moved: `frontend/src/lib/types.ts` → `frontend/src/lib/api/types.ts`. Hand-sync rule still applies.
- Browser-smoke (`tests/e2e/playwright/*`) still targets pre-greenfield routes; selectors re-point during S10.

### Next 3 priorities (per status report)
1. Expand grounding depth + citation density across broader scholarship coverage.
2. Expand recommendation benchmark dataset coverage; calibrate rerank weights with judged samples.
3. Strengthen ingestion coverage (richer parsers + captured HTML snapshot management).

## Critical rules
- Structured validated data is authoritative for eligibility, deadlines, funding rules. RAG is advisory; never the authority for scholarship rules.
- Public `/scholarships` returns **published only**.
- Eligibility = relational queries through the Knowledge-Graph Layer, not AI guesses.
- Do not import from `backend/legacy/`, `ai_services/`, `setup/`.
- Backend Pydantic schemas are the authoritative API contract; `frontend/src/lib/api/types.ts` is hand-synced.
- New feature = new service module inside the FastAPI app, not a new deployable.
- Use pgvector for MVP; do not introduce a separate search engine without justification.
- When updating runtime behavior, update `docs/scholarai/IMPLEMENTATION_STATUS_REPORT.md` in the same PR.
- Frontend UX rules (above) are PR-blocking. Validated-vs-AI partition is non-negotiable. No streaming-text theatre, no spinner soup, no emoji-as-UI, no AI-vendor branding (no model names, no chat-as-default outside interview practice).
