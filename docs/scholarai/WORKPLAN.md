# ScholarAI Documentation Work Plan

This work plan defines the documentation foundation for `docs/scholarai/`. It assumes a 16-week delivery window, a 3-developer team, limited budget, and an MVP-first execution model. The pack is written against the repository defaults in `.codex/AGENTS.md`, not against older legacy docs that diverge from those defaults.

## Planning Baseline

- Delivery model: modular monolith for MVP.
- Core stack: Next.js + React + TypeScript + TailwindCSS, FastAPI, Celery, Redis, PostgreSQL, pgvector, Docker Compose, Alembic, GitHub Actions.
- Data scope: Canada-first corpus for the MVP; `Fulbright-related USA scope` only for the allowed USA surface area; DAAD deferred.
- Domain scope: scholarship discovery and application support for MS Data Science, MS Artificial Intelligence, and MS Analytics.
- Truth model: structured validated data is authoritative for eligibility, deadlines, funding rules, and official requirements.

## File Plan

| File | Purpose | Primary author | Authoring window |
|---|---|---|---|
| `docs/scholarai/README.md` | Entry point, scope guardrails, file tree, glossary, diagram inventory. | Developer 1 | Week 1 |
| `docs/scholarai/WORKPLAN.md` | Documentation roadmap, ownership, sequencing, and consistency rules. | Developer 2 | Week 1 |
| `docs/scholarai/01_executive_summary.md` | One-document summary of product problem, users, MVP, and thesis framing. | Developer 1 | Week 1 |
| `docs/scholarai/02_prd_and_scope.md` | MVP boundaries, personas, core journeys, non-goals, and Canada-first scope rules. | Developer 1 | Weeks 1-2 |
| `docs/scholarai/03_brand_and_design_system.md` | UI principles, typography, color system, interaction patterns, and accessibility expectations. | Developer 1 | Weeks 2-3 |
| `docs/scholarai/04_requirements_and_governance.md` | Functional requirements, non-functional requirements, provenance rules, and decision log. | Developer 2 | Weeks 2-3 |
| `docs/scholarai/05_system_architecture.md` | Modular monolith boundaries, service interactions, async jobs, deployment topology. | Developer 2 | Weeks 2-4 |
| `docs/scholarai/06_data_models.md` | Canonical entities, schemas, provenance states, ERD, and graph abstractions. | Developer 3 | Weeks 3-4 |
| `docs/scholarai/07_ingestion_and_curation.md` | Source onboarding, Playwright ingestion, validation, review workflow, and publishing pipeline. | Developer 3 | Weeks 4-5 |
| `docs/scholarai/08_recommendation_and_ml.md` | Matching pipeline, ranking logic, fit scoring, feature definitions, and offline evaluation plan. | Developer 3 | Weeks 5-6 |
| `docs/scholarai/09_xai_rag_and_interview.md` | Explainability outputs, RAG guardrails, interview practice architecture, and safety limits. | Developer 3 | Weeks 6-7 |
| `docs/scholarai/10_backend_api_and_repo.md` | FastAPI module layout, API conventions, background jobs, repo structure, and integration seams. | Developer 2 | Weeks 6-8 |
| `docs/scholarai/11_research_and_evaluation.md` | Research claims, threats to validity, metrics, and reproducibility expectations. | Developer 3 | Weeks 8-9 |
| `docs/scholarai/12_execution_plan.md` | Sprint breakdown, staffing plan, milestone gates, and MVP cut rules. | Developer 2 | Weeks 8-9 |
| `docs/scholarai/13_qa_devops_and_risks.md` | Test strategy, CI/CD, environments, observability, operational risk, and release checklist. | Developer 2 | Weeks 9-10 |
| `docs/scholarai/14_future_roadmap.md` | Deferred regions, advanced ML, startup-scale features, and post-MVP sequencing. | Developer 1 | Weeks 10-11 |
| `docs/scholarai/diagrams/` | Mermaid or version-controlled source diagrams referenced by the pack. | Shared | Continuous |

