# ScholarAI Public-Live Readiness Gap Analysis And Hardening Plan

## Purpose
This document defines the gap between ScholarAI's current internal v0.1 SLC state and a minimally safe public-facing live deployment. It is evidence-based and intentionally conservative.

## Current Internal v0.1 SLC Readiness Summary
ScholarAI is in a credible internal v0.1 SLC state, not a public-live state.

Current strengths:
1. Core v0.1 SLC slices are implemented and locally demoable.
2. Alembic bootstrap plus seeded demo data provides a reproducible internal setup path.
3. Curation state discipline exists in code: `raw`, `validated`, `published`, `archived`.
4. Public scholarship reads are restricted to `published` records.
5. Auth, protected routes, recommendation flow, document assistance, interview practice, and curation all exist in usable narrow forms.

Current posture:
- Acceptable for internal demo: yes
- Acceptable for internal deploy with controlled users: yes, with rehearsal discipline
- Acceptable for public live use: no

## Readiness Classification
### Already acceptable for internal demo
1. Public browse and scholarship detail over published records only.
2. Authenticated dashboard, saved opportunities, and profile flow.
3. Seeded recommendation workflow with bounded explanation.
4. Document assistance and interview practice as bounded guidance tools.
5. Internal curator review and publish workflow.

### Acceptable for internal deploy only
1. Docker Compose startup with example env values.
2. Token-based auth with refresh flow stored in the browser.
3. Manual raw-record import as a bridge into curation.
4. Browser smoke coverage run manually or locally.
5. Seeded data used for rehearsal and internal demos.

### Not acceptable for public live use
1. Default-secret and development-oriented config posture.
2. Stateless refresh-token model without revocation or session invalidation.
3. LocalStorage token storage for a public-facing app.
4. No login throttling, abuse controls, or account verification.
5. No structured production logging or operational monitoring stack.
6. No public-ready privacy, terms, support, or incident-facing content.
7. No automated ingestion-validation chain backing the public corpus.
8. Limited automated browser regression coverage and no public-live deployment safety gates.

## Public-Live Readiness Gaps
### 1. Security
Current evidence:
- [backend/app/core/config.py](../../backend/app/core/config.py) includes a default `SECRET_KEY` and development defaults.
- [.env.example](../../.env.example) is intentionally demo-safe, not production-safe.
- [backend/app/main.py](../../backend/app/main.py) adds CORS and request IDs, but there are no security headers, CSP, HTTPS assumptions, or hardened proxy/deployment settings.

Gap:
- Current security posture is internal-demo-safe, not public-live-safe.

What is missing:
1. Mandatory non-default production secrets.
2. Secure environment separation for demo vs public deployment.
3. Reverse-proxy or edge-layer assumptions for HTTPS and header hardening.
4. Security headers such as CSP, HSTS where appropriate, and stricter origin policy.
5. Basic abuse protection on public/auth endpoints.

### 2. Auth And Session Robustness
Current evidence:
- [frontend/src/components/auth/auth-provider.tsx](../../frontend/src/components/auth/auth-provider.tsx) stores access and refresh tokens in `localStorage`.
- [backend/app/services/auth/service.py](../../backend/app/services/auth/service.py) issues stateless refresh tokens and immediately reissues new ones.
- [backend/app/api/v1/routes/auth.py](../../backend/app/api/v1/routes/auth.py) exposes register, login, refresh, and `/me`, but no account verification, password reset, or device/session invalidation.

Gap:
- Auth is good enough for internal usage, but too soft for public exposure.

What is missing:
1. Refresh-token rotation and revocation strategy.
2. Logout invalidation beyond local client token deletion.
3. Rate limiting or brute-force protection on auth endpoints.
4. Password policy strengthening beyond `min_length=8`.
5. Account verification, password reset, and abuse-resistant account lifecycle.
6. Preferably a move away from public-live `localStorage` token persistence toward safer cookie/session handling.

### 3. Data Quality And Curation Discipline
Current evidence:
- [backend/app/services/curation/service.py](../../backend/app/services/curation/service.py) correctly enforces state transitions.
- [backend/app/api/v1/routes/scholarships.py](../../backend/app/api/v1/routes/scholarships.py) only exposes `published` records.
- Curation still depends on manual raw import and seeded/demo data; the ingestion automation described in docs is not implemented.

Gap:
- The source-of-truth model exists, but the upstream trust pipeline is incomplete.

What is missing:
1. Real ingestion-run records that feed `raw` entries systematically.
2. More explicit provenance and review evidence in the actual admin workflow.
3. Data-quality regression tests tied to publication rules.
4. Safer operational controls around what can be published publicly.
5. A clearer separation between internal seed/demo data and public-live corpus data.

