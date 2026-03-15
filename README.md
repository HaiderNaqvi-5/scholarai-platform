# ScholarAI Platform

This repository contains the initial ScholarAI monorepo scaffold aligned with the documentation pack in `docs/scholarai/`. The documented MVP remains a Canada-first, modular monolith with a Next.js web app, FastAPI API, Celery workers, PostgreSQL, Redis, and low-ops Docker Compose environments.

## Authoritative Documentation

- `docs/scholarai/README.md` is the entrypoint for the ScholarAI documentation pack.
- `docs/scholarai/WORKPLAN.md` and the numbered docs define the MVP scope, architecture, data-trust rules, and roadmap.
- Older legacy directories remain in the repo for now, but the new scaffold below is the intended monorepo shape for the documented MVP.

## Monorepo Scaffold

```text
scholarai-platform/
|-- apps/
|   |-- api/
|   \-- web/
|-- workers/
|-- shared/
|-- infra/
|-- tests/
|-- docs/
|   \-- scholarai/
|-- backend/      # legacy implementation baseline retained during scaffold setup
|-- frontend/     # legacy implementation baseline retained during scaffold setup
\-- ai_services/  # legacy experiments retained during scaffold setup
```

## MVP Guardrails

- Keep the MVP as a modular monolith.
- Treat structured validated data as the source of truth.
- Keep scope Canada-first, with `Fulbright-related USA scope` only where explicitly allowed.
- Keep `DAAD deferred`.
- Do not treat optional graph or search infrastructure as mandatory day-one runtime dependencies.
