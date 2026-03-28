<!-- Context: project-intelligence/technical | Priority: critical | Version: 1.0 | Updated: 2026-03-23 -->

# Technical Domain

ScholarAI is a modular-monolith MVP with a Next.js frontend and FastAPI backend, tuned for Canada-first scholarship workflows with KPI-gated quality controls. The architecture prioritizes deterministic policy truth (validated data) and bounded guidance generation (documents/interviews).

## Quick Reference

- **Purpose**: Keep implementation patterns aligned across API, services, and background tasks.
- **Update When**: Stack, route contracts, KPI policy thresholds, or domain boundaries change.
- **Audience**: Backend/frontend developers, QA, DevOps, coding agents.

## Primary Stack

| Layer | Technology | Rationale |
|---|---|---|
| Frontend | Next.js + React + TypeScript + TailwindCSS | Fast UI iteration with typed contracts.
| Backend API | FastAPI + Pydantic | Explicit schemas and predictable validation behavior.
| Data | PostgreSQL + pgvector | Transactional truth + semantic retrieval.
| Async | Celery + Redis | Scheduled and long-running KPI/ingestion jobs.
| Migrations | Alembic | Versioned schema evolution for CI/CD safety.
| Runtime | Docker Compose (MVP baseline) | Reproducible local and staging setup.

## Architecture Pattern

**Concept**: One deployable backend with domain-segmented services and routers.

**Key Points**
- Modular monolith over early microservices to reduce operational overhead.
- API contracts versioned through `/api/v1` and `/api/v2` prefixes.
- KPI policy versions emitted in responses for auditability.
- Health reports include KPI degradation signals in addition to DB status.

**Reference**: `docs/scholarai/05_system_architecture.md`

## API Endpoint Pattern

**Concept**: Route handlers orchestrate dependencies, service calls, and schema-safe responses; business logic lives in services.

**Key Points**
- Use dependency-injected DB sessions and auth-scoped user contexts.
- Convert domain outputs to explicit response schemas.
- Expose `policy_version` where KPI gates apply.
- Keep threshold defaults centralized, not hardcoded in routes.

```python
@router.post("/evaluate", response_model=RecommendationEvaluationResponse)
async def evaluate_recommendations(payload: RecommendationEvaluationRequest, db: AsyncSession):
    service = RecommendationEvaluationService()
    metrics = service.evaluate(predicted_ids=payload.predicted_ids, judged_relevance=payload.judged_relevance, k_values=payload.k_values)
    thresholds = payload.thresholds or get_recommendation_default_thresholds()
    gates = service.evaluate_kpi_gates(metrics=metrics, thresholds=thresholds, baseline_metrics=[])
    return RecommendationEvaluationResponse(metrics=[...], kpi_gates=[...], policy_version=get_recommendation_kpi_policy_version())
```

**Reference**: `backend/app/api/v1/routes/recommendations.py`

## Component Pattern (Frontend)

**Concept**: Typed functional components with utility-first styling and API-driven state.

**Key Points**
- Prefer TypeScript interfaces for props and API payload contracts.
- Keep presentational components stateless where possible.
- Keep API side effects in route-level hooks/services, not deeply nested UI elements.
- Follow shared design tokens and Canada-first copy constraints.

```tsx
interface ScholarshipCardProps {
  title: string
  provider: string
  fitScore?: number
}

export function ScholarshipCard({ title, provider, fitScore }: ScholarshipCardProps) {
  return <article className="rounded-lg border p-4">{title} - {provider} ({fitScore ?? "N/A"})</article>
}
```

**Reference**: `docs/scholarai/03_brand_and_design_system.md`

## Naming Conventions

| Type | Convention | Example |
|---|---|---|
| Python modules | `snake_case.py` | `kpi_snapshot_service.py` |
| Python classes | `PascalCase` | `KPISnapshotService` |
| Python functions | `snake_case` | `record_document_snapshot` |
| API routes | resource-oriented plural nouns | `/api/v1/recommendations/evaluate` |
| Docs files | uppercase topic + date for reports | `KPI_MATURITY_STATUS_20260322.md` |

## Code Standards

**Concept**: Contracts first, policy centralization, and test-backed behavior changes.

**Key Points**
- Use Pydantic schemas for request/response boundaries.
- Keep KPI thresholds in policy/config helpers (`kpi_policy`, `config`).
- Preserve service-layer separation for domain logic.
- Add integration/unit tests for every contract or policy change.
- Keep Canada-first scope constraints explicit and machine-readable.

**Reference**: `docs/scholarai/10_backend_api_and_repo.md`

## Security Requirements

**Concept**: Validate input early, protect auth boundaries, and enforce safe production defaults.

**Key Points**
- Validate all request payloads through Pydantic models.
- Require authenticated access for protected routes.
- Use SQLAlchemy ORM/session boundaries to avoid unsafe SQL composition.
- Enforce production guardrails (`SECRET_KEY`, DB/Neo4j default checks).
- Treat generated coaching as guidance, not policy truth.

**Reference**: `backend/app/core/config.py`

## 📂 Codebase References

- **API bootstrap and middleware**: `backend/app/main.py`
- **Recommendation KPI route contracts**: `backend/app/api/v1/routes/recommendations.py`
- **Document coaching + KPI snapshot recording**: `backend/app/services/documents/service.py`
- **KPI thresholds and runtime settings**: `backend/app/core/config.py`
- **ScholarAI canonical architecture and scope docs**: `docs/scholarai/README.md`

## Related Files

- `business-domain.md`
- `business-tech-bridge.md`
- `decisions-log.md`
- `living-notes.md`
