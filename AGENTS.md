# Agent Instructions

## Workflow
- Follow the project-local instruction set declared in [`opencode.json`](C:/Users/HP/scholarai-platform/opencode.json):
  - Plugin: `ecc-universal`
  - `skills/tdd-workflow/SKILL.md`
  - `skills/security-review/SKILL.md`
  - `skills/coding-standards/SKILL.md`
  - `skills/backend-patterns/SKILL.md`
  - `skills/e2e-testing/SKILL.md`
  - `skills/verification-loop/SKILL.md`
  - `skills/api-design/SKILL.md`
- CI automation is defined in [`.github/workflows/ci.yml`](C:/Users/HP/scholarai-platform/.github/workflows/ci.yml) and currently runs backend sanity, KPI regression, frontend sanity, docs governance, and browser smoke jobs.
- Mandatory push gate: before any push to GitHub, run all backend unit/integration checks and the full CI-equivalent local suite (backend sanity, KPI regression, frontend lint/type/build, docs governance, and browser smoke) and only push after all pass.
- No additional agent-local workflow config was discovered in this workspace snapshot beyond [`opencode.json`](C:/Users/HP/scholarai-platform/opencode.json), including under [`frontend/`](C:/Users/HP/scholarai-platform/frontend).

## Commands
- Root stack: `docker compose up --build`
- Backend setup: `python -m pip install -r backend/requirements.txt`
- Backend bootstrap: `cd backend; python scripts/bootstrap_local.py`
- Backend tests: `pytest backend/tests/unit backend/tests/integration -q`
- Backend dev server: `cd backend; python -m uvicorn app.main:app --reload`
- Frontend setup: `cd frontend; npm ci`
- Frontend checks: `cd frontend; npm run lint`, `cd frontend; npm run typecheck`, `cd frontend; npm run build`
- Frontend dev server: `cd frontend; npm run dev`
- Browser smoke: `python tests/e2e/playwright/run_smoke_suite.py` after local backend/frontend services are running

## Key Files
- [`opencode.json`](C:/Users/HP/scholarai-platform/opencode.json) is the current source of truth for agent-facing workflow configuration and plugin selection in this workspace.
- [`.github/workflows/ci.yml`](C:/Users/HP/scholarai-platform/.github/workflows/ci.yml) is the source of truth for CI validation and smoke coverage.
- [`frontend/package.json`](C:/Users/HP/scholarai-platform/frontend/package.json) defines the active frontend scripts and npm workflow.
- [`docker-compose.yml`](C:/Users/HP/scholarai-platform/docker-compose.yml) defines the local multi-service runtime stack.
