# Infrastructure

This directory holds environment, container, and deployment notes for ScholarAI.

Current MVP stance:
- Keep infrastructure simple and local-first.
- Docker Compose remains the default development and demo orchestration layer.
- Avoid production-grade orchestration or heavy observability in this phase.

Local demo baseline:
1. Run `docker compose up --build`.
2. Copy `.env.example` to `.env` only if you need to override defaults.
3. Use the backend bootstrap path if you are running services directly outside Docker.
