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

## Current Status Update (Post-Stack Continuation)

### Completed after this report was first drafted

#### KPI Policy Centralization
- Status: done
- Implemented:
  - Centralized policy thresholds and versions in settings/policy helpers.
  - API responses expose `policy_version` for recommendation/document/interview KPI outputs.

#### KPI Persistence and Trend Visibility
- Status: done (baseline)
- Implemented:
  - KPI snapshots persisted for recommendation, document, and interview domains.
  - Analytics endpoint includes KPI trend items by domain and policy version.

#### Release Gate Automation
- Status: done (baseline)
- Implemented:
  - CI adds a KPI regression gate job that runs KPI-critical test suites and fails on regression.

#### API v2 Functional Parity Expansion
- Status: done (baseline critical set)
- Implemented:
  - v2 router now includes recommendations, documents, interviews, profile, scholarships, and analytics routes.

#### Production Observability Hooks
- Status: done (baseline)
- Implemented:
  - Health endpoints include `kpi_alerts` and degrade status on sustained KPI pass-rate drops.
  - Alert thresholds/volume/lookback are config-driven.

#### KPI Snapshot Retention Hardening
- Status: done (baseline)
- Implemented:
  - Added periodic Celery cleanup task `tasks.run_kpi_snapshot_retention_cleanup`.
  - Added configurable retention controls (`KPI_SNAPSHOT_RETENTION_*`) and beat schedule wiring.

## What Is Left (Detailed)

### 1) KPI Backtest Dataset Discipline (High Priority)
Current state:
- Request-level baseline comparison is possible, but no standardized judged-set registry is enforced.

Remaining work:
- Define approved judged datasets and baseline snapshots by domain slice.
- Version datasets and freeze benchmark sets for regression testing.
- Add data quality checks for judged relevance integrity.

Acceptance signal:
- KPI regressions are measured against approved, versioned benchmark sets.

### 2) Docs Convergence Completion (High Priority)
Current state:
- KPI docs are now linked from canonical entry points, but legacy references outside the canonical index still exist.

Remaining work:
- Mark non-canonical KPI references as historical where they conflict.
- Add PR links once branch stack is merged.
- Keep one live KPI operations index and archive dated snapshots.

Acceptance signal:
- New contributors can find current KPI posture and active stack from one canonical index.

### 3) Observability and Alert Routing Hardening (Medium Priority)
Current state:
- KPI alerts are surfaced in health payloads.
- KPI snapshot retention cleanup is automated through Celery beat.

Remaining work:
- Route KPI degradation alerts to external channels.
- Add dashboard tiles/charts for KPI trends and alert state.

Acceptance signal:
- KPI incidents are discoverable in monitoring channels without polling health manually.

### 4) KPI Override / Escalation Policy (Medium Priority)
Current state:
- CI gate exists, but emergency override process is not yet documented in canonical runbooks.

Remaining work:
- Document explicit override policy and required approvals.
- Add rollback/fix-forward expectations for KPI gate bypass events.

Acceptance signal:
- Emergency gate bypasses are auditable and consistently handled.

## Remaining Work by Phase
| Phase | Status | Remaining |
|---|---|---|
| Ingestion hardening | Implemented baseline | broaden source adapters and parser resilience KPIs |
| Recommendation harness | Implemented with persistence + gates | benchmark dataset governance |
| Document/interview depth | Implemented with persistence + gates | alert routing hardening |
| API long-term standardization | Implemented with expanded v2 parity | client migration completion tracking |
| Docs convergence | In progress | finalize historical tagging and branch-to-PR traceability |

## Immediate Next Slice Recommendation
1. KPI benchmark dataset governance and versioned baseline registry.
2. Alert routing + dashboard tiles for sustained KPI degradation.
3. Canonical override/escalation policy for CI KPI gate bypass.