## Section-to-File Mapping

| Section | Target file | Notes |
|---|---|---|
| Documentation overview and glossary | `docs/scholarai/README.md` | Keeps onboarding fast for new contributors. |
| Documentation roadmap and authoring rules | `docs/scholarai/WORKPLAN.md` | Controls sequencing and consistency. |
| Product narrative and thesis framing | `docs/scholarai/01_executive_summary.md` | Non-technical summary for reviewers and stakeholders. |
| Problem statement, personas, MVP scope, and non-goals | `docs/scholarai/02_prd_and_scope.md` | Source of truth for what is in or out of MVP. |
| Brand principles, design tokens, and UI patterns | `docs/scholarai/03_brand_and_design_system.md` | Must stay aligned with frontend implementation. |
| Functional requirements, non-functional requirements, and governance | `docs/scholarai/04_requirements_and_governance.md` | Includes provenance and decision-control rules. |
| Modular monolith architecture, runtime components, and deployment shape | `docs/scholarai/05_system_architecture.md` | Source of truth for system boundaries. |
| Canonical entities, schemas, and graph abstraction | `docs/scholarai/06_data_models.md` | Covers relational and logical graph views. |
| Ingestion pipeline, validation workflow, and publication states | `docs/scholarai/07_ingestion_and_curation.md` | Anchors raw -> validated -> published data flow. |
| Recommendation stages, ranking logic, and fit score methodology | `docs/scholarai/08_recommendation_and_ml.md` | Must not overclaim predictive certainty. |
| Explainability, RAG assistant, and interview-prep flows | `docs/scholarai/09_xai_rag_and_interview.md` | Captures AI safety and UX boundaries. |
| Backend modules, API contracts, repo layout, and async processing | `docs/scholarai/10_backend_api_and_repo.md` | Ties architecture to actual code organization. |
| Research evaluation, metrics, and validity limits | `docs/scholarai/11_research_and_evaluation.md` | Keeps academic claims defensible. |
| Sprint plan, milestones, team allocation, and cut-line logic | `docs/scholarai/12_execution_plan.md` | Connects ambition to 16-week reality. |
| QA strategy, CI/CD, environments, and risk controls | `docs/scholarai/13_qa_devops_and_risks.md` | Covers release readiness and operations. |
| Deferred scope and post-MVP expansion path | `docs/scholarai/14_future_roadmap.md` | Prevents startup ideas from leaking into MVP. |

## Key Architecture Decisions That Must Remain Consistent

1. ScholarAI is documented and built as a modular monolith for MVP, not as microservices.
2. The frontend stack remains Next.js + React + TypeScript + TailwindCSS.
3. The backend stack remains FastAPI with Alembic-managed PostgreSQL migrations.
4. Background and long-running jobs use Celery with Redis, not ad hoc cron logic inside web requests.
5. PostgreSQL is the primary system of record, and `pgvector` is the default semantic retrieval layer.
6. The Knowledge Graph Layer is mandatory as a logical layer; MVP implementation may be a relationally derived graph abstraction unless a narrowly scoped Neo4j slice proves simpler.
7. Structured validated data is authoritative for scholarship rules, deadlines, and eligibility; LLM outputs cannot override validated records.
8. RAG is allowed only for bounded document assistance such as SOP feedback, and it is not the source of truth for scholarship requirements.
9. The recommendation output is framed as an `Estimated Scholarship Fit Score` unless real outcome labels justify a stronger claim.
10. MVP data scope is Canada-first for MS Data Science, MS Artificial Intelligence, and MS Analytics.
11. USA scope is limited to Fulbright-related provider information, funding rules, and narrow cross-border logic directly needed for the MVP.
12. DAAD is deferred out of MVP and documented only in future-facing sections.
13. Deployment targets local and small-team environments first through Docker Compose and GitHub Actions, with low-ops defaults.
14. Every data flow must preserve provenance states: `raw`, `validated`, and `published`.

