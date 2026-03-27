# Governance Rollout Closure Evidence (2026-03-27)

This document closes the v0.1 governance rollout with an auditable trace that links template governance, CI governance gates, and branch enforcement on `main`.

## 1) Main Branch Enforcement State

Repository: `HaiderNaqvi-5/scholarai-platform`

Verified branch protection state (GitHub API, 2026-03-27):

- Pull request required before merge: **enabled** (`required_pull_request_reviews` configured).
- Required status checks before merge: **enabled**.
- Required check name: **`docs-governance`**.
- Strict up-to-date mode: **enabled** (`required_status_checks.strict = true`).
- Apply to administrators: **enabled** (`enforce_admins.enabled = true`).

## 2) Canonical Governance Rollout PR Chain

- PR #40: [docs(governance): enforce staged PR/issue contract and evidence policy](https://github.com/HaiderNaqvi-5/scholarai-platform/pull/40)
- PR #41: [ci(docs): add docs-governance terminology/link/canonical-tail gate](https://github.com/HaiderNaqvi-5/scholarai-platform/pull/41)
- PR #42: [docs(acceptance): add v0.1 checklist and role/auth conformance artifacts](https://github.com/HaiderNaqvi-5/scholarai-platform/pull/42)
- PR #43: [docs(governance): align baseline docs with docs-governance gate](https://github.com/HaiderNaqvi-5/scholarai-platform/pull/43)

## 3) Enforcement Recheck (Must-Fail / Must-Pass)

Validation PR:

- PR #46: [test: recheck docs-governance required gate on main](https://github.com/HaiderNaqvi-5/scholarai-platform/pull/46)

Commit sequence in PR #46:

- `e50574e0f119c907fe098eb2bc96ef0cc546d3ff` — intentional docs policy violation injected.
- `b06414771dff91a5ab1ab6fce5b29d725b4d72e7` — intermediate workflow hardening attempt in test branch.
- `da97835f5e530accd51899739a8ccf24a5cffd8e` — violation removed for must-pass check.

Observed enforcement outcomes:

- Must-fail evidence: `docs-governance` failed after hardening during validation run (`run_id: 23660440273`), and merge remained blocked while required check was failing.
- Must-pass evidence: `docs-governance` passed after removing the violation (`run_id: 23660609864`), and PR became merge-eligible before closure.

PR #46 was intentionally closed after evidence capture to avoid merging test-only commits.

## 4) Root Cause and Permanent Fix Trace

Root-cause discovered during recheck:

- In CI, `python scripts/docs_governance_check.py | tee ...` allowed a false pass when the Python command emitted an error but `tee` returned success.
- Missing `set -o pipefail` caused the step status to reflect pipeline tail success instead of governance check failure.

Permanent fix:

- PR #47: [fix(ci): enforce pipefail in docs-governance check](https://github.com/HaiderNaqvi-5/scholarai-platform/pull/47)
- Merged at: `2026-03-27T18:14:09Z`
- Merge commit: `4e761002f3102f6809fcad5a31e835c22a7b8f2d`
- Effective hardening in `.github/workflows/ci.yml`:
  - Added `set -o pipefail` before `python scripts/docs_governance_check.py | tee /tmp/docs-governance.out`.

## 5) Checklist Traceability Example (Template -> PR -> CI)

Checklist source of truth:

- `docs/scholarai/v0_1_slc_acceptance_checklist.md`
- Example ID: **`SLC-UI-003`** (UI evidence tied to checklist IDs in acceptance mapping).

Trace chain:

1. Issue intake governance:
   - `.github/ISSUE_TEMPLATE/bug_report.md` and `.github/ISSUE_TEMPLATE/feature_request.md` require stage/evidence/checklist fields.
2. PR governance:
   - `.github/pull_request_template.md` requires Stage Label, SLC impact, deferred impact, UI evidence links, and acceptance checklist IDs.
3. CI governance enforcement:
   - `docs-governance` job validates required docs/governance contracts and blocks merge when policy checks fail.

This provides end-to-end accountability from request intake through merge gate enforcement.
