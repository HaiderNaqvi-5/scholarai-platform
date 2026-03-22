# ScholarAI KPI Maturity Status (2026-03-22)

## Purpose
This report tracks outcome-based maturity gates across the stacked delivery sequence.
It answers two questions:
1. What KPI-gated slices are already implemented?
2. What is still left before KPI-driven release readiness?

## Implemented KPI-Gated Slices

### Slice A: Recommendation Evaluation KPIs
- Branch: `feat/reco-kpi-gates`
- Implemented in:
  - `backend/app/services/recommendations/evaluation.py`
  - `backend/app/schemas/recommendations.py`
  - `backend/app/api/v1/routes/recommendations.py`
  - `backend/tests/unit/test_recommendation_evaluation.py`
- Outcome:
  - Threshold-aware gate checks exist for `precision@k`, `recall@k`, `ndcg@k`.
  - Optional baseline delta gate (`ndcg_delta_min`) is implemented.
  - API returns per-k gate outputs and `kpi_passed` aggregate status.

### Slice B: Document + Interview Coaching KPIs
- Branch: `feat/coach-kpi-gates`
- Implemented in:
  - `backend/app/schemas/documents.py`
  - `backend/app/services/documents/service.py`
  - `backend/app/schemas/interviews.py`
  - `backend/app/services/interview/service.py`
  - `backend/tests/unit/test_document_service.py`
  - `backend/tests/unit/test_interview_service.py`
- Outcome:
  - Document feedback now includes a quality gate object with explicit threshold checks.
  - Interview session summary now includes progression gate pass/fail checks.

### Slice C: API Contract KPI Signals
- Branch: `feat/api-contract-kpi-signals`
- Implemented in:
  - `backend/app/main.py`
  - `backend/tests/integration/test_protected_routes.py`
- Outcome:
  - Contract-version headers are explicit (`X-API-Contract-Version`).
  - V1 deprecation window is machine-readable (`X-API-V1-Sunset-Days`).
  - Test coverage verifies v1/v2 header behavior.

## What Is Left (Detailed)

### 1) KPI Policy Centralization (High Priority)
Current state:
- Thresholds are hardcoded in service modules.

Remaining work:
- Move KPI thresholds to a centralized config source (env/settings or policy table).
- Add policy versioning so KPI evaluations can be reproduced against exact gate versions.
- Emit policy version in API responses for recommendation/doc/interview KPI outputs.

Acceptance signal:
- Gate outputs include a `policy_version` and do not require code edits to change thresholds.

### 2) KPI Persistence and Trend Visibility (High Priority)
Current state:
- KPI evaluation is computed per request/session response only.

Remaining work:
- Persist KPI snapshots for recommendation evaluations and coaching sessions.
- Add aggregate trend endpoints (rolling pass rate, median deltas, failure drivers by gate).
- Define retention policy for KPI snapshots.

Acceptance signal:
- Team can query KPI pass-rate trends over time without replaying historical payloads.

### 3) Release Gate Automation (High Priority)
Current state:
- KPIs are available but not enforced in CI/CD or merge policy.

Remaining work:
- Add CI job(s) that fail on KPI regression thresholds.
- Define branch/PR gate policy (block merge when KPI baseline deltas fail).
- Document approved override/escalation path for emergency merges.

Acceptance signal:
- A KPI regression reliably fails CI and blocks merge unless an explicit override path is used.

### 4) API v2 Functional Parity Expansion (Medium Priority)
Current state:
- `v2` namespace exists for recommendations evaluate path only.

Remaining work:
- Expand v2 route parity to additional critical endpoints used by clients.
- Add parity checklist and per-route migration completion status.
- Publish migration examples for client teams.

Acceptance signal:
- All client-critical paths have v2 equivalents with migration docs.

### 5) KPI Backtest Dataset Discipline (Medium Priority)
Current state:
- Request-level baseline comparison is possible, but no standardized judged-set registry is enforced.

Remaining work:
- Define approved judged datasets and baseline snapshots by domain slice.
- Version datasets and freeze benchmark sets for regression testing.
- Add data quality checks for judged relevance integrity.

Acceptance signal:
- KPI regressions are measured against approved, versioned benchmark sets.

### 6) Docs Convergence Completion (Medium Priority)
Current state:
- Canonical docs are strong, but KPI status is distributed across reports/branches.

Remaining work:
- Link this KPI report from canonical docs entry points.
- Add an "authoritative current stack" section with branch order and PR links.
- Mark legacy references as historical if they conflict with KPI-driven process.

Acceptance signal:
- New contributors can find current KPI posture and remaining work from one canonical entry point.

### 7) Production Observability Hooks (Medium Priority)
Current state:
- KPI values are returned via APIs but not fully integrated with monitoring/alerting.

Remaining work:
- Emit KPI pass/fail metrics to observability stack.
- Add alerts for sustained KPI degradation.
- Add dashboard tiles for recommendation/doc/interview/API contract KPI health.

Acceptance signal:
- KPI incidents are discoverable from monitoring without manual API polling.

## Remaining Work by Phase
| Phase | Status | Remaining |
|---|---|---|
| Ingestion hardening | Implemented baseline | broaden source adapters and parser resilience KPIs |
| Recommendation harness | Implemented with gates | persistent KPI snapshots and benchmark governance |
| Document/interview depth | Implemented with gates | trend persistence, policy versioning, observability |
| API long-term standardization | Implemented signal layer | expand v2 parity and automate release gates |
| Docs convergence | In progress | consolidate all KPI process docs into single canonical index |

## Immediate Next Slice Recommendation
1. KPI policy centralization (`policy_version`, config-driven thresholds).
2. KPI persistence model + trend endpoint.
3. CI merge gate enforcement using persisted benchmark checks.
