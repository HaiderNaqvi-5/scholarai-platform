# ScholarAI QA, DevOps, And Risks

## Purpose
This document defines the MVP quality strategy, local and CI workflows, deployment baseline, operational safeguards, and the risk register used to keep delivery realistic.

## QA And Test Strategy
### Test layers
| Layer | Purpose |
|---|---|
| Unit tests | Verify local module behavior and rule logic |
| Integration tests | Verify DB, API, curation, and recommendation flows |
| End-to-end tests | Verify user-critical product paths |
| Data validation tests | Catch parser and normalization regressions |
| Model evaluation tests | Catch ranking or explanation regressions |
| Manual acceptance tests | Validate demo readiness and user-facing quality |

## Unit Testing
| Target | Examples |
|---|---|
| Schema validation | requirement parsing, deadline parsing, normalization helpers |
| Recommendation logic | rule evaluation, candidate filtering, score formatting |
| Explanation formatting | rationale payload shape, warning generation |
| Document workflows | chunk selection, citation formatting |
| Interview workflows | rubric scoring structure, session state handling |

## Integration Testing
| Flow | What to verify |
|---|---|
| Curation lifecycle | `raw` -> `validated` -> `published` transitions |
| Scholarship detail reads | only published records are surfaced |
| Recommendation request | rule filtering, retrieval, and explanation contract |
| Document feedback | upload metadata, retrieval grounding, structured response |
| Admin actions | audit logging and protected access |

## Authorization And Scope Isolation Test Pack
### Required RBAC test classes
| Test class | Purpose |
|---|---|
| Capability allow tests | Confirm endpoints succeed only with required capability |
| Capability deny tests | Confirm deny-by-default when mapping is absent |
| Institution scope tests | Confirm university users cannot access cross-institution data |
| Compatibility-window tests | Validate role fallback behavior while capability claims are present |
| Privilege escalation tests | Block unsafe capability combinations and direct bypass attempts |

### Required RBAC acceptance thresholds
1. 100% protected endpoints mapped to at least one explicit capability.
2. 100% cross-institution negative tests pass for university-scoped endpoints.
3. 0 unresolved legacy-claim mismatch alerts at cutover decision point.
4. 100% privileged mutation actions emit auditable events.

### Current automated RBAC coverage (implemented)
- `backend/tests/unit/test_rbac_dependencies.py`
	- token capability precedence over role fallback
	- role fallback behavior when token capability claim is absent
- `backend/tests/unit/test_auth_claim_enforcement.py`
	- rejects malformed `capabilities` claims
	- rejects scope mismatch and missing university scope claims
- `backend/tests/unit/test_authorization_matrix.py`
	- capability matrix integrity checks and baseline hierarchy checks
- `backend/tests/unit/test_institution_scope_enforcement.py`
	- university users require institution scope
	- cross-institution source access is denied in curation/ingestion
- `backend/tests/integration/test_authorization_denials.py`
	- route-level 401 and 403 deny-path assertions for protected endpoints

## End-To-End Testing
### MVP user-critical paths
1. Search and filter scholarships.
2. Open scholarship detail and inspect validated facts.
3. Request recommendations and inspect explanation panels.
4. Upload a document and receive grounded feedback.
5. Start an interview practice session and receive rubric output.
6. Review and publish a scholarship through the admin flow.

## Data Validation Tests
| Test type | Purpose |
|---|---|
| Parser field presence tests | Ensure required fields survive extraction |
| Normalization tests | Keep country, degree, and field mappings consistent |
| Deduplication tests | Prevent duplicate publication |
| Scope tests | Block non-MVP geography leakage |
| Provenance tests | Ensure source and run references are preserved |

## Model Evaluation Tests
| Test type | Purpose |
|---|---|
| Offline ranking regression | Compare baseline metrics across judged-set snapshots |
| Constraint violation test | Ensure ineligible records do not slip into results |
| Explanation consistency check | Keep explanation payloads stable for similar inputs |
| Retrieval relevance spot checks | Ensure top chunks are usable for document assistance |

## Manual Acceptance Testing
Use a fixed checklist before demos and milestone signoff:
- published scholarship facts are visible and source-backed
- recommendations show estimated scores, not predictive claims
- document feedback shows citations and scope limits
- interview feedback is structured and non-authoritative
- admin actions create visible audit trail

