# ScholarAI Implementation Status Report

## Current Implementation Snapshot
ScholarAI now has a real internal v0.1 SLC path rather than only isolated slices. The repository supports public published-scholarship discovery and detail views, authenticated profile and recommendation flows, saved opportunities, document assistance, interview practice, curator review, source-registry ingestion runs, migration-driven bootstrap, and browser smoke coverage in CI. Phase 2 now adds scholarship-grounded bounded guidance for Documents and Interviews with explicit separation of facts, retrieved guidance, generated guidance, and limitations while keeping Canada-first scope fixed. The largest remaining implementation gaps are broader ingestion coverage, recommendation evaluation/tuning, and cleanup of intentionally thin non-core layers.

## Active Documentation-First Implementation Track
The current implementation pass has started locally with a docs-first RBAC expansion covering:
1. capability-based authorization matrix
2. six-role bundle model (`ENDUSER_STUDENT`, `INTERNAL_USER`, `DEV`, `ADMIN`, `UNIVERSITY`, `OWNER`)
3. institution-scoped university access rules
4. compatibility-window migration from legacy role claims to capability claims

This track is in-progress at contract and governance documentation level before broad code changes.

Current local rollout status:
- Backend capability dependencies, claim validation, and institution-scope controls are implemented.
- Frontend route-level and navigation-level capability checks are implemented.
- Frontend component-level action controls inside curation and mentor dashboards are in progress (button-level gating pass active).
- Owner governance now includes access-control operations for managed-user listing, role updates, and audited role reverts (`/api/v1/access-control/*`) surfaced in the owner home.

## Implemented Features
### Backend and platform foundation
| Area | Current implementation evidence |
|---|---|
| FastAPI modular monolith entrypoint | `backend/app/main.py`, `backend/app/api/v1/__init__.py` |
| Migration-driven bootstrap | `backend/alembic/versions/20260316_0001_initial_schema.py`, `backend/alembic/versions/20260316_0002_ingestion_runs.py`, `backend/scripts/bootstrap_local.py` |
| Seeded demo dataset and demo users | `backend/app/demo/demo_dataset.py`, `backend/app/demo/seed.py` |
| Local API rehearsal script | `backend/scripts/rehearse_seeded_demo.py` |
| CI sanity plus browser smoke gate | `.github/workflows/ci.yml` |

### Auth and session flow
| Area | Current implementation evidence |
|---|---|
| Register, login, current user, refresh | `backend/app/api/v1/routes/auth.py` |
| Access-token protection and refresh handling | `backend/app/core/dependencies.py`, `backend/app/core/security.py`, `backend/app/services/auth/service.py` |
| Frontend auth state and session persistence | `frontend/src/components/auth/auth-provider.tsx` |
| Protected route guards | `frontend/src/components/auth/protected-route.tsx`, `frontend/src/components/auth/admin-route.tsx` |
| Auth screens | `frontend/src/app/login/page.tsx`, `frontend/src/app/signup/page.tsx` |

### Student-facing product slices
| Area | Current implementation evidence |
|---|---|
| Landing page and app shell | `frontend/src/app/page.tsx`, `frontend/src/components/layout/marketing-shell.tsx`, `frontend/src/components/layout/app-shell.tsx` |
| Profile save and load flow | `backend/app/api/v1/routes/students.py`, `backend/app/services/students/service.py`, `frontend/src/components/profile/profile-form-shell.tsx` |
| Functional onboarding route | `frontend/src/app/onboarding/page.tsx` |
| Public scholarship browse, search, filters, and detail | `backend/app/api/v1/routes/scholarships.py`, `frontend/src/components/scholarships/scholarship-browse-shell.tsx`, `frontend/src/components/scholarships/scholarship-detail-shell.tsx` |
| Recommendation API and stage-aware explanation payload | `backend/app/api/v1/routes/recommendations.py`, `backend/app/services/recommendations/eligibility.py`, `backend/app/services/recommendations/service.py` |
| Recommendation workspace UI | `frontend/src/components/recommendations/recommendation-workspace.tsx` |
| Saved opportunities | `backend/app/api/v1/routes/saved_opportunities.py`, `backend/app/services/saved_opportunities/service.py`, `frontend/src/components/dashboard/dashboard-shell.tsx` |
| Dashboard shell | `frontend/src/components/dashboard/dashboard-shell.tsx` |

### Preparation tools
| Area | Current implementation evidence |
|---|---|
| Document submission and scholarship-grounded bounded feedback | `backend/app/api/v1/routes/documents.py`, `backend/app/schemas/documents.py`, `backend/app/services/documents/service.py`, `frontend/src/components/documents/document-assistance-shell.tsx` |
| Interview mode-aware sessions, adaptive rubric flow, and summary outputs | `backend/app/api/v1/routes/interview.py`, `backend/app/schemas/interviews.py`, `backend/app/services/interview/scoring.py`, `backend/app/services/interview/service.py`, `frontend/src/components/interview/interview-practice-shell.tsx` |

