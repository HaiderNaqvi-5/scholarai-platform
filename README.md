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
- The current implementation includes auth, dashboard, saved opportunities, seeded recommendation flow, document assistance, interview practice, and curator workflow foundations.
- Fresh local environments now use an Alembic-driven bootstrap path plus seeded demo data for MVP rehearsal.

## Local MVP Run
### Docker Compose
1. Run `docker compose up --build`.
2. If you need custom values, copy `.env.example` to `.env` and adjust it first.
3. Open `http://localhost:3000`.

### Direct Local Run
1. Copy `backend/.env.example` to `backend/.env`.
2. Copy `frontend/.env.local.example` to `frontend/.env.local`.
3. Start PostgreSQL and Redis locally.
4. In `backend/`, run `pip install -r requirements.txt`.
5. In `frontend/`, run `npm ci`.
6. Run `python scripts/bootstrap_local.py` from `backend/` to apply migrations and seed the demo dataset.
7. Start the backend with `uvicorn app.main:app --reload`.
8. Start the frontend with `npm run dev`.

## Demo Readiness
- Current repo-level audit: `docs/scholarai/DEMO_READINESS_AUDIT.md`
- Recommended local demo path: login -> dashboard -> profile -> recommendations -> document feedback -> interview -> curation
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
