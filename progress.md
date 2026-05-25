# progress.md

**Date:** 2026-05-26
**Branch:** `scraper/stealth-cleanup` (off `s92/cve-bumps`)

## Completed this session
- **Scraper stealth + legacy cleanup (2026-05-25):**
  - Added `playwright-stealth==1.0.6` pin in `backend/requirements.txt`.
  - Wired stealth + `HTTP_PROXY`/`HTTPS_PROXY` honor + structured fallback telemetry into `_capture_source_once`.
  - Deleted `backend/legacy/services/scraper_service.py` (orphan, banned by CLAUDE.md).
- **Staggered ingestion + beat health + admin nightly status (2026-05-26):**
  - 4 new settings in `core/config.py`: `INGESTION_STAGGER_SECONDS=300`, `INGESTION_STALE_HOURS=26`, `INGESTION_HEALTH_CHECK_INTERVAL_MINUTES=30`, `ADMIN_ALERT_EMAIL=None`.
  - `celery_app.py` beat_schedule gains `"ingestion-health-check"` entry every 30 min.
  - `scraper_tasks.py` rewritten:
    - `_run_nightly_ingestion_async` now queries active `SourceRegistry` rows and fans out per-source `apply_async` with `countdown = index * stagger_seconds`. Falls back to legacy `nightly_sync_main` when no active sources.
    - New `run_ingestion_health_check` task — `logger.error` + Sentry capture_message + admin email when last completion is stale beyond threshold. All fail-soft.
  - `schemas/curation.py` + `schemas/__init__.py` expose new `NightlyStatusResponse`.
  - `IngestionService.get_nightly_status` rolls up last-run + per-source health + next-expected 02:00 UTC ETA. Reuses `list_source_health`.
  - `routes/curation.py` new `GET /api/v1/curation/ingestion-runs/nightly-status` declared BEFORE `/{run_id}` (UUID-parse collision avoidance).
  - Frontend: `types.ts` + `endpoints/curation.ts` + new `_components/NightlyStatusBanner.tsx` (30s react-query refetch, status pill, per-source grid). Mounted at top of `/admin/ingestion`.
- **Tests:** +4 unit. Full unit suite **400 pass + 1 xfailed** (baseline 396 + 1; matches expected).
- **Compile:** backend `compileall` clean; frontend `tsc --noEmit` clean.

## In progress
None.

## Open / blockers
- Worker + beat image rebuild required to pick up `playwright-stealth` install AND new `"ingestion-health-check"` beat entry: `docker compose build celery-worker celery-beat backend`.
- `ADMIN_ALERT_EMAIL` env not set anywhere yet — production will need this in DO app spec / `.env.production` to actually deliver alerts (otherwise log-only).
- Frontend `bun run lint` + `bun run build` not run in this session (only `tsc --noEmit` checked).
- Browser smoke selector re-point + `ci.yml:198` `continue-on-error` removal still deferred (carried over from S91).

## Other active branches (untouched here)
- `s90/audit-remediation` — PR #100 open, 19 commits, frontend audit remediation.
- `s92/cve-bumps` — parent of this branch; CVE bumps in flight.

## Files touched
**Backend:**
- `backend/requirements.txt` — `playwright-stealth==1.0.6` added.
- `backend/app/core/config.py` — 4 new ingestion settings.
- `backend/app/tasks/celery_app.py` — `"ingestion-health-check"` beat entry.
- `backend/app/tasks/scraper_tasks.py` — staggered fan-out + health check task + `os`/`settings`/`send_email` imports.
- `backend/app/services/ingestion/service.py` — stealth/proxy/telemetry on `_capture_source_once`; new `get_nightly_status` method; `timedelta` import added.
- `backend/app/schemas/curation.py` — `NightlyStatusResponse` + `uuid` import.
- `backend/app/schemas/__init__.py` — `NightlyStatusResponse` re-export.
- `backend/app/api/v1/routes/curation.py` — new `GET /ingestion-runs/nightly-status` route.
- `backend/legacy/services/scraper_service.py` — **deleted**.
- `backend/tests/unit/test_scraper_tasks.py` — `FakeSession.execute` stub + 4 new tests.

**Frontend:**
- `frontend/src/lib/api/types.ts` — `SourceHealthSummary` + `NightlyStatusResponse` types.
- `frontend/src/lib/api/endpoints/curation.ts` — `nightlyStatus()` client.
- `frontend/src/app/(admin)/admin/ingestion/_components/NightlyStatusBanner.tsx` — **new**.
- `frontend/src/app/(admin)/admin/ingestion/page.tsx` — mount banner above runs list.

**Docs:**
- `CLAUDE.md` — appended 2 new sections (scraper stealth + staggered ingestion).
- `progress.md` — this file.

## Resume commands
```powershell
Set-Location C:\Users\HP\scholarai-platform
git status
# verify
Set-Location backend
python -m pytest tests/unit -q                                # expect 400 pass + 1 xfailed
python -m compileall app tests -q
Set-Location ..\frontend
bunx --bun tsc --noEmit
bun run lint
bun run build
# rebuild containers to pick up new beat entry + playwright-stealth
Set-Location ..
docker compose build celery-worker celery-beat backend
docker compose up celery-worker celery-beat backend redis postgres
# manual API check
$token = (Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/auth/login -Body (@{username="admin@example.com";password="strongpass1"} | ConvertTo-Json) -ContentType "application/json").access_token
Invoke-RestMethod -Uri http://localhost:8000/api/v1/curation/ingestion-runs/nightly-status -Headers @{ Authorization = "Bearer $token" }
```

## Notes
- Staggered fan-out uses `apply_async(countdown=...)` over a single beat — no `redbeat`, no custom scheduler, no migration. Scaling to per-source crontabs (Chevening hourly vs Fulbright weekly) would require a future alembic migration + `SourceRegistry.schedule_cron` column.
- Beat health check is poll-based (30 min). Alert latency ≤ 30 min after the beat misses.
- Route order intentional: `GET /ingestion-runs/nightly-status` must precede `GET /ingestion-runs/{run_id}` or FastAPI parses the literal as a UUID and 422s.
- `send_email` requires a `User`-like object with `.email`. The health task passes `types.SimpleNamespace(email=ADMIN_ALERT_EMAIL)` to keep the existing signature stable without bypassing the Mailgun fail-soft path.
- This branch carries the s92/cve-bumps dirty tree; when staging for PR, include only the files listed above.