### Phase 2 API Surface (Documents + Interviews, Canada-first Fixed)
| Endpoint | Phase 2 update |
|---|---|
| `POST /api/v1/documents` | Accepts optional scholarship grounding identifiers. |
| `POST /api/v1/documents/{id}/feedback` | Returns explicit grounded-context partitions for validated scholarship facts, retrieved writing guidance, generated guidance, and limitations. |
| `POST /api/v1/interviews` | Accepts `practice_mode` plus optional `scholarship_id`. |
| `GET /api/v1/interviews/{id}` | Returns session history summary and rubric trend summary for adaptive follow-up logic. |
| Validation behavior | Invalid scholarship grounding identifiers fail cleanly with structured errors. |

### Internal curation and ingestion
| Area | Current implementation evidence |
|---|---|
| Raw / validated / published state handling | `backend/app/models/models.py`, `backend/app/services/curation/service.py` |
| Curator review, edit, approve, reject, publish, unpublish actions | `backend/app/api/v1/routes/curation.py`, `frontend/src/components/curation/curation-dashboard-shell.tsx` |
| Source-registry ingestion runs that create raw records | `backend/app/services/ingestion/service.py`, `backend/app/tasks/scraper_tasks.py` |
| Audit-log foundation | `backend/app/models/models.py` |

### Tests and demo checks
| Area | Current implementation evidence |
|---|---|
| Backend unit and integration tests | `backend/tests/unit/`, `backend/tests/integration/` |
| Browser smoke artifacts | `tests/e2e/playwright/` |
| Full seeded demo browser rehearsal | `tests/e2e/playwright/rehearse_seeded_demo.py` |
| Independent smoke-suite runner | `tests/e2e/playwright/run_smoke_suite.py` |

## Partially Implemented Features
| Feature | What exists | What is still missing |
|---|---|---|
| Scholarship discovery experience | Public browse, query, field filter, deadline window, sort, save actions, and detail page | Filtering is still narrow and corpus-aware rather than broad search/discovery depth |
| Core student journey | Public browse -> detail plus signup -> profile -> recommendations -> save now works, with tracker status transitions for saved/in-progress/applied/closed reflected on the student dashboard | Compare workflows, deeper search refinement, and stronger action-planning surfaces are still thin |
| Recommendation system | Phase 1 pipeline active: relational eligibility graph abstraction, pgvector retrieval over published scholarships, calibrated heuristic rerank factors (guardrail floor/cap + policy version), stage-aware rationale, rules-only fallback parity, plus benchmark dataset registry with multiple judged datasets, benchmark list/evaluate APIs, KPI snapshot recording, and MRR@K instrumentation | Online drift automation and richer calibration analytics remain incomplete |
| Document assistance | Submission, processing state, recent drafts, scholarship-grounded bounded feedback, limitation notice, expanded bounded guidance retrieval across category/country/degree/field dimensions, and denser scholarship+guidance citations in feedback | No async larger-job orchestration yet |
| Interview practice | Practice-mode selection, scholarship-targeted sessions, adaptive weakest-dimension follow-up, structured rubric, results view, stored responses, history/trend summary, long-horizon coaching analytics aggregates, and deterministic action-plan items with measurable targets | No voice path and no AI-generated longitudinal intervention automation yet |
| Ingestion pipeline | Source-registry run model, capture path, parsing, raw-record creation, worker hook, run retry API/UI controls, diagnostics-filtered run history, queue assignment, bulk retry operations, and captured HTML snapshot management exist | Parser coverage remains heuristic and narrow, and deeper parser resilience remains incomplete |
| API contracts | Shared error envelope and list envelopes are active across the mounted list routes | Detail responses, pagination metadata, and route naming still do not match the target docs perfectly |
| DevOps readiness | Docker Compose, env examples, migration bootstrap, CI sanity, and browser smoke gate exist | Release management, rollback drills, and stronger production-like hardening remain incomplete |

## Scaffolded-Only Features
| Feature | Evidence | Why it is still scaffold-only |
|---|---|---|
| Shared package layer | `shared/README.md`, `shared/contracts/README.md` | Documentation scaffolding only; no active shared runtime package |
| Infra notes | `infra/README.md`, `infra/docker/README.md` | Guidance exists, but this is not a real infra management layer |

## Not Implemented Yet
### Remaining v0.1 SLC work
| Feature | Gap |
|---|---|
| Recommendation quality evaluation instrumentation | Versioned benchmark registry and benchmark evaluation endpoints now exist (`GET /api/v1/recommendations/benchmarks`, `POST /api/v1/recommendations/benchmarks/{dataset_id}/evaluate`); continuous online drift monitoring remains incomplete |
| Rerank calibration and guardrail tuning | Benchmark thresholds and gate evaluation now run against judged datasets, but ongoing calibration operations and alerting loops remain incomplete |
| Multi-source grounding depth in preparation tools | Grounded context exists but not all guidance items are citation-dense across broader scholarship coverage |
| Long-horizon interview coaching analytics | Session-level trend summary exists, but richer multi-session coaching plans are not implemented yet |
| Richer ingestion review controls | Run retry, run diagnostics filtering, queue assignment, and bulk retry operations are now implemented; captured HTML snapshot management remains open |
| Fully unified API contract | Route naming, pagination metadata, and some envelope details still diverge from `10_backend_api_and_repo.md` |
| v0.1 role-home completeness | Student, admin, owner, mentor, and test-user constrained home surfaces are now implemented and mapped in the acceptance checklist artifacts |

