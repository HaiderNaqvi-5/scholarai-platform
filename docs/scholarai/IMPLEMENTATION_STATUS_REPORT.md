# ScholarAI Implementation Status Report

## Current Implementation Snapshot
ScholarAI is no longer documentation-only. The repository now contains a working modular-monolith MVP foundation with live auth, profile persistence, published scholarship reads, seeded recommendations, saved opportunities, document assistance, interview practice, curator workflow, migration-driven bootstrap, and demo rehearsal scripts. The central student journey is partly real, but discovery breadth, scholarship detail UX, ingestion automation, and several contract/polish layers are still incomplete.

## Implemented Features
### Backend and platform foundation
| Area | Current implementation evidence |
|---|---|
| FastAPI modular monolith entrypoint | `backend/app/main.py`, `backend/app/api/v1/__init__.py` |
| Migration-driven bootstrap | `backend/alembic/versions/20260316_0001_initial_schema.py`, `backend/scripts/bootstrap_local.py` |
| Seeded demo dataset | `backend/app/demo/demo_dataset.py`, `backend/app/demo/seed.py` |
| Local API rehearsal script | `backend/scripts/rehearse_seeded_demo.py` |
| Minimal CI sanity | `.github/workflows/ci.yml` |

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
| Public published scholarship reads | `backend/app/api/v1/routes/scholarships.py` |
| Recommendation API and deterministic explanation payload | `backend/app/api/v1/routes/recommendations.py`, `backend/app/services/recommendations/eligibility.py`, `backend/app/services/recommendations/service.py` |
| Recommendation workspace UI | `frontend/src/components/recommendations/recommendation-workspace.tsx` |
| Saved opportunities | `backend/app/api/v1/routes/saved_opportunities.py`, `backend/app/services/saved_opportunities/service.py`, `frontend/src/components/dashboard/dashboard-shell.tsx` |
| Dashboard shell | `frontend/src/components/dashboard/dashboard-shell.tsx` |

### Preparation tools
| Area | Current implementation evidence |
|---|---|
| Document submission and bounded feedback foundation | `backend/app/api/v1/routes/documents.py`, `backend/app/services/documents/service.py`, `frontend/src/components/documents/document-assistance-shell.tsx` |
| Interview session flow and rubric scoring | `backend/app/api/v1/routes/interview.py`, `backend/app/services/interview/scoring.py`, `backend/app/services/interview/service.py`, `frontend/src/components/interview/interview-practice-shell.tsx` |

### Internal curation and governance
| Area | Current implementation evidence |
|---|---|
| Raw / validated / published state handling | `backend/app/models/models.py`, `backend/app/services/curation/service.py` |
| Curator review, edit, approve, reject, publish, unpublish actions | `backend/app/api/v1/routes/curation.py`, `frontend/src/components/curation/curation-dashboard-shell.tsx` |
| Audit-log foundation | `backend/app/models/models.py` |

### Tests and demo checks
| Area | Current implementation evidence |
|---|---|
| Backend unit and integration tests | `backend/tests/unit/`, `backend/tests/integration/` |
| Browser smoke artifacts | `tests/e2e/playwright/` |
| Full seeded demo browser rehearsal | `tests/e2e/playwright/rehearse_seeded_demo.py` |

## Partially Implemented Features
| Feature | What exists | What is still missing |
|---|---|---|
| Scholarship discovery experience | Public `GET /api/v1/scholarships` and `GET /api/v1/scholarships/{id}` plus a dashboard snapshot | No dedicated browse/search UI, no scholarship detail page in the frontend, and no richer filter UX |
| Core student journey | Signup -> profile -> recommendations -> save opportunity works in rehearsal scripts | The main browse -> detail -> compare -> save journey is still thinner than the dashboard-driven flow |
| Recommendation system | Deterministic rules-first ranking with match summaries, criteria, and constraints | No vector retrieval, no graph-aware filtering implementation, no ML reranking, no evaluation tooling wired into runtime |
| Document assistance | Submission, processing state, recent drafts, structured feedback, limitation notice | No bounded retrieval layer, no scholarship-specific grounding from validated records, no async job orchestration for larger workloads |
| Interview practice | Fixed session lifecycle, structured rubric, results view, stored responses | No scholarship-specific prompts, no adaptive interviewer behavior, no voice path, no richer history/analytics |
| Curation workflow | Internal dashboard and explicit state transitions on scholarship records | No upstream ingestion run workflow creating raw records from real sources, no queue assignment or bulk operations |
| DevOps readiness | Docker Compose, env examples, bootstrap script, CI sanity workflow | No browser automation in CI, no richer deployment packaging, no rollback rehearsal beyond local demo reset |

## Scaffolded-Only Features
| Feature | Evidence | Why it is scaffold-only |
|---|---|---|
| Onboarding route | `frontend/src/app/onboarding/page.tsx` | Informational shell only; no real intake flow beyond the profile form |
| Worker layer | `workers/README.md`, `backend/app/tasks/` | Celery exists, but real ingestion/document async workloads are not implemented |
| Shared package layer | `shared/README.md`, `shared/contracts/README.md` | Documentation scaffolding only; no active shared runtime package |
| Infra notes | `infra/README.md`, `infra/docker/README.md` | Guidance exists, but this is not a real infra management layer |
| Some legacy backend services and routes | `backend/app/services/recommendation_service.py`, `backend/app/services/scraper_service.py`, `backend/app/api/v1/routes/admin.py`, `backend/app/api/v1/routes/ai.py`, `backend/app/api/v1/routes/profile.py` | Present on disk but not part of the active mounted MVP surface |

