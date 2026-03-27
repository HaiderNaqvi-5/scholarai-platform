# ScholarAI Documentation Work Plan

## Objective
Progressively migrate ScholarAI documentation into a complete canonical pack before application code changes.

## Scope Of This Pass
- Audit `README.md` and `docs/` documentation.
- Classify current docs as aligned, partially reusable, conflicting, or obsolete.
- Create canonical entry points:
  - `docs/scholarai/WORKPLAN.md`
  - `docs/scholarai/README.md`
  - root `README.md`
- Propose archive/removal actions without deleting files in this pass.

## Implementation-Phase Note
The first coding phase normalizes the repository in place around `frontend/` and `backend/` instead of forcing an immediate migration to `apps/web` and `apps/api`.

## File Plan
| File | Pass 1 action | Status after pass 1 | Next action |
|---|---|---|---|
| `docs/scholarai/WORKPLAN.md` | Create | Canonical migration plan | Keep updated each migration pass |
| `docs/scholarai/README.md` | Create | Canonical docs index | Expand links as new docs are created |
| `README.md` | Rewrite | Canonical repo entry point | Keep aligned with `docs/scholarai/README.md` |
| `docs/scholarai/01_executive_summary.md` | Create | Canonical and active | Keep aligned with PRD and README |
| `docs/scholarai/02_prd_and_scope.md` | Create | Canonical and active | Keep aligned with governance and execution plan |
| `docs/scholarai/03_brand_and_design_system.md` | Create | Canonical and active | Reuse for future frontend implementation |
| `docs/scholarai/04_requirements_and_governance.md` | Create | Canonical and active | Use as review gate for later docs |
| `docs/scholarai/05_system_architecture.md` | Create | Canonical and active | Use as basis for data, API, and repo docs |
| `docs/scholarai/06_data_models.md` | Create | Canonical and active | Keep aligned with curation and architecture docs |
| `docs/scholarai/07_ingestion_and_curation.md` | Create | Canonical and active | Keep aligned with source-of-truth workflow |
| `docs/scholarai/08_recommendation_and_ml.md` | Create | Canonical and active | Keep aligned with evaluation and XAI docs |
| `docs/scholarai/09_xai_rag_and_interview.md` | Create | Canonical and active | Keep aligned with design and AI-governance docs |
| `docs/scholarai/10_backend_api_and_repo.md` | Create | Canonical and active | Use as implementation guardrail reference |
| `docs/scholarai/11_research_and_evaluation.md` | Create | Canonical and active | Use as thesis and experiment reference |
| `docs/scholarai/12_execution_plan.md` | Create | Canonical and active | Use as delivery baseline |
| `docs/scholarai/13_qa_devops_and_risks.md` | Create | Canonical and active | Use as quality and fallback reference |
| `docs/scholarai/14_future_roadmap.md` | Create | Canonical and active | Keep deferred scope separate from v0.1 |

## Section-To-File Mapping
| Section | Target file |
|---|---|
| Product intent, constraints, value proposition | `01_executive_summary.md` |
| Users, scope, non-goals, v0.1 boundaries | `02_prd_and_scope.md` |
| UX direction, brand rules, design system | `03_brand_and_design_system.md` |
| Functional requirements, governance, decision rules | `04_requirements_and_governance.md` |
| Modular monolith architecture and service boundaries | `05_system_architecture.md` |
| Relational schema, graph abstraction, data contracts | `06_data_models.md` |
| Scraping, validation, provenance lifecycle | `07_ingestion_and_curation.md` |
| Matching pipeline, ML framing, validity constraints | `08_recommendation_and_ml.md` |
| Explainability, RAG boundaries, interview subsystem | `09_xai_rag_and_interview.md` |
| API surface, backend module layout, repository standards | `10_backend_api_and_repo.md` |
| Research questions, experiments, reproducibility | `11_research_and_evaluation.md` |
| 16-week execution sequencing and ownership | `12_execution_plan.md` |
| QA strategy, CI/CD baseline, risk controls | `13_qa_devops_and_risks.md` |
| Future Research Extensions and Deferred By Stage Startup Features | `14_future_roadmap.md` |