### 4. Error Handling And API Contracts
Current evidence:
- [backend/app/main.py](../../backend/app/main.py) now provides a nested error envelope and request IDs.
- Contract cleanup is partial; not all endpoints are normalized to the same list-envelope style described in [10_backend_api_and_repo.md](../../docs/scholarai/10_backend_api_and_repo.md).
- [frontend/src/lib/api.ts](../../frontend/src/lib/api.ts) parses the current error envelope but UI-level fallback patterns remain uneven.

Gap:
- Better than before, but still not public-facing API quality.

What is missing:
1. Consistent response envelopes across list and error endpoints.
2. Stable public error codes and compatibility rules.
3. Clearer user-facing failure states on all public and authenticated surfaces.
4. A more explicit API versioning and public compatibility posture before external consumers exist.

### 5. Environment And Config Handling
Current evidence:
- [README.md](../../README.md), [backend/.env.example](../../backend/.env.example), and [frontend/.env.local.example](../../frontend/README.md) are good for internal handoff.
- [docker-compose.yml](../../docker-compose.yml) is development-oriented and runs `uvicorn --reload`.

Gap:
- Config is serviceable for internal use, not public release.

What is missing:
1. Public-live env templates separated from local demo examples.
2. Production-safe defaults that fail closed instead of booting with demo-safe values.
3. Non-reload startup commands and deployment-specific compose/runtime guidance.
4. Documented secret injection and rotation process.

### 6. Logging And Monitoring
Current evidence:
- [backend/app/main.py](../../backend/app/main.py) sets request IDs.
- There is a `/health` endpoint.
- There is no actual structured application logging configuration, no metrics, no alerting, and no queue or worker health visibility.

Gap:
- Operational visibility is far below public-live minimum.

What is missing:
1. Structured backend logs with request_id correlation.
2. Error logging for exception paths.
3. Basic worker/task logging and queue health visibility.
4. Minimal deploy monitoring and restart/incident guidance.
5. Public-live runbook for failures.

### 7. Test Coverage
Current evidence:
- [.github/workflows/ci.yml](../../.github/workflows/ci.yml) runs backend unit/integration and frontend lint/typecheck/build.
- Playwright smoke scripts exist under `tests/e2e/playwright/`, but browser coverage is not in CI.
- Security, abuse, and public-live regression scenarios are not meaningfully covered.

Gap:
- Coverage is acceptable for internal v0.1 SLC momentum, not for public launch confidence.

What is missing:
1. CI-executed browser smoke on core public and auth flows.
2. Tests for auth abuse and session edge cases.
3. Tests around curation publication safeguards.
4. Fresh-environment setup test that proves the public corpus boots cleanly.

### 8. Deployment Safety
Current evidence:
- Docker Compose is the only active deployment baseline.
- [docker-compose.yml](../../docker-compose.yml) is local-first and mounts source code volumes.
- Demo bootstrap still relies on seeded data and manual rehearsal.

Gap:
- This is an internal deployment posture, not a public service posture.

What is missing:
1. A production-like startup profile separated from live-reload development mode.
2. Backup and restore guidance for the database.
3. Migration rollout and rollback discipline beyond the first Alembic revision.
4. Safer container/runtime assumptions for public exposure.

### 9. Content And UX Readiness
Current evidence:
- The UX is good for internal demo and bounded v0.1 SLC explanation.
- There is no public privacy policy, terms, support contact, or public trust/disclaimer layer.
- Search/filter is intentionally narrow and some flows still need stronger empty/error/support content.

Gap:
- Public users would encounter a product that lacks policy, support, and trust framing expected for live exposure.

What is missing:
1. Privacy and terms pages.
2. Public support or contact guidance.
3. Stronger public disclaimers around bounded AI guidance and corpus limitations.
4. Better handling of unsupported states and coverage limits for public audiences.

## Highest-Risk Blockers
1. Demo/default security posture still exists in active config and deployment assumptions.
2. Auth/session model is not hardened for public abuse or compromised refresh tokens.
3. Trusted-data pipeline is still partly manual and seed-driven rather than ingestion-backed.
4. Observability is too weak for public incident response.
5. Public legal/support content is effectively absent.
6. Browser regression coverage is not part of the enforced release path.

## Prioritized Hardening Phases
### Phase 0: Public-Live Gate Definition
Goal: stop pretending internal-demo readiness equals public-live readiness.

Actions:
1. Add a public-live readiness document and release gate checklist.
2. Separate internal demo mode from public-live mode in docs and config naming.
3. Freeze any public-live attempt until Phase 1 and Phase 2 are complete.