## Not Implemented Yet
### Remaining MVP work
| Feature | Gap |
|---|---|
| Frontend scholarship detail page | No student-facing detail route or page implementation |
| Frontend browse/search/filter experience | Discovery UI is still thin and mostly dashboard/recommendation driven |
| Real ingestion automation | No Playwright/Pandas/Pydantic ingestion pipeline creating raw records from live sources |
| Raw-record source review pipeline | No explicit ingestion-run model or import queue feeding curation |
| Standardized API error envelope | Docs define one; active API still mostly uses FastAPI default error shape |
| Consistent list envelope contract | Some endpoints use `{ items: ... }`, but scholarship list still returns a raw array |
| Multi-revision migration history | Only the first Alembic revision exists |
| Automated browser checks in CI | Smoke scripts exist locally only |

### Future Research Extensions
| Feature | Status |
|---|---|
| Graph-layer experimentation | Not implemented |
| ML reranking and ablation studies | Not implemented |
| Larger judged-set evaluation and explainability study tooling | Not implemented |
| DAAD and broader provider expansion | Deferred |

### Post-MVP Startup Features
| Feature | Status |
|---|---|
| Broad geography coverage | Deferred |
| Marketplace / mentor workflows | Deferred |
| Partner-facing APIs and provider-submitted data flows | Deferred |
| Institution-facing analytics | Deferred |

## MVP Blockers
1. The browse and scholarship-detail experience is still incomplete on the frontend.
2. Real ingestion is missing, so curation currently depends on seeded or manually present records rather than a true raw-data pipeline.
3. API contracts still diverge from the docs in places, especially around error envelopes and list response consistency.
4. Browser-level verification is not yet part of CI, so demo confidence still depends on local rehearsal discipline.
5. Only the first migration exists; schema evolution discipline is started but not yet fully exercised.

## Documentation Alignment Notes
### Where implementation matches docs
- Modular monolith architecture is real.
- Canada-first, MS-only, Fulbright-limited US scope is enforced in the active seeded flow.
- Structured published data is the user-facing source of truth.
- Document assistance and interview practice remain bounded, non-authoritative support tools.
- Curation states `raw`, `validated`, and `published` are implemented and enforced.

### Where implementation diverges from docs
- `docs/scholarai/10_backend_api_and_repo.md` still describes a fuller contract than the code currently exposes:
  - `profiles` naming instead of active `/profile` routes
  - standard error envelope not yet implemented
  - list envelope consistency not yet achieved for scholarship reads
  - `admin` module described as active, but the mounted internal workflow is currently concentrated in `curation`
- `docs/scholarai/02_prd_and_scope.md` assumes browse and detail as fully realized MVP surfaces, while the repo still relies more heavily on dashboard and recommendation flows for demos.

## Legacy Docs Or Files That Should Be Archived Or Rewritten Later
| File | Recommendation | Reason |
|---|---|---|
| `docs/PRD.md` | Archive after final extraction | Canonical PRD already exists in `docs/scholarai/02_prd_and_scope.md` |
| `docs/architecture.md` | Archive after final extraction | Canonical architecture already exists; legacy wording risks drift |
| `docs/architecture_diagrams.md` | Rewrite or archive | Likely stale against the current MVP implementation |
| `docs/database_schema.md` | Archive after final extraction | Canonical data model now lives in `docs/scholarai/06_data_models.md` plus Alembic migration |
| `docs/api_design.md` | Rewrite or archive | Conflicts with actual route shape and current module naming |
| `docs/research.md` | Rewrite or archive | Canonical evaluation and roadmap docs exist now |
| `docs/phase_status_report.md` | Archive | Snapshot-style legacy reporting is superseded by this report |
| `backend/app/api/v1/routes/admin.py` and related legacy routes | Quarantine and archive later | Present on disk but not part of the active mounted API surface |
| `backend/app/services/recommendation_service.py`, `scraper_service.py`, `sop_service.py`, `interview_service.py` | Quarantine and archive or refactor | Legacy service layer conflicts with the active modular service packages |

## Recommended Next 3 Implementation Priorities
1. Build the student-facing browse and scholarship-detail path.
   - Add a real discovery page, filters, and a scholarship detail page using the already-public scholarship routes.
2. Implement the upstream ingestion-to-curation path.
   - Create the narrow raw-record import workflow so the curator dashboard is fed by real ingestion state instead of only seeded records.
3. Tighten API contract consistency.
   - Add the documented error envelope and normalize list response patterns so backend behavior matches `10_backend_api_and_repo.md`.

## MVP decision
ScholarAI currently has a real MVP foundation and multiple working slices, but it still needs discovery/detail completion, ingestion realism, and contract cleanup before it should be considered a fully coherent MVP.

## Deferred items
- Broader ML, RAG, graph experimentation, and startup-scale platform features.
- Rich deployment and observability work beyond the current local/demo baseline.
- Bulk admin analytics and queue-management depth.

## Assumptions
- The current mounted route set and running local demo path represent the intended active implementation surface.
- Legacy backend route and service files on disk are not treated as active product scope unless they are wired into `backend/app/api/v1/__init__.py`.
- Seeded demo data remains the current stand-in for a true ingestion-driven corpus.

## Risks
- Stale legacy code on disk can mislead future contributors about what is active.
- Documentation can drift again if route-contract fixes are not reflected in canonical docs.
- The project may appear more complete than it is if the demo path is mistaken for full discovery coverage.
