# Progress — 2026-05-12 (session: healthcheck architecture)

**Branch:** `master`

## Tasks completed
- Diagnosed false-unhealthy on `backend`, `celery-worker`, `celery-beat`. Root causes:
  - `backend/Dockerfile` baked `HEALTHCHECK curl /api/v1/health` into the image. Celery services share the same image but don't run uvicorn → curl always failed (`Failed to connect to localhost port 8000`).
  - `/api/v1/health` performs DB ping + `KPISnapshotService.alert_messages` (3 aggregate queries over `*_kpi_snapshots` tables). Under cold cache or pool pressure the call exceeded the 5s healthcheck timeout, producing intermittent unhealthy → restart risk.
  - `neo4j` healthcheck used `cypher-shell` (JVM cold-start) → 5s timeouts during recreate.
- Implemented liveness/readiness split (Kubernetes-style):
  - `GET /livez` — returns `{"status":"alive"}`, no I/O. ~70ms.
  - `GET /readyz` — DB `SELECT 1` only, returns 503 on failure. ~37ms.
  - `GET /health` — unchanged, still serves DB + KPI alerts payload for ops dashboards.
- Removed `HEALTHCHECK` directive from `backend/Dockerfile`. Image is now process-agnostic.
- Moved all healthchecks to `docker-compose.yml` (orchestration layer):
  - `backend` → `curl /livez` (interval 30s, timeout 5s, start_period 30s).
  - `celery-worker` → `celery inspect ping -d celery@$HOSTNAME` (interval 60s, timeout 15s, start_period 45s).
  - `celery-beat` → `grep beat /proc/1/cmdline` (interval 60s, timeout 10s, start_period 30s).
  - `neo4j` → bash TCP probe on 7687 (interval 15s, timeout 5s, start_period 30s).
- Rebuilt `scholarai-platform-backend:latest`, recreated stack. All 8 containers report `(healthy)` or `Up`.

## Files touched
- `backend/Dockerfile` — removed HEALTHCHECK directive, added explanatory comment.
- `backend/app/main.py` — added `/livez` and `/readyz` routes alongside existing `/health`.
- `docker-compose.yml` — explicit healthcheck blocks for backend, celery-worker, celery-beat, neo4j.
- `CLAUDE.md` — appended dev-env note documenting the new healthcheck architecture.
- `progress.md` — this file.

## In-progress / next
- Frontend container has no healthcheck. Low priority (nothing depends on it), but adding one keeps the pattern consistent.
- `broker_connection_retry` deprecation warning in celery (cosmetic) — set `broker_connection_retry_on_startup=True` in `app/tasks/celery_app.py` next time that file is touched. Skipped this session per "no cosmetic" instruction.

## Open bugs / blockers
- None known. Login/signup flow still works (verified earlier: `/auth/refresh`, `/auth/me`, `/profile`, `/saved-opportunities` returning 200).

## Commands to resume
- Stack: `cd scholarai-platform && docker compose up -d`
- Verify health: `docker ps --format "table {{.Names}}\t{{.Status}}"`
- Probe endpoints: `curl http://localhost:8000/livez`, `/readyz`, `/health`
- Backend API: `cd backend && python -m uvicorn app.main:app --reload`
- Tests: `pytest backend/tests/unit backend/tests/integration -q`