## Key Architecture Decisions That Must Stay Consistent
1. v0.1 architecture is a modular monolith.
2. Frontend is Next.js + React + TypeScript + TailwindCSS.
3. Backend is FastAPI.
4. Async jobs use Celery + Redis.
5. PostgreSQL is primary database and pgvector is the vector layer.
6. Knowledge Graph Layer is mandatory logically; v0.1 implementation may be Neo4j or a relationally derived abstraction.
7. Data ingestion uses Playwright + Pandas + Pydantic.
8. Deployment baseline is Docker Compose.
9. Migrations use Alembic.
10. CI/CD baseline is GitHub Actions.
11. v0.1 data scope is Canada-first for MS Data Science, MS Artificial Intelligence, and MS Analytics.
12. USA scope is limited to Fulbright-related information and narrowly scoped cross-border logic.
13. DAAD is deferred to Future Research Extensions.
14. Structured validated data is the source of truth for eligibility, deadlines, funding rules, and official requirements.

## Documentation Audit Classification
| File | Classification | Proposed action | Rationale |
|---|---|---|---|
| `README.md` | Partially reusable | Rewritten in pass 1 | Good project framing but outdated stack/scope details (for example OpenSearch, mentorship in v0.1) |
| `docs/PRD.md` | Conflicting | Rewrite into `docs/scholarai/02_prd_and_scope.md`; then archive legacy | Includes DAAD in v0.1 and broad provider framing that conflicts with current constraints |
| `docs/architecture.md` | Partially reusable | Rewrite into `docs/scholarai/05_system_architecture.md`; then archive legacy | Useful problem framing, but data/store choices and novelty claims need tighter constraints |
| `docs/architecture_diagrams.md` | Conflicting | Rewrite diagrams in new pack; then archive legacy | Diagrams include OpenSearch and multi-model orchestration outside current v0.1 baseline |
| `docs/database_schema.md` | Partially reusable | Rewrite into `docs/scholarai/06_data_models.md`; then archive legacy | Contains useful entities but includes deferred mentorship and mixed scope language |
| `docs/deployment.md` | Partially reusable | Rewrite into `docs/scholarai/13_qa_devops_and_risks.md`; then archive legacy | Useful delivery constraints, but includes services and milestones not yet governance-locked |
| `docs/api_design.md` | Conflicting | Rewrite into `docs/scholarai/10_backend_api_and_repo.md`; then archive legacy | Includes non-v0.1 geography and deferred feature endpoints |
| `docs/ai_models.md` | Conflicting | Rewrite into `docs/scholarai/08_recommendation_and_ml.md`; then archive legacy | Contains unsupported metric targets and speculative implementation assumptions |
| `docs/knowledge_graph.md` | Partially reusable | Rewrite into `docs/scholarai/06_data_models.md` and `05_system_architecture.md`; then archive legacy | Core graph idea is useful but implementation claims are over-asserted |
| `docs/research.md` | Partially reusable | Rewrite into `docs/scholarai/11_research_and_evaluation.md`; then archive legacy | Useful RQ framing, but claims require tighter validity and v0.1 boundary control |
| `docs/skills.md` | Obsolete | Archive | Internal team skills matrix is not source-of-truth architecture/product documentation |
| `docs/phase_status_report.md` | Obsolete | Archive | Snapshot report tied to specific commit/branch; not stable product documentation |
| `docs/implementation_plan.md.resolved` | Conflicting | Archive after extracting reusable constraints into new pack | Contains stale absolute paths, mixed decisions, and unresolved v0.1 conflicts |
| `docs/scholarai/CODEX_MASTER_PROMPT_V1.md` | Aligned | Keep active | Governing migration constraints align with repo rules |
| `docs/scholarai/CODEX_TASK_01_DOC_MIGRATION.md` | Aligned | Keep active | Current execution task file |
| `docs/scholarai/MASTER_PROMPT_V2_2.md` | Partially reusable | Archive after migration | Contains overlapping guidance; keep one governing prompt to avoid drift |
| `docs/scholarai/MASTER_PROMPT_V2_1.md` | Obsolete | Remove in later cleanup pass | Placeholder-only file with no operational content |

## Unresolved Assumptions
1. OpenSearch is treated as non-v0.1 until a concrete unmet retrieval need is documented.
2. Mentorship workflows remain deferred from v0.1 and move to Deferred By Stage Startup Features.
3. Interview practice remains in v0.1, but voice-first flow may be phased if complexity exceeds timeline.
4. Any quantitative model target metrics are provisional until dataset quality and label strategy are validated.

