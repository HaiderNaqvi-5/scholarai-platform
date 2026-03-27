# ScholarAI Platform

ScholarAI is an AI-powered scholarship platform focused on helping students discover scholarships, evaluate eligibility, plan application strategy, improve application documents, and practice scholarship interviews.

## Current v0.1 Scope
- Delivery model: 3 developers, 16 weeks, limited budget.
- Architecture style: modular monolith.
- Primary corpus: Canada-focused scholarship and program scope.
- Program scope: MS Data Science, MS Artificial Intelligence, MS Analytics.
- USA scope: limited to Fulbright-related information and narrowly scoped cross-border logic.
- DAAD: deferred to Future Research Extensions.
- Source of truth for policy-critical fields: structured validated data (not free-form generation).

## High-Level Architecture Summary
- Frontend: Next.js + React + TypeScript + TailwindCSS.
- Backend: FastAPI.
- Async processing: Celery + Redis.
- Data layer: PostgreSQL + pgvector.
- Knowledge Graph Layer: mandatory logical layer, implemented in v0.1 as either narrowly scoped Neo4j or a relationally derived graph abstraction.
- Ingestion: Playwright + Pandas + Pydantic.
- Deployment baseline: Docker Compose.
- Database migrations: Alembic.
- CI/CD baseline: GitHub Actions.

## Documentation Entry Points
- Canonical docs index: `docs/scholarai/README.md`
- Migration and authoring plan: `docs/scholarai/WORKPLAN.md`
- Current implementation audit: `docs/scholarai/IMPLEMENTATION_STATUS_REPORT.md`
- Internal v0.1 handoff: `docs/scholarai/INTERNAL_HANDOFF_PACKAGE.md`
- Public-live hardening plan: `docs/scholarai/PUBLIC_LIVE_HARDENING_PLAN.md`
- Governing migration specification: `docs/scholarai/CODEX_MASTER_PROMPT_V1.md`
- Current migration task: `docs/scholarai/CODEX_TASK_01_DOC_MIGRATION.md`

Legacy files under `docs/` are being migrated into `docs/scholarai/` and should be treated as transitional inputs until archived.

## Repository Navigation
```text
scholarai-platform/
├── backend/                 # Active FastAPI modular monolith root for Phase 1
├── frontend/                # Active Next.js app root for Phase 1
├── workers/                 # Thin worker scaffolding and future operational entrypoints
├── shared/                  # Shared contracts and cross-app references
├── tests/                   # Top-level browser and e2e planning assets
├── infra/                   # Local-first infrastructure notes and docker guidance
├── docs/
│   ├── scholarai/           # Canonical active documentation pack
│   └── *.md                 # Legacy docs pending migration
├── backend/legacy/          # Quarantined inactive backend routes and services
├── ai_services/             # Legacy implementation area proposed for later archive/refactor
└── setup/                   # Legacy setup area proposed for later archive/refactor
```

## Implementation Status
- Repository status: active internal v0.1 implementation with documentation-led scope control.
- Canonical docs `01` through `14` define the product, scope, design system, data model, architecture, evaluation, execution plan, QA strategy, and roadmap baseline.
- Active implementation track: docs-first RBAC expansion with capability-based access, institution-scoped university permissions, and compatibility-window migration.
- The current implementation includes:
  - auth and session persistence
  - public scholarship browse, search/filter, and scholarship detail pages backed by published-only routes
  - profile save/load flow and a functional onboarding route
  - seeded recommendation flow with explanation panels
  - saved opportunities and dashboard shell
  - document assistance shell
  - interview practice shell
  - curator workflow with `raw`, `validated`, and `published` states
  - source-registry ingestion runs that create raw records for curation
  - migration-driven bootstrap and browser smoke checks in CI
- Phase 2 now adds scholarship-grounded bounded guidance in Documents and Interviews, with explicit API-level separation of validated scholarship facts, retrieved writing guidance, generated guidance, and limitations.
- Remaining implementation depth is concentrated in richer ingestion coverage and recommendation evaluation/tuning beyond the new Phase 1 hybrid ranking baseline.

