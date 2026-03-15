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
- Repository status: documentation-first migration in progress.
- Canonical docs `01` through `14` now define the product, scope, design system, data model, architecture, evaluation, execution plan, QA strategy, and roadmap baseline.
- Phase 1 foundation implementation keeps `frontend/` and `backend/` as the active roots while the repo is normalized in place.
- Advanced features remain deferred until the first vertical slice is implemented against the normalized foundation.

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
