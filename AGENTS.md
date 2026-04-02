# Agent Instructions

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
- Continuity rule: continue working on v0.1 feature slices until the context/session limit is reached, unless blocked by an explicit dependency that needs user input.
- Additional repository guidance exists in [`.codex/AGENTS.md`](.codex/AGENTS.md); treat it as complementary project guidance alongside [`opencode.json`](opencode.json).

## Commands
- Root stack: `docker compose up --build`
- Backend setup: `python -m pip install -r backend/requirements.txt`
- Backend bootstrap: `cd backend; python scripts/bootstrap_local.py`
- Backend compile sanity: `python -m compileall backend/app backend/tests`
- Backend tests: `pytest backend/tests/unit backend/tests/integration -q`
- Docs governance: `python scripts/docs_governance_check.py`
- Backend dev server: `cd backend; python -m uvicorn app.main:app --reload`
- Backend API demo rehearsal: `cd backend; python scripts/rehearse_seeded_demo.py`
- Frontend setup: `cd frontend; npm ci`
- Frontend checks: `cd frontend; npm run lint`, `cd frontend; npm run typecheck`, `cd frontend; npm run build`
- Frontend smoke server: `cd frontend; npm run start -- --hostname 0.0.0.0 --port 3000`
- Frontend dev server: `cd frontend; npm run dev`
- Playwright browser install: `python -m playwright install chromium`
- Browser smoke: `python tests/e2e/playwright/run_smoke_suite.py` after local backend/frontend services are running
- Browser demo rehearsal: `python tests/e2e/playwright/rehearse_seeded_demo.py`
- Direct smoke entrypoints: `python tests/e2e/playwright/public_scholarship_browse_smoke.py`, `python tests/e2e/playwright/auth_dashboard_smoke.py`, `python tests/e2e/playwright/seeded_recommendations_smoke.py`, `python tests/e2e/playwright/document_feedback_smoke.py`, `python tests/e2e/playwright/interview_practice_smoke.py`, `python tests/e2e/playwright/curation_smoke.py`

## Key Files
- [`opencode.json`](opencode.json) is the current source of truth for agent-facing workflow configuration and plugin selection in this workspace.
- [`.codex/AGENTS.md`](.codex/AGENTS.md) contains additional repository-specific guidance on mission, architecture defaults, and documentation-first behavior.
- [`.github/workflows/ci.yml`](.github/workflows/ci.yml) is the source of truth for CI validation and smoke coverage.
- [`frontend/package.json`](frontend/package.json) defines the active frontend scripts and npm workflow.
- [`tests/e2e/README.md`](tests/e2e/README.md) documents the current smoke coverage and rehearsal expectations.
- [`docker-compose.yml`](docker-compose.yml) defines the local multi-service runtime stack.
