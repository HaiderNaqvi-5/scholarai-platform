# Agent Instructions

> **⚠️ Current state (2026-05-30):** Pakistan-pivot product (brand **AidwiseAI**). **561 backend tests pass + 1 xfail**, alembic head `20260526_0029`. Auth = **Clerk** (`AUTH_PROVIDER=local|clerk`, default `local`); email = **Resend**; capture = **Firecrawl Cloud** (Playwright dropped from prod). Frontend = **Bun** (no `package-lock.json`). Live state of record: root `CLAUDE.md` + `progress.md`.

## Workflow
- Follow the project-local instruction set declared in [`opencode.json`](opencode.json):
  - Plugin: `ecc-universal`
  - `skills/tdd-workflow/SKILL.md`
  - `skills/security-review/SKILL.md`
  - `skills/coding-standards/SKILL.md`
  - `skills/backend-patterns/SKILL.md`
  - `skills/e2e-testing/SKILL.md`
  - `skills/verification-loop/SKILL.md`
  - `skills/api-design/SKILL.md`
- CI automation is defined in [`.github/workflows/ci.yml`](.github/workflows/ci.yml) and currently runs backend sanity, KPI regression, frontend sanity, docs governance, and browser smoke jobs.
- Mandatory push gate: before any push to GitHub, run all backend unit/integration checks and the full CI-equivalent local suite (backend sanity, KPI regression, frontend lint/type/build, docs governance, and browser smoke) and only push after all pass.
- **Browser smoke is the human gate, not the CI gate, until Frontend Pass S10.** CI marks `Run critical browser smoke` `continue-on-error: true` because greenfield S1–S9 dropped the old `data-testid` anchors that the smoke scripts target — failures are stale-selector noise, not regressions. The flag MUST be removed as the first task of S10 (re-point selectors → flip flag → verify red turns green). Until then, every PR touching `frontend/src/app/**`, `frontend/src/components/auth/**`, `frontend/src/lib/auth/**`, `frontend/src/lib/api/**`, or `backend/app/api/v1/routes/**` MUST run `python tests/e2e/playwright/run_smoke_suite.py` locally and paste the result in the PR description before merge. Scraper / ingestion / backend-service-only PRs are exempt.
- Continuity rule: continue working on v0.1 feature slices until the context/session limit is reached, unless blocked by an explicit dependency that needs user input.
- Additional repository guidance exists in [`.codex/AGENTS.md`](.codex/AGENTS.md); treat it as complementary project guidance alongside [`opencode.json`](opencode.json).

## Commands
- Root stack: `docker compose up --build`
- Backend setup: `python -m pip install -r backend/requirements.txt`
- Backend bootstrap: `cd backend; python scripts/bootstrap_local.py`
- Backend compile sanity: `python -m compileall backend/app backend/tests`
- Backend tests: `pytest backend/tests -q` (run the FULL tree — Clerk/Resend suites live in `tests/integrations` (plural) + `tests/api|core|db|services|scripts`; the old `tests/unit tests/integration`-only command silently skipped 42 auth/email tests, fixed in `ci.yml`).
- Docs governance: `python scripts/docs_governance_check.py`
- Backend dev server: `cd backend; python -m uvicorn app.main:app --reload`
- Backend API demo rehearsal: `cd backend; python scripts/rehearse_seeded_demo.py`
- Frontend uses **Bun** (no `package-lock.json`; CI uses `oven-sh/setup-bun`). Do NOT use npm.
- Frontend setup: `cd frontend; bun install --frozen-lockfile`
- Frontend checks: `cd frontend; bun run lint`, `cd frontend; bunx --bun tsc --noEmit`, `cd frontend; bun run build`
- Frontend smoke server: `cd frontend; bun run start -- --hostname 0.0.0.0 --port 3000`
- Frontend dev server: `cd frontend; bun dev`  (stop the compose `frontend` container first — it binds :3000 and serves a stale build)
- Playwright browser install (test-only; Playwright/Chromium removed from prod Docker + capture path 2026-05-26): `python -m playwright install chromium`
- Browser smoke: `python tests/e2e/playwright/run_smoke_suite.py` after local backend/frontend services are running
- Browser demo rehearsal: `python tests/e2e/playwright/rehearse_seeded_demo.py`
- Direct smoke entrypoints: `python tests/e2e/playwright/public_scholarship_browse_smoke.py`, `python tests/e2e/playwright/auth_dashboard_smoke.py`, `python tests/e2e/playwright/seeded_recommendations_smoke.py`, `python tests/e2e/playwright/document_feedback_smoke.py`, `python tests/e2e/playwright/interview_practice_smoke.py`, `python tests/e2e/playwright/curation_smoke.py`

## Key Files
- [`opencode.json`](opencode.json) is the current source of truth for agent-facing workflow configuration and plugin selection in this workspace.
- [`.codex/AGENTS.md`](.codex/AGENTS.md) contains additional repository-specific guidance on mission, architecture defaults, and documentation-first behavior.
- [`.github/workflows/ci.yml`](.github/workflows/ci.yml) is the source of truth for CI validation and smoke coverage.
- [`frontend/package.json`](frontend/package.json) + `frontend/bun.lock` define the active frontend scripts and **Bun** workflow.
- [`tests/e2e/README.md`](tests/e2e/README.md) documents the current smoke coverage and rehearsal expectations.
- [`docker-compose.yml`](docker-compose.yml) defines the local multi-service runtime stack.
