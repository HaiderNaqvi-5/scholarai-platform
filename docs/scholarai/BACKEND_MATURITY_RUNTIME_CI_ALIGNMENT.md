# Backend Runtime and CI Alignment (Taskboard Subtask 01)

Date: 2026-03-23

## Objective

Standardize backend runtime and validation commands to reduce local/CI drift and deployment surprises.

## Decisions Applied

1. **Canonical backend Python runtime set to 3.12** for local validation and CI jobs.
2. **Single canonical dependency manifest remains `backend/requirements.txt`**.
3. **Removed stale duplicate manifests**:
   - `backend/requirements_current.txt`
   - `backend/requirements_actual.txt`

## CI Alignment Changes

Updated `.github/workflows/ci.yml` backend Python versions from `3.11` to `3.12` for:

- `backend-sanity`
- `kpi-regression-gate`
- `browser-smoke` backend setup step

## Canonical Validation Command Set

Use these commands before commit for backend maturity tasks:

1. **Targeted checks (task-specific)**
   - `pytest backend/tests/unit/test_health.py backend/tests/unit/test_security.py -q`
2. **Full backend regression**
   - `pytest backend/tests/unit backend/tests/integration -q`
3. **KPI regression gate parity**
   - `pytest backend/tests/integration/test_recommendation_policy_version.py backend/tests/integration/test_analytics_kpi_trends.py backend/tests/integration/test_document_interview_policy_versions.py backend/tests/unit/test_kpi_policy.py backend/tests/unit/test_kpi_snapshot_service.py backend/tests/unit/test_recommendation_evaluation.py backend/tests/unit/test_document_service.py backend/tests/unit/test_interview_service.py -q`

## Commit Gate Checklist

- [x] Targeted command executed and green
- [x] Full backend unit/integration executed and green
- [x] KPI suite executed and green
- [x] Scope limited to runtime/CI alignment and command standardization
- [x] Output summary captured in this report

## Notes

- `backend/pytest.ini` already defines `asyncio_default_fixture_loop_scope = function`, reducing async fixture warning noise.
- Existing `python-jose` `datetime.utcnow()` deprecation warning is dependency-origin and non-blocking for this step.