## Unresolved Assumptions

1. The final physical implementation of the Knowledge Graph Layer is still open between a relationally derived graph view and a narrow Neo4j deployment.
2. The exact list of Canadian universities and scholarship providers in the MVP corpus is not yet frozen; the docs should describe onboarding criteria before naming a final list.
3. `Fulbright-related USA scope` is in scope, but the minimum viable surface area is still assumed to be provider and rule coverage rather than broad USA university discovery.
4. The first release is assumed to prioritize student-facing workflows plus the minimum admin tooling required to review and publish validated data.
5. Mentor-specific workflows are assumed to be thin or deferred unless the team demonstrates spare capacity after core discovery and assistant flows stabilize.
6. Mermaid is assumed to be the default diagram format because it is cheap, diffable, and repository-friendly for a 3-developer team.
7. Authentication and user-management documentation will align to the existing codebase if present; until then, the pack should describe role boundaries without inventing an auth stack.
8. OpenSearch is not assumed for the new pack unless later implementation evidence shows `pgvector` plus PostgreSQL search is insufficient for MVP needs.

## Document Authoring Order

1. Week 1: finalize `README.md`, `WORKPLAN.md`, `01_executive_summary.md`, and `02_prd_and_scope.md` so the team has a stable vocabulary and MVP boundary.
2. Weeks 2-4: write `03_brand_and_design_system.md`, `04_requirements_and_governance.md`, `05_system_architecture.md`, and `06_data_models.md` in parallel, because these define the build constraints for frontend, backend, and data work.
3. Weeks 4-7: produce `07_ingestion_and_curation.md`, `08_recommendation_and_ml.md`, and `09_xai_rag_and_interview.md` after the data model and architecture docs are stable.
4. Weeks 6-10: complete `10_backend_api_and_repo.md`, `11_research_and_evaluation.md`, `12_execution_plan.md`, and `13_qa_devops_and_risks.md` once the main technical decisions are documented.
5. Weeks 10-11: write `14_future_roadmap.md` last so deferred items are separated from what the team can actually ship in 16 weeks.
6. Weeks 12-16: keep all documents current with implementation decisions, but only after the owning document is updated first and related references are re-checked.

## Internal Consistency Checklist

- Use `Canada-first`, `Fulbright-related USA scope`, and `DAAD deferred` exactly as written.
- Use `modular monolith` consistently and avoid introducing service-splitting language.
- Refer to the logical graph component as the `Knowledge Graph Layer`.
- Refer to data states as `raw`, `validated`, and `published`.
- Use `Estimated Scholarship Fit Score` when discussing ranking output without real outcome labels.
- Keep any roadmap item that expands beyond Canada or beyond the three MVP programs out of MVP documents.

## MVP Decision

The documentation pack is organized around a Canada-first MVP delivered by a 3-developer team in 16 weeks, using a modular monolith and low-ops infrastructure. The pack will document only the architecture and scope that can realistically support that delivery model.

## Deferred Items

- Broad USA university discovery outside Fulbright-related scope.
- DAAD provider ingestion and recommendation support.
- Any startup-scale architecture that requires microservices or expensive managed infrastructure.
- Claims of outcome prediction stronger than `Estimated Scholarship Fit Score` without real labels.

## Assumptions

- `.codex/AGENTS.md` is the governing source when older repository docs disagree.
- The initial document set will follow the preferred file list in the repo guidance.
- Documentation ownership by developer is a lead role, not an exclusive editing lock.

## Risks

- Older docs in `docs/` already contain conflicting scope and architecture choices; contributors may accidentally copy them into the new pack.
- If the team delays scope documents, implementation may drift into non-MVP work that the 16-week schedule cannot absorb.
- If the Knowledge Graph Layer decision stays unresolved too long, data-model and recommendation docs may diverge.
