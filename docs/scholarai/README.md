# ScholarAI Documentation Pack

This directory is the source of truth for the new ScholarAI documentation set. It exists to give a 3-developer team a concrete, implementation-grounded set of documents for shipping a 16-week MVP under tight budget constraints without mixing MVP decisions with deferred research or startup-scale ideas.

The pack is anchored to the repository defaults in `.codex/AGENTS.md`. When older documents elsewhere in `docs/` disagree, this pack should keep the newer rules explicit: modular monolith, Canada-first corpus, Fulbright-related USA scope, and DAAD deferred.

## Purpose of This Pack

- Define the MVP boundary before implementation expands.
- Keep product, architecture, data, and research terminology consistent across the repo.
- Give each developer a clear documentation lane that maps to actual delivery work.
- Preserve explicit assumptions, risks, and deferred items so the team does not overbuild.

## File Tree

```text
docs/scholarai/
|-- README.md
|-- WORKPLAN.md
|-- 01_executive_summary.md
|-- 02_prd_and_scope.md
|-- 03_brand_and_design_system.md
|-- 04_requirements_and_governance.md
|-- 05_system_architecture.md
|-- 06_data_models.md
|-- 07_ingestion_and_curation.md
|-- 08_recommendation_and_ml.md
|-- 09_xai_rag_and_interview.md
|-- 10_backend_api_and_repo.md
|-- 11_research_and_evaluation.md
|-- 12_execution_plan.md
|-- 13_qa_devops_and_risks.md
|-- 14_future_roadmap.md
\-- diagrams/
```

The documentation foundation now includes `README.md`, `WORKPLAN.md`, and the full fourteen-file core ScholarAI pack covering scope, brand, requirements, architecture, data, curation, recommendation, AI assistance, backend structure, research, execution, QA, and roadmap decisions.

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

## Key Architecture Decisions Summary

- ScholarAI ships the MVP as a modular monolith.
- The frontend stack is Next.js + React + TypeScript + TailwindCSS.
- The backend stack is FastAPI with Alembic migrations.
- Background processing uses Celery with Redis.
- PostgreSQL is the primary system of record, with `pgvector` as the default semantic retrieval layer.
- The Knowledge Graph Layer is mandatory conceptually, but the MVP may implement it as a relationally derived graph abstraction unless a narrow Neo4j slice is simpler.
- Structured validated data is authoritative for eligibility, deadlines, funding rules, and official scholarship requirements.
- RAG, if used in MVP, is limited to bounded SOP document assistance and cannot override validated scholarship data.
- Ranking language should use `Estimated Scholarship Fit Score` unless real outcome labels justify stronger claims.
- MVP data coverage is Canada-first for MS Data Science, MS Artificial Intelligence, and MS Analytics.
- USA scope is limited to Fulbright-related provider information, funding rules, and narrow cross-border logic needed for the MVP.
- DAAD stays out of MVP and belongs in future-roadmap material only.
- Deployment defaults stay low-ops: Docker Compose locally and GitHub Actions for CI/CD.
- Provenance states remain `raw`, `validated`, and `published` across ingestion and curation flows.

## Required Diagrams

1. System context diagram showing users, external scholarship sources, ScholarAI, and operating boundaries.
2. Modular monolith container diagram showing Next.js frontend, FastAPI app modules, Celery workers, Redis, PostgreSQL, and the logical Knowledge Graph Layer.
3. Deployment diagram for local and MVP environments using Docker Compose and GitHub Actions.
4. Data provenance flow diagram covering `raw`, `validated`, and `published` states.
5. Ingestion pipeline diagram showing Playwright extraction, Pandas transforms, Pydantic validation, review, and publish steps.
6. Canonical data model / ERD for students, scholarships, providers, programs, requirements, deadlines, and provenance records.
7. Logical graph diagram showing how eligibility entities connect inside the Knowledge Graph Layer.
8. Recommendation pipeline diagram showing eligibility filtering, semantic retrieval, ranking, and explanation output.
9. RAG assistant diagram showing retrieval boundaries and why validated records remain authoritative.
10. Interview practice sequence diagram showing prompt generation, response capture, evaluation, and feedback publication.
11. Async jobs diagram showing scheduled ingestion, validation jobs, re-indexing, and notification triggers.
12. Role and permission diagram showing student and admin responsibilities, with mentor scope added only if it survives MVP cuts.

Mermaid should be the default format for these diagrams unless a stronger repository-standard alternative emerges.

## Glossary of Core Terms

| Term | Meaning in ScholarAI |
|---|---|
| `MVP` | The 16-week, budget-constrained first release the 3-developer team can realistically ship. |
| `Modular Monolith` | A single deployable application with clear internal module boundaries, not a microservice system. |
| `Canada-first` | The default MVP geographic scope for universities, programs, and scholarship discovery. |
| `Fulbright-related USA scope` | The only allowed USA expansion in MVP: provider data, funding rules, and directly required cross-border logic tied to Fulbright. |
| `DAAD deferred` | DAAD support is explicitly outside MVP and belongs in future work. |
| `Knowledge Graph Layer` | The logical graph-based eligibility and relationship layer used by ScholarAI, whether implemented with Neo4j or a relationally derived graph abstraction. |
| `pgvector` | PostgreSQL extension used for vector storage and semantic retrieval in the recommendation and RAG flows. |
| `Estimated Scholarship Fit Score` | A ranking-oriented score that estimates how well a scholarship matches a student profile without claiming causal success prediction. |
| `RAG` | Retrieval-augmented generation used for bounded document assistance such as SOP feedback, always subordinate to validated source data. |
| `Provenance state` | The status of a record as it moves through ingestion: `raw`, `validated`, or `published`. |
| `Validated data` | Structured scholarship data that has passed schema checks and review and is treated as the authority for rules and deadlines. |
| `Ingestion pipeline` | The extraction, parsing, validation, review, and publishing workflow used to turn source content into structured records. |

## MVP Decision

This documentation pack is intentionally built around the smallest credible ScholarAI release: a Canada-first scholarship discovery and assistance platform for three MS program areas, delivered as a modular monolith by a 3-person team in 16 weeks.

## Deferred Items

- Broad USA scholarship or university discovery outside Fulbright-related scope.
- DAAD ingestion, matching, or provider-specific flows.
- Startup-scale service decomposition, expensive managed infrastructure, or broad multi-region expansion.
- Stronger predictive claims than `Estimated Scholarship Fit Score` without real outcome labels.

## Assumptions

- `.codex/AGENTS.md` is the current governing specification for this documentation pack.
- The remaining files in the tree will be created iteratively and kept aligned with the section map in this README.
- Mermaid is acceptable for version-controlled diagrams in a limited-budget student project.

## Risks

- Contributors may reuse outdated content from older `docs/` files that conflicts with this pack's scope and architecture rules.
- If the team treats deferred ideas as MVP requirements, the 16-week plan will become unrealistic.
- If terminology drifts between files, the pack will stop serving as a reliable implementation guide.
