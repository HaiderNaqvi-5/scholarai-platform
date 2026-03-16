# ScholarAI Platform

ScholarAI is an AI-powered scholarship platform focused on helping students discover scholarships, evaluate eligibility, plan application strategy, improve application documents, and practice scholarship interviews.

## Current MVP Scope
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
- Knowledge Graph Layer: mandatory logical layer, implemented in MVP as either narrowly scoped Neo4j or a relationally derived graph abstraction.
- Ingestion: Playwright + Pandas + Pydantic.
- Deployment baseline: Docker Compose.
- Database migrations: Alembic.
- CI/CD baseline: GitHub Actions.

## Documentation Entry Points
- Canonical docs index: `docs/scholarai/README.md`
- Migration and authoring plan: `docs/scholarai/WORKPLAN.md`
- Current implementation audit: `docs/scholarai/IMPLEMENTATION_STATUS_REPORT.md`
- Internal MVP handoff: `docs/scholarai/INTERNAL_HANDOFF_PACKAGE.md`
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
├── ai_services/             # Legacy implementation area proposed for later archive/refactor
└── setup/                   # Legacy setup area proposed for later archive/refactor
```

## Implementation Status
- Repository status: active MVP implementation with documentation-led scope control.
- Canonical docs `01` through `14` define the product, scope, design system, data model, architecture, evaluation, execution plan, QA strategy, and roadmap baseline.
- The current implementation includes:
  - auth and session persistence
  - public scholarship browse and detail pages backed by published-only routes
  - public published-scholarship read endpoints
  - profile save/load flow
  - seeded recommendation flow with explanation panels
  - saved opportunities and dashboard shell
  - document assistance shell
  - interview practice shell
  - curator workflow with `raw`, `validated`, and `published` states
  - manual raw-record import into curation as the current narrow upstream bridge
- Fresh local environments now use an Alembic-driven bootstrap path plus seeded demo data for MVP rehearsal.
- Remaining MVP gaps include upstream ingestion automation, broader discovery filters, and tighter API-wide contract consistency.

## Local MVP Run
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
2. In `backend/`, use Python `3.11` and run `pip install -r requirements.txt`.
3. In `frontend/`, run `npm ci`.
4. From `backend/`, run `python scripts/bootstrap_local.py`.
5. Start the backend with `uvicorn app.main:app --reload`.
6. Start the frontend with `npm run dev`.

### Important local run note
- If route files or app-structure files changed after the frontend server started, restart the Next.js process or rerun `docker compose up --build`. A stale dev process can serve false `404` responses for newly added routes.

## Demo Readiness
- Current repo-level audit: `docs/scholarai/DEMO_READINESS_AUDIT.md`
- Full implementation status audit: `docs/scholarai/IMPLEMENTATION_STATUS_REPORT.md`
- Internal handoff and presenter notes: `docs/scholarai/INTERNAL_HANDOFF_PACKAGE.md`
- Recommended local demo path: scholarships -> scholarship detail -> signup/login -> dashboard -> profile -> recommendations -> document feedback -> interview -> curation
- API rehearsal script: `backend/scripts/rehearse_seeded_demo.py`
- Rehearsal script: `tests/e2e/playwright/rehearse_seeded_demo.py`

## MVP decision
ScholarAI implementation will follow a documentation-first path, with `docs/scholarai/` as the active source of truth.

## Deferred items
- Legacy docs archival/removal actions after migration content is finalized.
- Feature work outside MVP constraints.

## Assumptions
- Team will use `docs/scholarai/WORKPLAN.md` as the sequencing reference for future documentation passes.
- Legacy docs remain available for extraction until explicit archive/remove actions are approved.
- Architecture defaults in `.codex/AGENTS.md` remain governing constraints.

## Risks
- Parallel editing in legacy and canonical docs may create inconsistencies.
- Scope creep into deferred startup features can break MVP feasibility.
- Early code work before canonical docs are complete can lock in conflicting assumptions.
