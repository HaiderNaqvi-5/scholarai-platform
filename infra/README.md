# Infrastructure

This directory holds environment, container, and deployment notes for ScholarAI.

Current MVP stance:
- Keep infrastructure simple and local-first.
- Docker Compose remains the default development and demo orchestration layer.
- Avoid production-grade orchestration or heavy observability in this phase.

Local demo baseline:
1. Copy `.env.example` to `.env` only if you need to override defaults.
2. Run `docker compose up --build`.
3. Wait for backend bootstrap to apply Alembic migrations and seed demo data.
4. Verify `http://localhost:8000/health`.
5. If the frontend route set changed since the last run, restart the frontend process or rerun `docker compose up --build`.
6. Use the backend bootstrap path if you are running services directly outside Docker.
