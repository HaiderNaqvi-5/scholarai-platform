# Docker Notes

ScholarAI uses Docker Compose as the default local development and demo environment.

MVP defaults for the first coding phase:
- `frontend`
- `backend`
- `postgres`
- `redis`
- `celery-worker`

Current local demo notes:
- `backend` runs `python scripts/bootstrap_local.py` before Uvicorn so a fresh local database can be initialized for demo use.
- `frontend` expects `NEXT_PUBLIC_API_BASE_URL` from the root `.env` file during Docker Compose runs.
- `celery-worker` uses `app.tasks.celery_app:celery_app`.

Deferred from the active default compose:
- Neo4j
- OpenSearch
- extra scheduler services unless they become immediately necessary
