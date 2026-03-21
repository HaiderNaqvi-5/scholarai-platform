# ScholarAI Docs Delta Report (2026-03-22)

## Purpose
Provide a commit-ready snapshot of documentation changes required to align canonical docs with the current implementation status.

## Implementation Verification Baseline
- Backend/auth/curation target test suite is green:
  - `tests/unit/test_ingestion_service.py`
  - `tests/unit/test_curation_service.py`
  - `tests/unit/test_auth_service.py`
  - `tests/unit/test_auth_claim_enforcement.py`
  - `tests/unit/test_authorization_matrix.py`
  - `tests/integration/test_authorization_denials.py`
- Latest run result: `24 passed`.

## Docs Changed In Working Tree
### Legacy-root docs updated
- `docs/PRD.md`
- `docs/api_design.md`
- `docs/architecture.md`
- `docs/architecture_diagrams.md`
- `docs/database_schema.md`
- `docs/deployment.md`
- `docs/phase_status_report.md`
- `docs/research.md`

### Canonical docs updated
- `docs/scholarai/04_requirements_and_governance.md`
- `docs/scholarai/05_system_architecture.md`
- `docs/scholarai/06_data_models.md`
- `docs/scholarai/10_backend_api_and_repo.md`
- `docs/scholarai/12_execution_plan.md`
- `docs/scholarai/13_qa_devops_and_risks.md`
- `docs/scholarai/14_future_roadmap.md`
- `docs/scholarai/README.md`
- `docs/scholarai/WORKPLAN.md`

## Intended Alignment Outcome
1. Canonical docs describe capability-based authorization and institution scope behavior.
2. Execution-plan and status docs reflect current implementation posture and remaining gaps.
3. Legacy root docs are either synchronized to canonical truths or explicitly marked as historical/superseded.

## Required Consistency Checks Before Push
1. Route naming consistency:
   - Ensure endpoint names and dependency guards in docs match mounted routes in `backend/app/api/v1/routes/` and `backend/app/core/dependencies.py`.
2. Data-model consistency:
   - Ensure schema language matches model/migration reality in `backend/app/models/models.py` and latest Alembic revisions.
3. MVP scope consistency:
   - Confirm Canada-first and bounded-assistance language is consistent across `02`, `05`, `08`, `10`, `12`, `14` docs.
4. Legacy-doc de-duplication:
   - Ensure root docs do not conflict with canonical docs. Prefer explicit superseded banners when needed.

## Known Risk If Pushed Without Grouping
- Mixing docs and code changes in one large commit will make review and rollback difficult.
- Root and canonical docs may drift again if they are merged without a clear source-of-truth note.

## Commit-Ready Scope Recommendation
- Push docs in dedicated commits (no backend/frontend code mixed in the same commit).
- Keep canonical changes separate from legacy archival/superseded edits.