### Phase 1: Security And Session Hardening
Goal: close the most obvious public-risk holes first.

Actions:
1. Make non-default production secrets mandatory.
2. Remove public-live reliance on demo-safe env defaults.
3. Add auth rate limiting or equivalent abuse controls.
4. Add refresh-token rotation/revocation or replace the session model with a safer public-live approach.
5. Strengthen password and account lifecycle controls.

### Phase 2: Data Trust And Publication Hardening
Goal: ensure public users only see data with defensible publication discipline.

Actions:
1. Implement the real ingestion-to-raw path.
2. Add publication safety checks and data regression tests.
3. Separate seed/demo data from public-live content paths.
4. Tighten curator workflow auditability and publication review evidence.

### Phase 3: Operational Hardening
Goal: make failures visible and recoverable.

Actions:
1. Add structured logs and exception logging.
2. Add minimal monitoring and worker visibility.
3. Add deployment runbooks, backup guidance, and rollback steps.
4. Remove live-reload and source-mounted assumptions from public-live deployment mode.

### Phase 4: Public UX And Release Quality
Goal: make the product safe and credible for external users.

Actions:
1. Add privacy, terms, support, and public trust/disclaimer content.
2. Normalize API/public error handling and frontend empty/error states.
3. Put core browser smoke into CI.
4. Rehearse a clean-environment deployment and rollback path.

## Recommended Sequence For Closing Gaps
1. Do not widen features first.
2. Harden auth/session and secret handling first.
3. Then harden publication/data trust.
4. Then add logging, monitoring, and deployment safeguards.
5. Only after that, finish public UX/legal/support content and broader release polish.

For a small team, that order is correct because the highest public risk is trust failure and account compromise, not feature incompleteness.

## Files That Should Be Updated Next
### Code and config
- [backend/app/core/config.py](../../backend/app/core/config.py)
- [backend/app/core/security.py](../../backend/app/core/security.py)
- [backend/app/services/auth/service.py](../../backend/app/services/auth/service.py)
- [backend/app/main.py](../../backend/app/main.py)
- [docker-compose.yml](../../docker-compose.yml)
- [.env.example](../../.env.example)
- [backend/.env.example](../../backend/.env.example)
- [.github/workflows/ci.yml](../../.github/workflows/ci.yml)

### Data and curation
- [backend/app/api/v1/routes/curation.py](../../backend/app/api/v1/routes/curation.py)
- [backend/app/services/curation/service.py](../../backend/app/services/curation/service.py)
- future ingestion implementation area under `backend/app/` or `workers/`

### Public-facing UX and docs
- [frontend/src/app/page.tsx](../../frontend/src/app/page.tsx)
- [frontend/src/components/layout/marketing-shell.tsx](../../frontend/src/components/layout/marketing-shell.tsx)
- [README.md](../../README.md)
- [docs/scholarai/DEMO_READINESS_AUDIT.md](../../docs/scholarai/DEMO_READINESS_AUDIT.md)
- [docs/scholarai/INTERNAL_HANDOFF_PACKAGE.md](../../docs/scholarai/INTERNAL_HANDOFF_PACKAGE.md)

## Critical Docs That Must Be Revised Before Public Use
1. Root [README.md](../../README.md)
   - It should explicitly separate internal v0.1 SLC readiness from any public-live posture.
2. [docs/scholarai/DEMO_READINESS_AUDIT.md](../../docs/scholarai/DEMO_READINESS_AUDIT.md)
   - It should remain explicitly internal and non-public.
3. [docs/scholarai/13_qa_devops_and_risks.md](../../docs/scholarai/13_qa_devops_and_risks.md)
   - It should be updated once the hardening phases begin so the public-live gates are documented.
4. New public-facing policy/support docs
   - privacy
   - terms
   - support/contact

## SLC decision (v0.1)
ScholarAI is not public-live ready. It is in an internal v0.1 SLC state that can support controlled demos and internal handoff.

## Deferred items
- Broad feature expansion before core hardening.
- Startup-scale operational work beyond the minimum public-live gate.
- Research-extension systems that do not reduce immediate public risk.

## Assumptions
- The team remains small and cannot support a heavy operations program.
- Public-live means minimally safe and supportable, not enterprise-grade.
- Hardening must be incremental and protect momentum around the existing v0.1 SLC foundation.

## Risks
- If the team treats internal demo readiness as public-live readiness, the first failures will likely be auth abuse, data trust problems, or weak operational visibility.
- If hardening is deferred too long, feature work will entrench unsafe assumptions.
- If public trust content is added last, the product may appear more mature than its operational posture actually is.

