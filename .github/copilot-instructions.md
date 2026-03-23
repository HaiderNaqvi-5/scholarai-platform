# ScholarAI AI Coding Agent Instructions

## Mission & Delivery Model
ScholarAI is a **modular monolith** scholarship platform built by 3 developers in 16 weeks. Assistance must remain feasible within these constraints—avoid microservices, heavy orchestration, or infrastructure assumptions beyond Docker Compose.

**Key principle**: Prefer the simplest defensible solution. Separate recommendations into MVP / Future Research Extensions / Post-MVP Startup Features.

---

## Architecture (Essential Knowledge)

### Modular Monolith Stack
- **Frontend**: Next.js 16 + React 19 + TypeScript + TailwindCSS (one app serving students and admins)
- **Backend**: FastAPI (one app with internal service modules, not separate deployables)
- **Async**: Celery + Redis (background jobs only—don't create new services)
- **Primary data**: PostgreSQL + pgvector (vector search built-in, no separate search engine by default)
- **Knowledge Graph Layer**: Mandatory as a logical concept; MVP uses relational abstraction (not Neo4j unless justified)
- **Deployment**: Docker Compose; migrations via Alembic; CI/CD via GitHub Actions

### Backend Module Boundaries
Each service module owns one domain and has clear input/output contracts:

| Module | Routes | Owns | Must Not Own |
|--------|--------|------|-------------|
| `auth` | `/auth/*` | JWT tokens, role checks, session lifecycle | Scholarship data |
| `students` | `/profile` | Student profile CRUD | Recommendations |
| `scholarships` | `/scholarships/*` | Discovery, detail, publication workflow | Document feedback |
| `recommendations` | `/recommendations` | Ranking + explanations (eligibility → scoring → output) | Curation writes |
| `documents` | `/documents/*` | Upload lifecycle, feedback requests | Scholarship truth |
| `interviews` | `/interviews/*` | Practice sessions, rubric outputs | Student scoring logic |
| `curation` | `/curation/*` | Ingestion review, publish/unpublish (raw → validated → published) | Recommendation ranking |

**Critical pattern**: Services use dependency injection via `AsyncSession` (database) and call shared utilities in `scholarai_common/`.

### Data Flow: Core Workflows
1. **Discovery**: Student → `/scholarships` (PostgreSQL read-model, public records only)
2. **Recommendations**: Student profile + eligibility rules (Knowledge Graph Layer) → pgvector retrieval → ranking → explanation
3. **Documents**: Student uploads → extraction → AI feedback (with grounded context sections) → mentor review
4. **Curation**: Raw ingestion → validation → publish (triggers read-model rebuild)

---

## Critical Developer Workflows

### Local Run (Docker Compose)
```bash
docker compose up --build
# Backend applies migrations + seeds demo data
# Frontend: http://localhost:3000
# Docs: http://localhost:8000/docs
```

### Local Run (Direct)
```bash
# Terminal 1: Backend (Python 3.12)
cd backend
pip install -r requirements.txt
python scripts/bootstrap_local.py  # Apply migrations + seed
uvicorn app.main:app --reload

# Terminal 2: Frontend
cd frontend
npm ci
npm run dev  # http://localhost:3000
```

### Key Commands
- **Tests**: `pytest backend/tests/` (unit + integration fixtures in `conftest.py`)
- **Lint**: `eslint` in frontend; `ruff` or `black` for backend (check setup files)
- **Migrations**: `alembic revision -m "description"` → `alembic upgrade head`
- **Celery worker**: `celery -A app.celery_app worker --loglevel=info` (from `backend/`)

### Backend Test Runtime Recommendation
- Prefer Python `3.12` for backend tests and local backend execution consistency.
- Example: `py -3.12 -m venv .venv312` then run tests via
  - `\.venv312\Scripts\python -m pytest backend/tests/unit backend/tests/integration -q`

### Important Local Note
After editing route files or app structure, restart the Next.js dev server to avoid stale `404`s.

---

## Code Patterns & Conventions

### Service Layer (Backend)
```python
# backend/app/services/<domain>/service.py
class <Domain>Service:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def method_name(self, payload: SchemaIn) -> SchemaOut:
        # Use SQLAlchemy async patterns: select(...).where(...), scalar_one_or_none()
        # Raise ScholarAIException for domain errors
        pass
```

**Pattern enforcement**:
- All database calls use `AsyncSession` (no sync blocking)
- Domain errors raise `ScholarAIException` with `ErrorCode` + status code
- Services return Pydantic `schemas.*` (never raw SQLAlchemy models)

### API Routes (FastAPI)
```python
# backend/app/api/v1/routes/<domain>.py
router = APIRouter(prefix="/<domain>", tags=["<domain>"])

@router.post("")
async def create(payload: CreateSchema, service: <Domain>Service = Depends(...)) -> ResponseSchema:
    return await service.method(payload)
```

**Pattern enforcement**:
- One `APIRouter` per domain module
- Dependencies injected via `Depends()` (not direct instantiation)
- Responses wrapped in `ErrorEnvelope` for errors; success returns typed schema
- List endpoints normalize to `{ items: [...], total: int }`

### Error Handling
```python
from scholarai_common.errors import ScholarAIException, ErrorCode

raise ScholarAIException(
    code=ErrorCode.<CODE>,
    message="User-facing message",
    status_code=400  # or 401, 404, 500
)
```

**No generic exceptions**—use `ErrorCode` enums defined in `scholarai_common/errors.py`.

### Frontend Components (Next.js)
- Layouts in `src/app/`; components in `src/components/`
- API calls via `src/lib/api.ts` (typed fetch wrapper)
- Auth token stored in memory + localStorage (check `lib/types.ts` for contract types)
- TailwindCSS v4 for styling (prefer utility-first, avoid custom CSS)

### Schemas & Contracts
- Request/response schemas in `backend/app/schemas/`
- Shared contracts in `shared/contracts/` (future expansion)
- Pydantic `BaseModel` for validation; use `Field(..., description="...")` for OpenAPI
- Enums in `backend/app/models/models.py` for domain constants

---

## Data Scope & Guardrails

### MVP Data Rules
- **Primary corpus**: Canada-first (MS Data Science, MS AI, MS Analytics)
- **USA scope**: Fulbright-related + narrowly scoped cross-border logic only
- **Deferred**: DAAD, general USA discovery
- **Source of truth**: Structured validated data (eligibility, deadlines, funding rules) — **not** AI generation

### Boundary Enforcement
- Eligibility rules = Knowledge Graph Layer (relational queries, not AI guesses)
- SOP/essay feedback = RAG-assisted (retrieved guidance + generated suggestions + limitations)
- Interview practice = LLM + feedback (not outcome prediction)

**When uncertain**: Add `limitation_notice` to API responses (see `DocumentFeedback` schema).

---

## Integration Points & Dependencies

### LangChain (RAG)
- Used for document feedback + interview prompt generation
- Entry point: `backend/app/services/documents/` and `backend/app/services/interview/`
- Embedding model: `sentence-transformers/all-MiniLM-L6-v2` (pgvector compatible)

### Celery Tasks
- Defined in `backend/app/tasks/`
- Triggered by API routes via `task.delay(...)`
- Redis broker/backend configured in `app/core/config.py`
- **Pattern**: Long-running ops (ingestion, document processing) async only

### Ingestion Pipeline
- Playwright scrapers → Pandas cleanup → Pydantic validation → Celery → PostgreSQL
- Entry: `backend/scripts/` or `POST /api/v1/curation/run`
- Output: `IngestionRun` records with provenance (raw → validated → published)

### CORS & Auth
- CORS origins in `app.core.config.Settings.CORS_ORIGINS`
- Auth: JWT via `python-jose[cryptography]` + `passlib[bcrypt]`
- Middleware injects `request.state.request_id` (X-Request-ID header)

---

## Documentation-First Approach

### When Adding Features
1. Check `docs/scholarai/` for architecture context (esp. `05_system_architecture.md`, `10_backend_api_and_repo.md`)
2. Update relevant docs **before** broad implementation if scope is unclear
3. End every doc with:
   - **MVP decision**
   - **Deferred items**
   - **Assumptions**
   - **Risks**

### Canonical Docs
- `docs/scholarai/01_executive_summary.md` — product mission
- `docs/scholarai/05_system_architecture.md` — modular monolith design
- `docs/scholarai/10_backend_api_and_repo.md` — backend layout + API contracts
- `docs/scholarai/WORKPLAN.md` — file-to-section mapping + decision matrix

---

## Testing & Validation

### Backend Tests
- Unit tests in `backend/tests/unit/`; integration in `backend/tests/integration/`
- Fixtures defined in `backend/tests/conftest.py` (app, client, async DB setup)
- Async tests via `@pytest.mark.asyncio`
- Database tests use transaction rollback (no cleanup needed)

### Frontend Tests
- Not yet structured; plan via `tests/e2e/` (Playwright-based acceptance tests)

### Smoke Checks
- `docker compose up` auto-seeds demo data (configurable via `AUTO_SEED_DEMO_DATA`)
- Check `/health` endpoint for system readiness
- Verify `/docs` (Swagger UI) reflects all routes

---

## Common Pitfalls to Avoid

1. **Microservice creep**: New feature = new service module inside FastAPI, not new deployment
2. **Async carelessness**: Always `await` database calls; never mix sync + async
3. **Generic exceptions**: Use `ScholarAIException` + `ErrorCode` enums
4. **Search engine sprawl**: Use pgvector for MVP; Neo4j/OpenSearch justified later only
5. **RAG as truth**: Eligibility rules are Knowledge Graph (relational); RAG is advisory
6. **Hardcoded secrets**: Use `.env` files; validate in production via `validate_production_settings()`
7. **Frontend stale routes**: Restart Next.js dev server after route changes
8. **Token expiry**: `ACCESS_TOKEN_EXPIRE_MINUTES` defaults to 30; check frontend for refresh logic

---

## References
- Root README: [README.md](../README.md)
- Architecture: [docs/scholarai/05_system_architecture.md](../docs/scholarai/05_system_architecture.md)
- API Design: [docs/scholarai/10_backend_api_and_repo.md](../docs/scholarai/10_backend_api_and_repo.md)
- Agent guidance: [.codex/AGENTS.md](../.codex/AGENTS.md)
- Example service: [backend/app/services/auth/service.py](../backend/app/services/auth/service.py)
- Config: [backend/app/core/config.py](../backend/app/core/config.py)