## Document Authoring Order
1. `01_executive_summary.md`
2. `02_prd_and_scope.md`
3. `04_requirements_and_governance.md`
4. `05_system_architecture.md`
5. `03_brand_and_design_system.md`
6. `06_data_models.md`
7. `07_ingestion_and_curation.md`
8. `08_recommendation_and_ml.md`
9. `09_xai_rag_and_interview.md`
10. `10_backend_api_and_repo.md`
11. `12_execution_plan.md`
12. `13_qa_devops_and_risks.md`
13. `11_research_and_evaluation.md`
14. `14_future_roadmap.md`

## Migration Order For Old Docs
1. Rewrite core canonical docs in `docs/scholarai/` while preserving stable concepts from legacy files.
2. Add per-file migration notes in each new canonical doc header.
3. Move legacy conflicting/obsolete docs into a dated archive folder, for example `docs/archive/2026-03-pass1/`.
4. Keep only one active prompt/governance file set under `docs/scholarai/`.
5. Remove clearly empty placeholders only after archive snapshot is committed.

## RBAC Expansion Program (March 2026)
### Objective
Start local implementation through a docs-first authorization rewrite that introduces a capability-based matrix, institution-scoped university access, and a zero-downtime claim migration path.

### Locked Decisions
1. Authorization model uses explicit capabilities, not deep role inheritance.
2. University access is institution-scoped from the first contract draft.
3. Migration uses a compatibility window mapping legacy role claims to capability claims.
4. Canonical docs under `docs/scholarai/` are authoritative when conflicts exist.

### Canonical Roles
- `ENDUSER_STUDENT`
- `INTERNAL_USER`
- `DEV`
- `ADMIN`
- `UNIVERSITY`
- `OWNER`

### Phase-By-Phase Delivery (Docs First, Then Code)
| Phase | Focus | Primary docs | Exit gate |
|---|---|---|---|
| 1 | Governance freeze and capability registry | `04_requirements_and_governance.md`, `06_data_models.md` | Capability IDs, deny-by-default rules, and owners approved |
| 2 | Institution scope contract | `06_data_models.md`, `10_backend_api_and_repo.md` | `institution_id` scope rules and cross-institution deny behavior documented |
| 3 | Endpoint-level authorization map | `10_backend_api_and_repo.md` | All mounted endpoint groups mapped to required capabilities |
| 4 | Compatibility-window migration contract | `12_execution_plan.md`, `10_backend_api_and_repo.md` | Dual-claim strategy (`role` + `capabilities`) and cutover metrics approved |
| 5 | Security and QA hardening contract | `13_qa_devops_and_risks.md`, `05_system_architecture.md` | Escalation tests, audit requirements, and rollback triggers documented |
| 6 | Transitional conflict reconciliation | `README.md`, `docs/scholarai/README.md`, legacy docs notes | Canonical precedence markers added and conflicts resolved |
| 7 | Implementation task pack | `12_execution_plan.md`, `IMPLEMENTATION_STATUS_REPORT.md` | Week-by-week owner tasks and acceptance criteria frozen |
| 8 | Controlled rollout and deprecation | `12_execution_plan.md`, `14_future_roadmap.md` | Legacy role-only path removal date and post-cutover checks approved |

### Non-Negotiable Acceptance Signals
1. No endpoint remains without a documented capability requirement.
2. Unauthorized and cross-institution access denial behavior is specified and testable.
3. Compatibility window has explicit start, cutover, and deprecation milestones.
4. Legacy docs that conflict with canonical contracts contain a clear transition note.
5. Documentation updates are approved before broad implementation commits.

## v0.1 decision
The full canonical documentation pack now exists and defines product, scope, design, data, architecture, evaluation, execution, QA, and roadmap before application code changes.

## Deferred items
- Physical archive/removal operations for legacy docs.
- Diagram rewrites and terminology normalization across all legacy files.

## Assumptions
- Existing legacy docs remain readable and available during migration passes.
- Team will review archive/removal proposals before destructive actions.
- Current repository architecture defaults in `.codex/AGENTS.md` remain authoritative.

## Risks
- Keeping legacy docs active for too long can cause scope drift and conflicting implementation decisions.
- If old and new docs are both treated as authoritative, team coordination errors are likely.
- Delayed normalization of API/schema docs can propagate inconsistent naming into implementation.