## Local Setup
### MVP baseline
- Docker Compose for local multi-service startup
- `.env.example` for documented environment variables
- local PostgreSQL, Redis, backend, frontend, and worker services

### Local developer expectations
- one-command environment startup
- seeded example data for core flows
- documented test commands

## Environments
| Environment | Purpose |
|---|---|
| Local | day-to-day development |
| Demo / staging | integration rehearsal and evaluation runs |
| Production-like thesis demo | final packaged environment for presentation |

Limited budget means MVP should avoid a large environment matrix.

## CI/CD
### CI baseline
- documentation checks
- backend lint and tests
- frontend lint and tests
- basic integration checks

### CD baseline
- manual promotion to demo environment
- no automatic production rollout required for MVP

## Rollback Strategy
| Layer | Rollback approach |
|---|---|
| Application deploy | Revert to previous image or commit |
| Database migrations | Use reviewed down-migration path where safe, otherwise restore from backup |
| Published scholarship records | Unpublish and restore last validated state |
| Model artifact | Pin previous stable scorer and explanation formatter |

### RBAC rollback additions
1. Keep role fallback feature flag available until post-cutover stability is proven.
2. If authorization mismatches spike, restore dual-evaluator mode before broad rollback.
3. If scope isolation fails, disable university-scoped mutation endpoints until patched.

## Observability Basics
### Minimum signals
- structured application logs
- request IDs
- background task status
- ingestion run summaries
- health endpoints for frontend, backend, DB connectivity, and worker queue

### RBAC observability signals
- authorization denials by capability key and endpoint
- legacy fallback invocation count during compatibility window
- cross-institution deny events grouped by actor and institution
- privileged action audit completeness checks

This is enough for MVP without building a heavy observability stack.

## Secrets Handling
1. Keep secrets out of the repo.
2. Use environment variables and documented secret injection paths.
3. Separate local development secrets from demo deployment secrets.
4. Rotate API keys used for document assistance or interview workflows if exposed.

## Risk Register
| Risk | Probability | Impact | Mitigation | Owner |
|---|---|---|---|---|
| Data quality is weaker than expected | Medium | High | keep corpus narrow and curator-reviewed | A |
| Recommendation quality lags | Medium | High | ship rules + retrieval fallback | B |
| AI provider instability or cost spikes | Medium | Medium | degrade gracefully and keep bounded prompts | B |
| Frontend polish takes longer than planned | Medium | Medium | focus on core flows and reuse design system tokens | C |
| Evaluation recruitment is late | Medium | High | prepare pilot materials early in Phase 3 | All |
| Scope creep from deferred features | High | High | enforce doc-based scope gate | All |

## Fallback Delivery Plan
### If schedule slips
- keep discovery, detail, curation, and rules-first recommendation flows intact
- keep explanation panel simple but present
- keep document assistance limited to core grounded feedback
- fall back to text-only interview practice

### What gets cut first
1. Audio interview support
2. richer admin analytics
3. broader model family comparisons
4. non-essential visual flourishes

### What must remain no matter what
1. `raw` -> `validated` -> `published` curation pipeline
2. published scholarship discovery and detail pages
3. rules-first recommendation baseline
4. explicit source-of-truth separation between validated facts and generated guidance

## DevOps Delivery Posture
### MVP
- simple local-first Docker Compose setup
- minimal CI gates
- manual demo promotion

### Future Research Extensions
- stronger experiment-tracking infrastructure if justified
- richer monitoring for large evaluation runs

### Post-MVP Startup Features
- automated deployment pipelines
- more advanced observability and alerting
- stronger secrets and environment isolation

## MVP decision
ScholarAI MVP will use a lean QA and DevOps approach centered on local reproducibility, essential CI checks, manual promotion, and explicit fallback rules that preserve the data and recommendation core.

## Deferred items
- Full production-grade observability stack.
- Fully automated deployment promotion.
- Broad performance testing beyond MVP-critical paths.

## Assumptions
- Docker Compose is sufficient for development and demo deployment.
- Manual demo promotion is acceptable within the project constraints.
- The team can maintain a regression checklist across core user and admin flows.

## Risks
- Weak regression discipline can break trust-critical flows late in the project.
- Manual deployment steps can introduce demo-day mistakes if not rehearsed.
- If fallback cuts are not decided early, schedule pressure will produce chaotic scope reduction.
