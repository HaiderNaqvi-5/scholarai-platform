# ScholarAI Documentation Pack

## Purpose
This folder is the canonical documentation source of truth for ScholarAI product scope, architecture, research framing, and execution planning. It is written for a 3-developer, 16-week, MVP-first delivery model.

## Implementation Note
The first coding phase normalizes the repository in place around the existing `frontend/` and `backend/` roots. A future `apps/*` migration remains optional and deferred until the MVP foundation is stable.

## File Tree
```text
docs/scholarai/
├── README.md
├── WORKPLAN.md
├── CODEX_MASTER_PROMPT_V1.md
├── CODEX_TASK_01_DOC_MIGRATION.md
├── 01_executive_summary.md
├── 02_prd_and_scope.md
├── 03_brand_and_design_system.md
├── 04_requirements_and_governance.md
├── 05_system_architecture.md
├── 06_data_models.md
├── 07_ingestion_and_curation.md
├── 08_recommendation_and_ml.md
├── 09_xai_rag_and_interview.md
├── 10_backend_api_and_repo.md
├── 11_research_and_evaluation.md
├── 12_execution_plan.md
├── 13_qa_devops_and_risks.md
├── 14_future_roadmap.md
├── IMPLEMENTATION_STATUS_REPORT.md
├── DEMO_READINESS_AUDIT.md
├── INTERNAL_HANDOFF_PACKAGE.md
└── PUBLIC_LIVE_HARDENING_PLAN.md
```

## Section-To-File Mapping
| Topic | Canonical file |
|---|---|
| Product intent and summary | `01_executive_summary.md` |
| PRD, MVP boundaries, scope control | `02_prd_and_scope.md` |
| Visual system and UX standards | `03_brand_and_design_system.md` |
| Requirements and governance rules | `04_requirements_and_governance.md` |
| Architecture and runtime boundaries | `05_system_architecture.md` |
| Data model, schema, and graph layer | `06_data_models.md` |
| Ingestion, curation, provenance | `07_ingestion_and_curation.md` |
| Recommendation and ML modeling | `08_recommendation_and_ml.md` |
| Explainability, RAG, interview subsystems | `09_xai_rag_and_interview.md` |
| Backend API and repository conventions | `10_backend_api_and_repo.md` |
| Research design and evaluation methods | `11_research_and_evaluation.md` |
| 16-week delivery sequence | `12_execution_plan.md` |
| QA, DevOps, and risk controls | `13_qa_devops_and_risks.md` |
| Future extensions and startup roadmap | `14_future_roadmap.md` |

## Key Architecture Decisions Summary
1. MVP architecture is a modular monolith.
2. Frontend is Next.js + React + TypeScript + TailwindCSS.
3. Backend is FastAPI.
4. Async tasks run through Celery + Redis.
5. PostgreSQL is primary data store and pgvector is used for vector search.
6. Knowledge Graph Layer is mandatory logically; MVP implementation can be Neo4j or a relationally derived abstraction.
7. Ingestion stack is Playwright + Pandas + Pydantic.
8. Deployment baseline is Docker Compose and migrations use Alembic.
9. MVP corpus is Canada-first for MS Data Science, MS Artificial Intelligence, and MS Analytics.
10. USA usage is restricted to Fulbright-related scope and narrowly scoped cross-border logic.
11. DAAD is not part of MVP and is deferred to Future Research Extensions.
12. Structured validated data is authoritative for eligibility, deadlines, funding rules, and official scholarship requirements.

## Current Implementation Status
- Current repo-evidence audit: `IMPLEMENTATION_STATUS_REPORT.md`
- Demo-readiness audit: `DEMO_READINESS_AUDIT.md`
- Internal handoff and presentation note: `INTERNAL_HANDOFF_PACKAGE.md`
- Public-live readiness gap analysis: `PUBLIC_LIVE_HARDENING_PLAN.md`
- Current codebase reality:
  - auth, protected routes, and session persistence are implemented
  - profile save/load and a functional onboarding route are implemented
  - public scholarship browse, search/filter, and scholarship detail pages are implemented
  - dashboard, saved opportunities, document assistance, interview practice, and curation are implemented as narrow MVP slices
  - curation now includes manual raw import plus source-registry ingestion runs
  - migration-driven bootstrap and browser smoke checks in CI are implemented
  - Phase 1 recommendation depth is now active (relational eligibility graph abstraction, pgvector retrieval, heuristic rerank, and rules-only fallback)
  - Phase 2 adds scholarship-grounded bounded guidance for documents and interviews with explicit fact/guidance/limitation separation while keeping Canada-first scope fixed
  - broader ingestion coverage is still incomplete

## Phase 2 API Contract Updates (Canada-first Fixed)
- `POST /api/v1/documents` now accepts optional scholarship grounding identifiers.
- `POST /api/v1/documents/{id}/feedback` returns explicit grounded-context sections:
  - validated scholarship facts
  - retrieved writing guidance
  - generated guidance
  - limitations
- `POST /api/v1/interviews` now accepts `practice_mode` and optional `scholarship_id`.
- `GET /api/v1/interviews/{id}` now returns session history summary plus rubric trend summary.
- Invalid grounding IDs are expected to fail cleanly with structured validation errors.

## Required Diagrams List
1. Product context and actor map.
2. Modular monolith container diagram.
3. Scholarship recommendation pipeline (eligibility filter -> vector retrieval -> reranking).
4. Data ingestion and provenance lifecycle (`raw` -> `validated` -> `published`).
5. Knowledge Graph Layer logical model and MVP implementation choice.
6. Primary relational schema ERD.
7. API boundary and backend module map.
8. 16-week delivery roadmap diagram.
9. Risk and quality gate flow (development to release).

## Glossary Of Core Terms
| Term | Definition |
|---|---|
| MVP | Minimum viable product delivered by 3 developers in 16 weeks under constrained budget. |
| Modular monolith | Single deployable backend with clear internal service boundaries. |
| Knowledge Graph Layer | Logical graph reasoning layer used for eligibility and relationship-aware filtering. |
| Structured validated data | Parsed and schema-validated records that serve as source of truth for policy-critical fields. |
| Provenance states | Data lifecycle states: `raw`, `validated`, `published`. |
| Estimated Scholarship Fit Score | Non-causal model output indicating estimated fit based on available features and assumptions. |
| Application Competitiveness Score | Non-causal estimate of application strength relative to scholarship requirements. |
| RAG | Retrieval-Augmented Generation limited to writing guidance and feedback, not policy truth. |
| Future Research Extensions | Deferred research-focused capabilities outside MVP scope. |
| Post-MVP Startup Features | Commercial expansion features after MVP stabilization and validation. |

## MVP decision
`docs/scholarai/` is the canonical home for active ScholarAI documentation, and migration proceeds through this pack.

## Deferred items
- Legacy docs archival execution (proposed in `WORKPLAN.md`).
- Cross-file diagram standardization pass.

## Assumptions
- Existing `docs/*.md` files outside this folder are treated as legacy inputs until migrated.
- Prompt/task files in this folder remain active governance inputs during migration.
- Section names and terms defined here are reused verbatim across new canonical docs.

## Risks
- If legacy docs continue to be edited as primary sources, terminology drift will continue.
- Diagram updates lagging behind text can reintroduce architecture inconsistencies.
- Unclear ownership of documentation updates can weaken source-of-truth discipline.
