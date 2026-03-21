# ScholarAI Minimal Push Plan (2026-03-22)

## Goal
Align documentation and implementation status on GitHub with minimal risk and clean review boundaries.

## Current Branch State
- Local is commit-synced with `origin/main` (`0 ahead / 0 behind`).
- Many local modifications exist and are not yet pushed.
- Backend/auth/curation ingestion verification suite currently passes (`24 passed`).

## Push Strategy
Use three small commits in order.

## Commit 1: Canonical Status and Plan Updates
### Files
- `docs/scholarai/12_execution_plan.md`
- `docs/scholarai/13_qa_devops_and_risks.md`
- `docs/scholarai/14_future_roadmap.md`
- `docs/scholarai/WORKPLAN.md`
- `docs/scholarai/README.md`

### Commit message
`docs(scholarai): align execution plan and roadmap with current implementation status`

## Commit 2: Canonical Architecture/API/Data Consistency
### Files
- `docs/scholarai/04_requirements_and_governance.md`
- `docs/scholarai/05_system_architecture.md`
- `docs/scholarai/06_data_models.md`
- `docs/scholarai/10_backend_api_and_repo.md`

### Commit message
`docs(scholarai): sync governance, architecture, data model, and API contracts`

## Commit 3: Legacy Root Docs Harmonization
### Files
- `docs/PRD.md`
- `docs/api_design.md`
- `docs/architecture.md`
- `docs/architecture_diagrams.md`
- `docs/database_schema.md`
- `docs/deployment.md`
- `docs/phase_status_report.md`
- `docs/research.md`

### Commit message
`docs(legacy): harmonize root docs and mark canonical references`

## Pre-Push Checklist
1. Run docs sanity diff review:
   - Ensure no contradiction between root docs and `docs/scholarai/*`.
2. Verify implementation references remain valid:
   - route/module names, role/capability terms, and state-machine names.
3. Re-run target backend checks:
   - `python -m pytest tests/unit/test_ingestion_service.py tests/unit/test_curation_service.py tests/unit/test_auth_service.py tests/unit/test_auth_claim_enforcement.py tests/unit/test_authorization_matrix.py tests/integration/test_authorization_denials.py`

## Push Command Sequence
1. Stage first commit file group and commit.
2. Stage second commit file group and commit.
3. Stage third commit file group and commit.
4. `git push origin main`

## Rollback Safety
- If one docs commit is wrong, revert only that commit:
  - `git revert <commit_sha>`
- Keep docs commits independent from code commits.
