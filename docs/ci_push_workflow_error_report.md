# CI / Push Failure Investigation Report

Generated: 2026-03-21T10:40:55Z (UTC)  
Repository: `HaiderNaqvi-5/scholarai-platform`

## Scope
- Find current errors.
- Find failed GitHub push-related runs.
- Check CI workflow issues.
- Provide concrete solutions.

## What was checked
- Workflow config: `.github/workflows/ci.yml`
- Recent workflow runs (`push` + `pull_request`) via GitHub Actions API
- Failed job logs for representative failing runs
- Local baseline reproduction:
  - `backend`: `pytest tests/unit tests/integration -q` ✅ (47 passed)
  - `frontend`: `npm run lint` ❌ (5 errors, 4 warnings)

## Executive summary
1. **There are many failed workflow runs triggered by push events** (especially on `main` and earlier `develop`).
2. **Current blocking failures are frontend quality/build related**, not backend tests:
   - ESLint `no-explicit-any` violations.
   - React hook rule violation (`setState` directly in `useEffect` body).
   - Next.js build failure on `/admin` due to `useSearchParams()` missing `Suspense` boundary.
3. **Historical backend CI failures existed** (import/path issues), but at least one of those is now resolved in current code.
4. Some recent PR runs show **`action_required`**, which is workflow-state/approval related, not a compile/test code failure.

---

## A) Failed push-triggered runs found

The following `push` runs are recorded with `conclusion=failure`:

- `23336667622` (run #24, `main`, sha `54764e86`)
- `23307109008` (run #22, `main`, sha `5f64fa75`)
- `23306096783` (run #21, `main`, sha `c6280b88`)
- `23213541558` (run #18, `main`, sha `dad99167`)
- `23207645156` (run #16, `main`, sha `a2ff8f8e`)
- `23141415025` (run #14, `main`, sha `30d30d08`)
- `23141086430` (run #13, `main`, sha `3bf0d454`)
- `23140982661` (run #12, `main`, sha `4174fd38`)
- `23140841357` (run #11, `main`, sha `4bf1c095`)
- `23140688242` (run #10, `main`, sha `30b7f135`)
- `23139838913` (run #9, `main`, sha `db290e47`)
- `23129424197` (run #8, `main`, sha `1b56da43`)
- `23129177422` (run #7, `main`, sha `500a03e7`)
- `23107400628` (run #6, `develop`, sha `6366952b`)
- `23091096160` (run #5, `develop`, sha `33f0821b`)
- `23090714365` (run #4, `develop`, sha `18003f62`)
- `23090458830` (run #3, `develop`, sha `d14bfabe`)
- `23090369822` (run #2, `develop`, sha `bf0c85e4`)
- `23090195412` (run #1, `develop`, sha `79d9e858`)

### Important interpretation
- These are **push-triggered CI failures**, not evidence of Git network push rejection.
- Branch updates were accepted by GitHub, but CI checks failed after push.

---

## B) Current CI errors (reproducible now)

### 1) Frontend lint failures (blocking `frontend-sanity`)
Seen in runs such as:
- `23336667622` job `67880032682`
- `23377876040` job `68012751561`

Errors:
- `frontend/src/components/admin/analytics-dashboard-shell.tsx`
  - `Unexpected any. Specify a different type`
- `frontend/src/components/mentor/mentor-dashboard-shell.tsx`
  - `Unexpected any. Specify a different type` (multiple)
- `frontend/src/components/auth/auth-provider.tsx`
  - React hooks lint error: synchronous `setState` call inside effect

Warnings (non-blocking but should clean up):
- unused `message` prop in route wrappers
- unused `SkeletonCard` import

### 2) Frontend build failure in browser smoke (blocking `browser-smoke`)
Seen in runs such as:
- `23336667622` job `67880032655`
- `23377876040` job `68012751567`

Failure signature:
- `useSearchParams() should be wrapped in a suspense boundary at page "/admin"`
- `Error occurred prerendering page "/admin"`

Impact:
- `npm run build` fails in CI, so smoke flow never reaches service boot/smoke scripts.

### 3) Historical backend failure (observed in older runs)
In older logs (example run `23306096783`), backend failed with:
- `ModuleNotFoundError: No module named 'sqlalchemy.exceptions'`

Current repository state:
- `/backend/app/main.py` now imports correctly from `sqlalchemy.exc`.
- Local backend sanity tests pass (`47 passed`), indicating this specific issue has been addressed.

### 4) Historical backend test path/import failures (early CI evolution)
In older run `23107400628`, backend job failed with repeated:
- `ModuleNotFoundError: No module named 'app'`
- `ImportError while importing test module ...`

Likely cause in that period:
- Running tests from wrong working directory / incorrect PYTHONPATH assumptions.

Current state suggests this was later corrected by the split sanity test command pattern used now.

---

## C) Workflow-level issues identified

1. **Frontend gates are stricter than current code quality**  
   CI correctly fails because lint/build gates are enabled and code does not satisfy them.

2. **Browser smoke is coupled to successful frontend production build**  
   Any Next.js prerender issue prevents smoke tests from even starting backend/frontend services.

3. **Node 20 deprecation warning in Actions logs**  
   Warnings indicate future runner behavior changes for JS actions. Not immediate failure, but medium-term risk.

4. **Some recent PR runs are `action_required`**  
   These are workflow-state signals (often policy/approval-driven) rather than compiler/test exceptions.

---

## D) Recommended fixes (priority order)

### Priority 1 — Unblock CI now
1. **Fix frontend lint errors**
   - Replace `any` with explicit interfaces/types in:
     - `frontend/src/components/admin/analytics-dashboard-shell.tsx`
     - `frontend/src/components/mentor/mentor-dashboard-shell.tsx`
   - Refactor `auth-provider` initialization so state is not set synchronously in an effect body.

2. **Fix `/admin` prerender issue**
   - Wrap `useSearchParams()` usage in `Suspense` boundary, or move usage into client-only subtree compliant with Next.js rule.
   - Re-run `npm run build` locally to verify.

### Priority 2 — Harden workflow stability
3. **Add targeted frontend tests/checks around `/admin` rendering path**
   - Prevent recurrence of Suspense/prerender regressions.

4. **Keep backend sanity command path stable**
   - Continue using working-directory/test-path-safe command style currently used in `ci.yml`.

### Priority 3 — Maintenance
5. **Prepare Actions for Node 24 transition**
   - Update action versions when available/required and validate workflow behavior before enforcement date.

6. **Document `action_required` handling**
   - Add a short maintainer note in docs/ops runbook clarifying when manual approval/policy gates apply.

---

## E) Verification checklist after applying fixes
- [ ] `frontend`: `npm run lint` passes
- [ ] `frontend`: `npm run typecheck` passes
- [ ] `frontend`: `npm run build` passes
- [ ] `backend`: `pytest tests/unit tests/integration -q` passes
- [ ] `ci` workflow passes for both `pull_request` and `push`
- [ ] Browser smoke reaches and executes smoke scripts (not failing early at build step)

