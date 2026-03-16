# ScholarAI Demo Readiness Audit

## Purpose
This document records the current demo readiness of the repository based on the implemented codebase, local run surface, and MVP constraints. It is operational, not aspirational.

## Working demo flows
1. Signup and login with token-backed session handling.
2. Public scholarship browse and scholarship detail views over published records only.
3. Authenticated dashboard access with saved opportunities.
4. Profile save flow feeding published recommendation results.
5. Recommendation shortlist with deterministic explanation panels.
6. Document assistance submission and structured feedback foundation.
7. Interview practice session flow with rubric-based scoring.
8. Curator dashboard with `raw`, `validated`, `published`, and unpublish actions.
9. Manual raw-record import into the curation queue.

## What is stable enough for a local demo
| Area | Current state |
|---|---|
| Auth and protected pages | Usable for MVP demo |
| Dashboard shell | Usable for MVP demo |
| Public scholarship browse and detail flow | Usable for MVP demo after a fresh frontend restart or rebuild |
| Seeded published recommendation flow | Usable once the migration-driven bootstrap path is run |
| Document feedback shell | Usable as a bounded MVP workflow |
| Interview practice shell | Usable as a bounded MVP workflow |
| Curator review shell | Usable for internal admin demo |
| Manual raw import into curation | Usable for internal admin demo |

## Final internal verification for this pass
1. `http://localhost:8000/health` returned a healthy response.
2. `http://localhost:3000/scholarships` returned `200` after a clean frontend rebuild.
3. `tests/e2e/playwright/public_scholarship_browse_smoke.py` passed after the frontend rebuild.

## Missing or weak points
| Gap | Why it matters |
|---|---|
| Only the first Alembic revision exists so far | Schema evolution is not fully exercised yet |
| Frontend/browser verification is not regularly executed in this repo | Demo confidence remains partially manual |
| Search and browse discovery baseline is still narrow | Student-facing discovery remains intentionally constrained to a simple published-record browse surface |
| Route-level frontend changes require a clean restart to avoid stale 404s in an already-running dev process | Demo rehearsals can produce false failures if the frontend is not rebuilt or restarted |

## Highest-risk demo blockers
1. If migrations and seed bootstrap are not applied, the app will not be demo-ready.
2. If Node or Python dependencies are missing locally, browser-level verification and app startup will fail.
3. If the frontend server was already running before route-level changes were pulled, the new pages may not be visible until the process is restarted.
4. The repo still depends on a manual local demo checklist rather than a complete end-to-end automated rehearsal.

## External demo recommendation
For an external or thesis-facing demo, do not present the project unless:
1. Docker Compose or direct local startup has been rehearsed from a clean environment.
2. The migration and seed bootstrap path has been run successfully.
3. The auth, dashboard, recommendation, document, interview, and curator smoke flows have been manually checked.

## Immediate pre-demo checklist
1. Copy the correct env example and confirm no secrets are committed.
2. Start Postgres and Redis.
3. Run the migration and seed bootstrap script or the Docker Compose stack.
4. Restart or rebuild the frontend if route-level changes were pulled since the last run.
5. Verify `/health` responds and the frontend loads.
6. Run `backend/scripts/rehearse_seeded_demo.py` for API-level verification or `tests/e2e/playwright/rehearse_seeded_demo.py` for browser-level rehearsal.
7. Verify public browse/detail, document feedback, interview practice, and curation access.

## MVP decision
ScholarAI is close to a presentable internal MVP demo, with a migration-driven bootstrap path now available, but still requires rehearsal discipline before external presentation.

## Deferred items
- Multi-revision migration coverage and rollback rehearsal.
- Fully automated browser verification in CI.
- Richer deployment packaging beyond local/demo scope.

## Assumptions
- Demo environments will remain local or Docker Compose based.
- The team can rehearse the checklist before presenting externally.
- Seeded demo data remains acceptable until a real ingestion-fed corpus is available.

## Risks
- A clean machine run can still fail if the bootstrap step is skipped.
- Browser-level regressions can slip through because local dependencies are not always installed.
- External demos remain vulnerable until the discovery and scholarship detail path is completed.
