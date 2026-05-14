# Progress — 2026-05-14 (session: PR #84 CI repair + test gap-fill)

**Branch:** `chore/document-smoke-flag-removal` (off `main` @ `7259c8b`; PR #86 open)

## Tasks completed this session

### 1. Pakistan PRD test audit + gap-fill (earlier in session)
- Audited `SCHOLARAI_PAKISTAN_PRD.md` (§0, §0.5, §0.6, §1–§10) against the backend test surface. Coverage already extensive; mapped every acceptance bullet to an existing suite.
- Added `backend/tests/unit/test_b2b_trust_boundary.py` — AST-walks `app/services/recommendations` + `app/services/scholarships`, fails if they reference `Institution` / `InstitutionStudent` / `ReferralEnrollment` / `UniversityLead` or those table names. Enforces PRD §0.6 trust boundary in CI.
- Added `backend/tests/unit/test_demo_seed_pakistan.py` — source-level pin on `scripts/demo_seed_pakistan.py` (zara persona, plan=elite, 2099 expiry, 5 consents, ≥10 scholarships / ≥30 unis / ≥70 visa Q). Runs offline, no DB.
- Extended `_profile()` fixture in `tests/unit/test_privacy_and_b2b.py` with the migration-0019 B2B snapshot fields so the snapshot test is resilient to field additions.
- Full backend suite green: **306 passed** (`pytest tests/unit tests/integration`).
- This work shipped via PR #85 (`feat/phase-c-and-scraper-wip` → `main`, merged).

### 2. PR #84 CI repair — all 4 failing checks fixed (merged)
PR #84 (`feat/pakistan-pivot-merge` → `main`) had 4 red checks. Root causes + fixes:
- **frontend-sanity + browser-smoke + Vercel** — CI used `actions/setup-node@v4` with `cache: npm` + `cache-dependency-path: frontend/package-lock.json`, but the greenfield rebuild migrated to Bun (`frontend/bun.lock`, no `package-lock.json`). Cache step aborted both jobs. Fix: `.github/workflows/ci.yml` migrated frontend jobs to `oven-sh/setup-bun@v2` + `bun install --frozen-lockfile` + `bun run lint/typecheck/build` + `bun run start`. Added missing `"typecheck": "tsc --noEmit"` script to `frontend/package.json`.
- **docs-governance** — `scripts/docs_governance_check.py` flagged 3 broken local links in `docs/scholarai/PUBLIC_LIVE_HARDENING_PLAN.md` pointing at pre-rebuild frontend paths. Re-pointed: `auth-provider.tsx` → `lib/auth/AuthProvider.tsx`, `lib/api.ts` → `lib/api/client.ts`, `marketing-shell.tsx` → inlined-in-`app/page.tsx` note.
- **Latent typecheck failure** — `bun run typecheck` (newly wired) surfaced 19 errors in `frontend/src/components/scholarship/EligibilityMatrix.tsx` reading pre-Pakistan-pivot `StudentProfile` fields. Re-pointed to canonical shape: `citizenship` → `citizenship_country_code`, `degree_level` → `target_degree_level`, `gpa` → `gpa_value`, `field_tags[]` → `target_field`, `language_scores[]` → `language_test_type` + `language_test_score`.
- **browser-smoke still red after the above** — stale `data-testid` selectors from the greenfield rebuild (not real regressions). Added `continue-on-error: true` to the smoke step per the `AGENTS.md`/`CLAUDE.md` "smoke relaxed until S10 / Frontend Pass" doctrine.
- Result: all 7 checks green. PR #84 **merged**.
- Note: PR #84's branch was auto-deleted on merge; an accidental push recreated it as an orphan — deleted again (local + remote). Local safety tag `safety/c096dc8` left in place (harmless, local-only).

### 3. Document the temp CI flag (PR #86 — this branch)
- `continue-on-error: true` on `browser-smoke` had no written removal trigger — risk of rotting into a permanent silent false-green.
- `CLAUDE.md` edits:
  - Stack line: notes CI `frontend-sanity` + `browser-smoke` run on Bun, no `package-lock.json`.
  - Push gate section: documents the flag, warns a green `browser-smoke` job ≠ smoke passed, states the flag must be removed at S10 / Frontend Pass.
  - Open work / Frontend Pass line: appends "remove `continue-on-error` from the `browser-smoke` step" to the existing "re-point smoke selectors" task.
- CLAUDE.md at 118 lines (under 200 cap).

## Files touched this session
- `backend/tests/unit/test_b2b_trust_boundary.py` — new (PR #85).
- `backend/tests/unit/test_demo_seed_pakistan.py` — new (PR #85).
- `backend/tests/unit/test_privacy_and_b2b.py` — fixture extension (PR #85).
- `.github/workflows/ci.yml` — Bun migration + `continue-on-error` on smoke (PR #84).
- `frontend/package.json` — added `typecheck` script (PR #84).
- `docs/scholarai/PUBLIC_LIVE_HARDENING_PLAN.md` — 3 broken links re-pointed (PR #84).
- `frontend/src/components/scholarship/EligibilityMatrix.tsx` — canonical `StudentProfile` fields (PR #84).
- `CLAUDE.md` — Bun-CI note + S10 flag-removal note (PR #86, this branch).
- `progress.md` — this file.

## In-progress / next
- PR #86 open: `chore/document-smoke-flag-removal` → `main`. CLAUDE.md + progress.md only. Awaiting review/merge.
- **S10 / Frontend Pass** must: re-point all smoke `data-testid` selectors AND remove `continue-on-error: true` from the `browser-smoke` step in `.github/workflows/ci.yml`.
- Pre-existing low-priority items carried from prior sessions: `/admin/sources` UI for `DiscoveryService` results; apply migration `20260514_0020_ingestion_caching` to live dev DB; `broker_connection_retry_on_startup` deprecation in `app/tasks/celery_app.py`.

## Open bugs / blockers
- None. PR #84 merged green; PR #86 is docs-only.

## Commands to resume
- Backend tests: `cd backend && python -m pytest tests/unit tests/integration -q`
- Frontend gate: `cd frontend && bun install --frozen-lockfile && bun run lint && bun run typecheck && bun run build`
- Docs gate: `python scripts/docs_governance_check.py`
- API: `cd backend && python -m uvicorn app.main:app --reload`
- Frontend dev: `cd frontend && bun dev`