## Phase 2 API Updates (Canada-first Fixed)
- `POST /api/v1/documents` accepts optional scholarship grounding identifiers for Canada-scoped scholarship context.
- `POST /api/v1/documents/{id}/feedback` returns explicit grounded-context sections for validated facts, retrieved writing guidance, generated guidance, and limitations.
- `POST /api/v1/interviews` accepts `practice_mode` plus optional `scholarship_id`.
- `GET /api/v1/interviews/{id}` returns session history summary and rubric trend summary used by adaptive follow-up.
- Invalid grounding identifiers fail cleanly with structured error responses.

## Local v0.1 Run
### Env files
- Docker Compose path: copy `.env.example` to `.env` only if you need to override defaults.
- Direct backend path: copy `backend/.env.example` to `backend/.env`.
- Direct frontend path: copy `frontend/.env.local.example` to `frontend/.env.local`.
- No secrets belong in source control. Example values are for internal local/demo use only.

### Quick internal Docker path
1. Run `docker compose up --build`.
2. Wait for backend bootstrap to apply Alembic migrations and seed demo data.
3. Open `http://localhost:3000`.
4. Check `http://localhost:8000/health` if the UI does not load expected data.

### Direct local path
1. Start PostgreSQL and Redis locally.
2. In `backend/`, use Python `3.12` and run `pip install -r requirements.txt`.
3. In `frontend/`, run `npm ci`.
4. From `backend/`, run `python scripts/bootstrap_local.py`.
5. Start the backend with `uvicorn app.main:app --reload`.
6. Start the frontend with `npm run dev`.

### Backend test environment (recommended)
- Use Python `3.12` for backend unit/integration tests.
- Example local venv flow:
  1. `py -3.12 -m venv .venv312`
  2. `.\.venv312\Scripts\python -m pip install -r backend/requirements.txt`
  3. `.\.venv312\Scripts\python -m pytest backend/tests/unit backend/tests/integration -q`

### Important local run note
- If route files or app-structure files changed after the frontend server started, restart the Next.js process or rerun `docker compose up --build`. A stale dev process can serve false `404` responses for newly added routes.

## Demo Readiness
- Current repo-level audit: `docs/scholarai/DEMO_READINESS_AUDIT.md`
- Full implementation status audit: `docs/scholarai/IMPLEMENTATION_STATUS_REPORT.md`
- Internal handoff and presenter notes: `docs/scholarai/INTERNAL_HANDOFF_PACKAGE.md`
- Recommended local demo path: scholarships -> scholarship detail -> signup/login -> dashboard -> onboarding/profile -> recommendations -> document feedback -> interview -> curation
- Seeded local demo accounts:
  - student: `student@example.com` / `strongpass1`
  - admin: `admin@example.com` / `strongpass1`
- API rehearsal script: `backend/scripts/rehearse_seeded_demo.py`
- Rehearsal script: `tests/e2e/playwright/rehearse_seeded_demo.py`
- Smoke suite runner: `tests/e2e/playwright/run_smoke_suite.py`

## v0.1 decision
ScholarAI implementation will follow a documentation-first path, with `docs/scholarai/` as the active source of truth.

## Deferred items
- Legacy docs archival/removal actions after migration content is finalized.
- Feature work outside v0.1 constraints.

## Assumptions
- Team will use `docs/scholarai/WORKPLAN.md` as the sequencing reference for future documentation passes.
- Legacy docs remain available for extraction until explicit archive/remove actions are approved.
- Architecture defaults in `.codex/AGENTS.md` remain governing constraints.

## Risks
- Parallel editing in legacy and canonical docs may create inconsistencies.
- Scope creep into deferred startup features can break v0.1 feasibility.
- Early code work before canonical docs are complete can lock in conflicting assumptions.


Validation check injection: MVP