### Future Research Extensions
| Feature | Status |
|---|---|
| Graph-layer experimentation | Not implemented |
| ML reranking and ablation studies | Not implemented |
| Larger judged-set evaluation and explainability study tooling | Not implemented |
| DAAD and broader provider expansion | Deferred |

### Deferred By Stage
| Feature | Status |
|---|---|
| Broad geography coverage | Deferred |
| Marketplace / mentor workflows | Deferred |
| Partner-facing APIs and provider-submitted data flows | Deferred |
| Institution-facing analytics | Deferred |
| Tenant-aware admin or commercial partitioning | Deferred |

## v0.1 SLC Blockers
1. The ingestion path now exists, but it is still too heuristic and narrow to count as a mature trusted-data pipeline.
2. Recommendation depth now covers the Phase 1 runtime pipeline, but evaluation and calibration depth are still below the full target in `08_recommendation_and_ml.md`.
3. Document and interview tools now provide scholarship-grounded bounded guidance, but broader grounding depth and advanced coaching coverage are still below the full target workflow.
4. Shared and infra layers remain intentionally thin, so maintainability relies on discipline rather than stronger packaging boundaries.

## Documentation Alignment Notes
### Where implementation matches docs
- Modular monolith architecture is real.
- Canada-first, MS-only, Fulbright-limited US scope is enforced in the active discovery and recommendation flow.
- Structured published data is the user-facing source of truth.
- Document assistance and interview practice remain bounded, non-authoritative support tools.
- Documents and interviews now expose explicit grounded-context separation and mode-aware API behavior for scholarship-linked preparation.
- Curation states `raw`, `validated`, and `published` are implemented and enforced.
- A real source-registry ingestion run path now exists.

### Where implementation still diverges from docs
- `docs/scholarai/10_backend_api_and_repo.md` still uses the conceptual module label `profiles` while implementation routes are mounted from `students.py` under `/profile` (with `/profiles` alias).
- The docs describe a fuller recommendation pipeline than the current rules-first runtime implementation exposes.
- The docs describe a richer ingestion stack and queue model than the current heuristic v0.1 SLC ingestion run path.

## Legacy Docs Or Files That Should Be Archived Or Rewritten Later
| File | Recommendation | Reason |
|---|---|---|
| `docs/PRD.md` | Archive after final extraction | Canonical PRD already exists in `docs/scholarai/02_prd_and_scope.md` |
| `docs/architecture.md` | Archive after final extraction | Canonical architecture already exists; legacy wording risks drift |
| `docs/architecture_diagrams.md` | Rewrite or archive | Likely stale against the current v0.1 SLC implementation |
| `docs/database_schema.md` | Archive after final extraction | Canonical data model now lives in `docs/scholarai/06_data_models.md` plus Alembic migrations |
| `docs/api_design.md` | Rewrite or archive | Conflicts with actual route shape and current module naming |
| `docs/research.md` | Rewrite or archive | Canonical evaluation and roadmap docs exist now |
| `docs/phase_status_report.md` | Archive | Snapshot-style legacy reporting is superseded by this report |
| `backend/legacy/` | Keep quarantined until archive/refactor pass | Inactive backend code was moved out of the active app tree to reduce implementation drift |

## Recommended Next 3 Implementation Priorities
1. Expand grounding depth beyond the current bounded guidance library and increase citation density across broader scholarship coverage.
2. Expand recommendation benchmark dataset coverage and calibrate rerank weights with judged samples.
3. Strengthen ingestion coverage with richer parsers and captured HTML snapshot management.

## SLC decision (v0.1)
ScholarAI now has a coherent internal v0.1 SLC path with real browse, profile, recommendation, preparation, curation, ingestion, migration, and CI smoke flows, but it still needs deeper recommendation and preparation fidelity before it should be treated as a fully mature v0.1 SLC foundation.

## Deferred items
- Broader ML, RAG, graph experimentation, and startup-scale platform features.
- Rich deployment and observability work beyond the current internal/demo baseline.
- Bulk admin analytics and queue-management depth.

## Assumptions
- The current mounted route set and running local demo path represent the intended active implementation surface.
- `backend/legacy/` is preserved for traceability, not as active v0.1 SLC behavior.
- The new ingestion run path is the correct narrow bridge between seeded/manual state and broader automated source coverage.

## Risks
- Heuristic ingestion can still create noisy raw records if source pages drift heavily.
- The recommendation pipeline may appear more complete than it is if the current rules-first fallback is mistaken for the full intended ranking stack.
- Documentation can drift again unless the canonical docs are updated alongside future runtime changes.

