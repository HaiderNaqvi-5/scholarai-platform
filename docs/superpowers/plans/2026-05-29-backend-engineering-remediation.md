# Backend Engineering Remediation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the 30 engineering-standard gaps (E1–E30) found in the 2026-05-29 backend audit — concurrency, data integrity, test confidence, observability, architecture, API/dependency hygiene — without regressing the green test suite or shipping behavior changes silently.

**Architecture:** Fix in dependency order. Build a real-DB test safety net and CI gates FIRST (Phase 0) so every later behavioral change is verifiable. Then data integrity (Phase 1), concurrency/perf (Phase 2), observability/resilience (Phase 3), architecture cleanup (Phase 4), API/dependency hygiene (Phase 5), and test depth (Phase 6). Each phase ends green and is independently shippable.

**Tech Stack:** FastAPI, SQLAlchemy 2 async, asyncpg, Alembic, Celery+Redis, pgvector/Postgres 16, Anthropic SDK, sentence-transformers, pytest + pytest-asyncio, GitHub Actions.

**Scope note:** This is a master plan across 6 independent workstreams. Phases 0–2 are the high-value core and can ship as their own PR series. Phases 4–6 are largely mechanical and can be parallelized once Phase 0 lands. The two large refactors (E7 IngestionService split, E14 route→service extraction) are scoped here as decomposition + interfaces; each needs its own detailed sub-plan written at execution time after reading the target files in full — do NOT improvise their internals from this document.

**Decisions baked in (override before executing if wrong):**
- **D-A (E5):** The 5 orphan `student_profiles` columns from migration `0019` are *intended* → ADD to the ORM model (not drop). Source: CLAUDE.md says StudentProfile is 28 fields incl. financial/research; frontend type already has them.
- **D-B (E20/E21):** Dead/heavy deps removed only after a grep proves zero runtime imports (task includes the proof step).
- **D-C (E13):** `app/api/v2` is a stub re-mounting v1 with no external consumers → DELETE.

**Baseline commands (run before starting, record the numbers):**
```bash
cd backend && pytest tests/unit tests/integration -q          # record pass count (~561 + 1 xfail)
cd backend && python -c "from app.main import create_app; print(len(create_app().routes))"
```

---

## Phase 0 — Safety net & CI gates (BLOCKS everything else)

Rationale: E6 found 0 real-DB tests; you cannot safely verify E1/E4/E5/E19 without one. E8 found CI and local run different pytest majors. Fix the harness before touching product code.

### Task 0.1: Fix CI/local runner version split (E8)

**Files:**
- Modify: `backend/requirements.txt` (remove test-only pins) and `backend/requirements-dev.txt`
- Modify: `.github/workflows/ci.yml` (backend job install step)

- [ ] **Step 1:** Read `backend/requirements.txt` lines 43-49 and `backend/requirements-dev.txt`. Confirm the conflict: root `pytest==8.3.0`/`pytest-asyncio==0.24.0` vs dev `pytest==9.0.3`/`pytest-asyncio==1.3.0`.
- [ ] **Step 2:** Move `pytest`, `pytest-asyncio`, `playwright` OUT of `requirements.txt` into `requirements-dev.txt`. Keep ONE pinned version each (use the dev pins: `pytest==9.0.3`, `pytest-asyncio==1.3.0`). Leave runtime-required `clerk-backend-api`, `svix` in `requirements.txt`.
- [ ] **Step 3:** In `.github/workflows/ci.yml`, change the backend install to `pip install -r requirements.txt -r requirements-dev.txt`.
- [ ] **Step 4:** Run `cd backend && pip install -r requirements.txt -r requirements-dev.txt && pytest tests/unit -q`. Expected: same pass count as baseline, single pytest version.
- [ ] **Step 5:** Commit: `chore(deps): unify pytest version across CI and local; split test deps out of prod requirements`.

### Task 0.2: Add asyncio_mode=auto, drop blanket marks (E30 async-mark)

**Files:** Modify `backend/pytest.ini`

- [ ] **Step 1:** Read `backend/pytest.ini`. Add under `[pytest]`: `asyncio_mode = auto`.
- [ ] **Step 2:** Grep the 16 files with module-level `pytestmark = pytest.mark.asyncio`: `grep -rln "pytestmark = pytest.mark.asyncio" tests/`. In each, remove the blanket mark (auto mode handles coroutine tests; sync tests like `test_document_service.py:286` must no longer inherit it).
- [ ] **Step 3:** Run `pytest tests/unit -q`. Expected: same pass count; verify previously-skipped sync test now actually runs (`pytest tests/unit/test_document_service.py -v` shows it executed, not skipped).
- [ ] **Step 4:** Commit: `test: enable asyncio_mode=auto; remove blanket asyncio marks`.

### Task 0.3: Real-DB test fixture (E6) — THE keystone

**Files:**
- Modify: `backend/tests/conftest.py` (add transactional async session + client fixtures)
- Reference: `backend/tests/db/conftest.py` (existing SQLite fixture pattern), `backend/app/core/database.py`, `backend/app/core/dependencies.py` (`get_db`)

- [ ] **Step 1:** Read `backend/tests/db/conftest.py`, `app/core/database.py`, and how `get_db` is defined/overridden in existing integration tests.
- [ ] **Step 2:** Add to `backend/tests/conftest.py` a session-scoped async engine + function-scoped transactional session fixture that rolls back per test, plus an `app_client` fixture that wires `dependency_overrides[get_db]` to it. Use Postgres when `TEST_DATABASE_URL` is set, else fall back to async SQLite for local unit runs:

```python
import os
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.models.models import Base
from app.core.dependencies import get_db
from app.main import create_app

TEST_DB_URL = os.getenv("TEST_DATABASE_URL", "sqlite+aiosqlite:///:memory:")

@pytest_asyncio.fixture(scope="session")
async def _engine():
    engine = create_async_engine(TEST_DB_URL, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session(_engine) -> AsyncSession:
    conn = await _engine.connect()
    txn = await conn.begin()
    Session = async_sessionmaker(bind=conn, expire_on_commit=False)
    session = Session()
    try:
        yield session
    finally:
        await session.close()
        await txn.rollback()
        await conn.close()

@pytest_asyncio.fixture
async def app_client(db_session) -> AsyncClient:
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
```

- [ ] **Step 3:** Add `aiosqlite` to `requirements-dev.txt` if absent. Note pgvector/ARRAY columns won't create under SQLite — for those models the Postgres path (`TEST_DATABASE_URL`) is required; document this in a comment.
- [ ] **Step 4:** Write ONE proof test that exercises real SQL through the fixture (pick a simple owned-resource read, e.g. tracker list), asserting it returns rows inserted via `db_session`. Run it. Expected: PASS against a real session (not a fake).
- [ ] **Step 5:** Commit: `test: add transactional real-DB session + ASGI client fixtures`.

### Task 0.4: Postgres-backed integration CI job (E6, E9)

**Files:** Modify `.github/workflows/ci.yml`

- [ ] **Step 1:** Add a `backend-integration` job using `services: postgres: image: pgvector/pgvector:pg16` + a redis service, env `TEST_DATABASE_URL=postgresql+asyncpg://...`, steps: checkout → setup-python → install → `alembic upgrade head` → `pytest tests/integration -q`.
- [ ] **Step 2:** Add at workflow root: `concurrency: { group: ${{ github.workflow }}-${{ github.ref }}, cancel-in-progress: true }` and `permissions: { contents: read }` (also closes sec-audit N34). Add pip caching to setup-python.
- [ ] **Step 3:** Push branch, confirm the new job runs green on CI.
- [ ] **Step 4:** Commit: `ci: add Postgres-backed integration job, concurrency cancel, least-privilege permissions`.

### Task 0.5: Coverage gate (E9)

**Files:** Modify `requirements-dev.txt`, `pytest.ini`, `.github/workflows/ci.yml`

- [ ] **Step 1:** Add `pytest-cov` to `requirements-dev.txt`.
- [ ] **Step 2:** Run `pytest tests/unit tests/integration --cov=app --cov-report=term-missing -q` locally; record the baseline % .
- [ ] **Step 3:** In `pytest.ini` add `addopts = --cov=app --cov-fail-under=<baseline_minus_2>` (set floor 2 pts below current so the gate ratchets, never regresses). Document the number.
- [ ] **Step 4:** Commit: `ci: add coverage measurement with regression floor`.

**Phase 0 gate:** CI runs unit + Postgres-integration + coverage, single pytest version, concurrency + permissions hardened. STOP and confirm green before Phase 1.

---

## Phase 1 — Data integrity

### Task 1.1: Close ORM↔DB drift on StudentProfile + User (E5) — DECISION D-A

**Files:**
- Modify: `backend/app/models/models.py` (`StudentProfile`, `User`)
- Test: `backend/tests/db/test_student_profile_columns.py` (new)
- Reference: `alembic/versions/20260513_0019_b2b_data_expansion.py`, `20260511_0014_*` (plan CHECK)

- [ ] **Step 1:** Re-read migration `0019` lines 35-101. Confirmed columns to add to `StudentProfile`: `current_university_id` (UUID FK→universities.id, nullable), `target_university_ids` (ARRAY/JSON per migration type, nullable), `gmat_score` (Integer), `sat_score` (Integer), `budget_pkr_max` (Integer). Note the 3 CHECKs (gmat 200-800, sat 400-1600, budget>=0) and the FK + GIN index.
- [ ] **Step 2:** Write failing test: load the ORM, assert `StudentProfile.__table__.columns` contains all 5 names and a CheckConstraint exists for each bound. Run against Postgres fixture. Expected: FAIL (columns missing).
- [ ] **Step 3:** Add the 5 mapped columns to `StudentProfile` with matching types, the FK on `current_university_id`, and `__table_args__` CheckConstraints mirroring the migration (use the SAME constraint names as `0019` so Alembic sees them as managed). Add `User.plan` as a CheckConstraint (or Enum) matching `0014`'s `ck_users_plan_allowed`.
- [ ] **Step 4:** Run the test. Expected: PASS. Then run full suite — expect no regression.
- [ ] **Step 5:** Commit: `fix(models): sync StudentProfile + User.plan to migrations 0019/0014 (close ORM drift)`.

### Task 1.2: Enable Alembic drift detection (E5, E9)

**Files:** Modify `backend/alembic/env.py`, `.github/workflows/ci.yml`

- [ ] **Step 1:** In `env.py`, add `compare_type=True` (if not already) and `compare_server_default=True` to both `context.configure(...)` calls (offline + online).
- [ ] **Step 2:** Locally run `alembic upgrade head` against the integration Postgres, then `alembic check`. Fix any drift it now reports (after Task 1.1 the StudentProfile/User drift should be gone; resolve anything residual by adding to the model or writing a corrective migration — do NOT auto-generate a destructive DROP).
- [ ] **Step 3:** Add an `alembic check` step to the `backend-integration` CI job (after `alembic upgrade head`).
- [ ] **Step 4:** Commit: `ci(db): enable compare_server_default + alembic check drift gate`.

### Task 1.3: JSONB + missing indexes (E25, E26)

**Files:** Modify `backend/app/models/models.py`; new migration `alembic/versions/20260529_0030_jsonb_and_indexes.py`

- [ ] **Step 1:** Identify the `JSON`→`JSONB` candidates (`run_metadata`, `feedback_payload`, `score_payload`, audit before/after, KPI payloads) and the unindexed lookup columns (`Scholarship.category`, `Scholarship.external_source_id`). Decide `ReferralEnrollment.university_id` FK addition.
- [ ] **Step 2:** Change the model column types to `postgresql.JSONB` and add `index=True` / `Index(...)` + the FK.
- [ ] **Step 3:** `alembic revision --autogenerate -m "jsonb and indexes"`; review the generated migration line-by-line (autogenerate now trustworthy post-1.2). Use `USING ... ::jsonb` casts for the type changes; create indexes `CONCURRENTLY` inside an `autocommit_block()`.
- [ ] **Step 4:** Run `alembic upgrade head` then `alembic downgrade -1` then `upgrade head` on the integration DB. Expected: clean round-trip.
- [ ] **Step 5:** Commit: `perf(db): migrate hot JSON columns to JSONB; index category/external_source_id; add ReferralEnrollment FK`.

**Phase 1 gate:** `alembic check` clean; migration up/down round-trips; suite green.

---

## Phase 2 — Concurrency & performance

These change runtime behavior — every task here is verified through the Phase 0 real-DB/client fixture.

### Task 2.1: Unblock the event loop for the Anthropic SDK (E1)

**Files:** Modify `backend/app/services/llm/anthropic_client.py` (`_raw_call` ~126-139, callers in `complete_with_accounting`)

- [ ] **Step 1:** Read the full `anthropic_client.py`. Confirm `_raw_call` is sync and called from an `async def`.
- [ ] **Step 2:** Lowest-risk fix (keeps accounting logic + sync SDK client intact): make the async caller offload the sync call — `result = await anyio.to_thread.run_sync(self._raw_call, <args>)`. Add `import anyio`. Do NOT swap to `AsyncAnthropic` (larger blast radius) unless a follow-up decides to.
- [ ] **Step 3:** Add a test (real-client fixture) that fires 5 concurrent requests to an LLM-backed endpoint with the deterministic-fallback path (no API key) and asserts they are served concurrently (total time ≈ slowest, not sum). Run. Expected: PASS.
- [ ] **Step 4:** Full suite green. Commit: `perf(llm): offload sync Anthropic SDK call to threadpool (stop blocking event loop)`.

### Task 2.2: Offload SentenceTransformer encode + warm at startup (E2)

**Files:** Modify `backend/app/services/recommendations/service.py:299,308`, `backend/app/services/documents/retriever.py:44,85`, `backend/app/main.py` (startup)

- [ ] **Step 1:** Wrap each `.encode(...)` call in `await anyio.to_thread.run_sync(self._embedder.encode, text)`. Make model load lazy (module-level singleton) so it loads once.
- [ ] **Step 2:** Add a FastAPI lifespan/startup hook that warms the embedder (calls `.encode("warmup")` in a thread) so the first request doesn't pay the ~400 MB load on the loop.
- [ ] **Step 3:** Test: concurrent `/recommendations` requests served concurrently (as 2.1). Run. Expected PASS.
- [ ] **Step 4:** Commit: `perf(reco): offload embedding encode to threadpool; warm model at startup`.

### Task 2.3: Configure the DB connection pool (E3)

**Files:** Modify `backend/app/core/database.py:6-9`

- [ ] **Step 1:** Current engine sets only `pool_pre_ping=True`. Add `pool_size=20, max_overflow=10, pool_recycle=1800`. Keep these env-overridable via new `settings.DB_POOL_SIZE` etc. (add to `config.py` with sane defaults).
- [ ] **Step 2:** Verify boot: `python -c "from app.core.database import engine; print(engine.pool.size())"`. Expected: 20.
- [ ] **Step 3:** Commit: `perf(db): configure async pool size/overflow/recycle (was defaults)`.

### Task 2.4: Push `/scholarships` filtering into SQL (E4)

**Files:** Modify `backend/app/api/v1/routes/scholarships.py:110-156` (and `services/scholarships/match_service.py:276-284`)

- [ ] **Step 1:** Read the full filter block. Enumerate the 8 filters (query/field_tag/degree/provider/funding/amount/deadline + sort) currently applied in Python.
- [ ] **Step 2:** Port each filter to a SQLAlchemy `where(...)` condition on the `select(Scholarship)` statement; apply ordering in SQL; apply `.limit(page_size).offset((page-1)*page_size)`. Run `count()` as a separate scalar for the total. JSON `field_tags` filter: until E25 makes it JSONB+GIN, use the Postgres JSON containment operator or a temporary `func` filter — note the dependency on Task 1.3 for index efficiency.
- [ ] **Step 3:** Test (real DB): seed 50 scholarships, request page 2 size 10 with 2 filters, assert correct rows + total + that only `page_size` rows are returned. Also a test pinning that out-of-scope `scholarship_in_scope` rows are excluded (guards against the sec-audit N61 dead-code class). Run. Expected PASS.
- [ ] **Step 4:** Commit: `perf(api): filter+paginate scholarships in SQL instead of in-memory`.

### Task 2.5: Fix the export N+1 (E19)

**Files:** Modify `backend/app/services/privacy/export_service.py:132-136`

- [ ] **Step 1:** Replace the per-session `SELECT InterviewResponse` loop with one `select(InterviewResponse).where(InterviewResponse.session_id.in_(session_ids))` grouped in Python, or add `selectinload(InterviewSession.responses)` to the parent query.
- [ ] **Step 2:** Test (real DB): user with 3 interview sessions × responses; assert the export contains all responses and (via SQLAlchemy echo/`assert_statement_count` helper) issues O(1) queries not O(N). Run. Expected PASS.
- [ ] **Step 3:** Commit: `perf(privacy): eliminate N+1 in data-export interview fetch`.

### Task 2.6: Celery worker hardening (E12)

**Files:** Modify `backend/app/tasks/celery_app.py:19-26`

- [ ] **Step 1:** Add to the Celery config: `task_soft_time_limit=600`, `task_time_limit=900`, `task_acks_late=True`, `task_reject_on_worker_lost=True`, `worker_prefetch_multiplier=1`. Stagger the two 02:00 beats (sec-audit N22): set one to `minute=30`.
- [ ] **Step 2:** Boot the worker (`celery -A app.tasks.celery_app worker --loglevel=info` dry) or run the existing trial/reminder task tests; confirm no config error.
- [ ] **Step 3:** Commit: `ops(celery): add task time limits, acks_late, prefetch=1, stagger beats`.

**Phase 2 gate:** concurrency tests prove non-blocking; suite green; manual smoke of `/scholarships` + `/recommendations`.

---

## Phase 3 — Observability & resilience

### Task 3.1: Central logging config + request-ID propagation (E10)

**Files:** Create `backend/app/core/logging_config.py`; modify `backend/app/main.py` (call it at startup; inject request-id into log records via `contextvars` + `logging.Filter`)

- [ ] **Step 1:** Create `configure_logging()` using `logging.config.dictConfig` with a JSON formatter (use `python-json-logger`, add to requirements), level from `settings.LOG_LEVEL` (default INFO; DEBUG only in dev).
- [ ] **Step 2:** Add a `ContextVar` set by the existing X-Request-ID middleware (`main.py:136`); a `logging.Filter` injects it into every record so logs carry `request_id`.
- [ ] **Step 3:** Call `configure_logging()` at app startup before middleware mount.
- [ ] **Step 4:** Test: capture logs in a request, assert the record JSON contains the same `request_id` as the response header. Run. Expected PASS.
- [ ] **Step 5:** Commit: `feat(obs): structured JSON logging with request-id propagation`.

### Task 3.2: Replace print() with logging (E11)

**Files:** Modify `curation/service.py:259,291`, `interview/evaluator.py:135`, `interview/voice_path.py:27`, `documents/chunker.py:26`, `tasks/graph_sync_tasks.py:26` (leave `app/ml/*` CLI prints)

- [ ] **Step 1:** In each, add `logger = logging.getLogger(__name__)` and replace `print(...)` with `logger.warning/exception(...)`. For the curation OpenSearch failures, use `logger.exception` (preserves traceback) AND `sentry_sdk.capture_exception` so the swallow is visible.
- [ ] **Step 2:** `grep -rn "print(" app/ | grep -v "app/ml/"` → expect 0 hits.
- [ ] **Step 3:** Commit: `fix(obs): replace print() with structured logging; capture swallowed OpenSearch errors`.

### Task 3.3: External-call resilience (E18, E28)

**Files:** Modify `backend/app/integrations/clerk/jwt_verify.py:41` (async httpx + retry), add timeouts/retry where missing

- [ ] **Step 1:** Convert the JWKS `httpx.get` to `httpx.AsyncClient().get` with the existing timeout, guarded by an `asyncio.Lock` around the module cache (also closes sec-audit N36). Add one retry on transport error.
- [ ] **Step 2:** Add `max_retries=2` to the Anthropic client construction (E1 file) and confirm Resend/Firecrawl/OpenSearch calls have explicit timeouts (audit says they do — verify, add where missing).
- [ ] **Step 3:** Test: JWKS fetch failure retries then raises cleanly; verify with a mocked transport. Run. Expected PASS.
- [ ] **Step 4:** Commit: `fix(resilience): async JWKS fetch with lock+retry; explicit LLM retry policy`.

**Phase 3 gate:** logs are JSON with request_id; zero non-CLI prints; suite green.

---

## Phase 4 — Architecture cleanup

### Task 4.1: Delete the fake v2 API (E13) — DECISION D-C

**Files:** Delete `backend/app/api/v2/__init__.py` + `app/api/v2/`; modify `backend/app/main.py` (remove v2 mount + Deprecation/Sunset headers on v1)

- [ ] **Step 1:** Grep for external/in-repo references to `/api/v2`: `grep -rn "api/v2\|v2/" app/ frontend/src tests/ docs/`. Confirm no real consumer.
- [ ] **Step 2:** Remove the v2 router include and the Deprecation/Sunset header logic in `main.py`. Delete `app/api/v2/`.
- [ ] **Step 3:** `python -c "from app.main import create_app; print(len(create_app().routes))"` → route count drops by the 6 duplicated mounts; suite green.
- [ ] **Step 4:** Commit: `chore(api): remove stub v2 router and misleading deprecation headers`.

### Task 4.2: Remove dead modules + heavy unused deps (E20, E21) — DECISION D-B

**Files:** Delete `app/ai_services/model_router.py`, `app/ml/{trainer,data_generator}.py` if proven unused; trim `requirements.txt`

- [ ] **Step 1:** Prove unused: `grep -rn "ai_services\|app.ml\|model_router\|data_generator\|trainer" app/ tests/ scripts/`. For each heavy dep, `grep -rn "import xgboost\|import shap\|import lime\|langchain\|import neo4j" app/`. Record what is genuinely unimported by runtime code.
- [ ] **Step 2:** Delete the proven-dead modules. Move genuinely-unused heavy deps to an optional extras group (or remove). If `langchain` is only used by `voice_path` (sec-audit N35, slated for gating), coordinate with that ticket — do not remove if voice path still imports it.
- [ ] **Step 3:** `python -c "from app.main import create_app; create_app()"` boots; suite green; Docker image rebuild smaller (record size delta).
- [ ] **Step 4:** Commit: `chore: remove dead ml/ai_services modules; trim unused heavy deps`.

### Task 4.3: Delete the dead second schema home (E15)

**Files:** Delete `backend/app/api/v1/schemas.py` (after proving 0 importers)

- [ ] **Step 1:** `grep -rn "from app.api.v1.schemas\|api.v1.schemas import" app/ tests/`. Expect 0 (audit says 0 routes import it). If any test imports it, migrate that import to `app/schemas/`.
- [ ] **Step 2:** Delete the file. Suite green; app boots.
- [ ] **Step 3:** Commit: `chore(schemas): remove dead app/api/v1/schemas.py (consolidate on app/schemas)`.

### Task 4.4: [SUB-PLAN REQUIRED] Split IngestionService god class (E7)

**Files:** `backend/app/services/ingestion/service.py` (2,729 lines, 107 methods)

- [ ] **Step 1:** This is too large to script blind. Write a dedicated sub-plan: `docs/superpowers/plans/2026-XX-ingestion-service-split.md`. Read the full file first. Proposed seams (confirm against code): `SourceCaptureClient` (capture/Firecrawl/conditional-GET), `CandidateParser` (JSON-LD/microdata/regex extraction), `DedupService` (fuzzy/snapshot drift), `IngestionRunManager` (run lifecycle/persistence). `IngestionService` becomes a thin orchestrator.
- [ ] **Step 2:** Constraint for the sub-plan: pure refactor, zero behavior change. The 50+ ingestion tests (many DB-mocked) must stay green; add real-DB tests for the run lifecycle BEFORE extracting (Phase 0 fixture enables this). Extract one collaborator per PR, suite green between each.
- [ ] **Step 3:** Do NOT start extraction until the sub-plan + characterization tests exist. Commit the sub-plan doc first.

### Task 4.5: [SUB-PLAN REQUIRED] Extract business logic from routes (E14)

**Files:** `routes/analytics.py:40` (16 inline aggregations), `curation.py`, `mentor.py`, `scholarships.py`, `clerk_webhook.py`, `waitlist.py`

- [ ] **Step 1:** Start with the worst offender: create `AnalyticsService.platform_overview(db)` holding the 16 aggregations; route becomes `return await AnalyticsService(db).platform_overview()`. Add a real-DB test asserting the counts.
- [ ] **Step 2:** Repeat per route module, one PR each, only moving DB access into the matching `services/<domain>/service.py`. No behavior change.
- [ ] **Step 3:** Each extraction: suite green + real-DB test for the moved logic. Commit per module: `refactor(<domain>): move DB access from route into service`.

---

## Phase 5 — API & dependency hygiene

### Task 5.1: Unify config single-source-of-truth (E16)

**Files:** Modify `backend/app/core/config.py` (add `OPENSEARCH_HOST/PORT/USER` + `GOOGLE_API_KEY`), `services/recommendations/hybrid_retriever.py:11-14`, `interview/voice_path.py:8`

- [ ] **Step 1:** Add the missing settings to `config.py` (no insecure defaults — `OPENSEARCH_PASSWORD` already validated in prod; align `OPENSEARCH_USER` etc.).
- [ ] **Step 2:** Replace every `os.getenv("OPENSEARCH_*")`/`os.getenv("GOOGLE_API_KEY")` in app code with `settings.*`. `grep -rn "os.getenv\|os.environ" app/` → only legitimate call-time reads (resend monkeypatch path) remain, with a comment.
- [ ] **Step 3:** Test: prod-settings validation still rejects default OpenSearch password; reading the retriever config returns the Settings value. Run. Expected PASS.
- [ ] **Step 4:** Commit: `fix(config): route OpenSearch + Google keys through Settings (single source of truth)`.

### Task 5.2: Idempotency on webhooks + creating POSTs (E17)

**Files:** Modify `backend/app/api/v1/routes/clerk_webhook.py`, `waitlist.py`

- [ ] **Step 1:** Clerk webhook: at handler top, `SETNX svix:processed:<svix-id> 1 EX 86400` in Redis; short-circuit duplicates with 200 (also closes sec-audit N5). Waitlist: dedupe on `(email, day)` unique key; uniform response.
- [ ] **Step 2:** Test (real DB + fake redis): replayed webhook event processed once; duplicate waitlist submit returns same response, one row. Run. Expected PASS.
- [ ] **Step 3:** Commit: `fix(api): idempotent Clerk webhook + waitlist (dedupe on event id / email-day)`.

### Task 5.3: Normalize pagination + route aliases (E24)

**Files:** Modify `routes/access_control.py:35`, `mentor.py:41`, `curation.py:141-153`, `api/v1/__init__.py:30-47`

- [ ] **Step 1:** Pick canonical `page`/`page_size` contract (matches `scholarships.py`). Convert `access_control` and `mentor` list endpoints to it; remove the deprecated `limit` override hack in `curation.py`.
- [ ] **Step 2:** Drop the duplicate alias mounts (`/profiles`, `/mentors`); keep singular OR plural canonical, add nothing else (frontend uses the canonical per CLAUDE.md — verify before removing).
- [ ] **Step 3:** Test: each list endpoint honors `page`/`page_size`; removed aliases 404. Run. Expected PASS.
- [ ] **Step 4:** Commit: `refactor(api): unify pagination contract; drop duplicate route aliases`.

### Task 5.4: Dependency automation + JWT lib consolidation (E22, E23)

**Files:** Create `.github/dependabot.yml`; (E23 coordinate with sec-audit N66)

- [ ] **Step 1:** Add `.github/dependabot.yml` with `pip` (backend) + `bun`/`npm` (frontend) + `github-actions` ecosystems, weekly.
- [ ] **Step 2:** E23/N66: migrate the local JWT path off `python-jose` to `pyjwt` (already a dep), then remove `python-jose` from `requirements.txt`. This touches `core/security.py` — gate behind the local-auth-deprecation decision; if local auth still active, do the pyjwt migration with a test asserting token encode/decode parity before removing jose.
- [ ] **Step 3:** Commit (two): `ci: add dependabot` and `chore(auth): migrate local JWT to pyjwt; drop python-jose`.

---

## Phase 6 — Test depth

### Task 6.1: Convert NoOp-DB integration tests to real-DB (E6 follow-through, E29)

**Files:** the ~13 `tests/integration/*` files injecting `_NoOpDB`/`FakeSession`

- [ ] **Step 1:** One file at a time, replace the fake `get_db` override with the Phase 0 `app_client`/`db_session` fixtures; seed via real inserts. Delete the now-unused fake classes (only those YOUR change orphaned).
- [ ] **Step 2:** Run each converted file against Postgres CI. Expected: PASS exercising real SQL. Track the fake-class count dropping from 42.
- [ ] **Step 3:** Commit per file: `test(<area>): use real DB session instead of hand-mocked fake`.

### Task 6.2: Add missing test types (E30)

**Files:** new `tests/db/test_migrations_roundtrip.py`, `tests/unit/test_cgpa_property.py`

- [ ] **Step 1:** Migration round-trip test: `alembic upgrade head` → `downgrade base` → `upgrade head` on the integration DB, assert no error.
- [ ] **Step 2:** Property test (Hypothesis, add to dev deps) for `utils/cgpa_converter.py`: for CGPA in valid ranges, US-GPA output stays in [0,4] and is monotonic. Run.
- [ ] **Step 3:** Commit: `test: add migration round-trip + cgpa property-based tests`.

### Task 6.3: Frontend smoke + contract gate (E30, sec-audit D7)

**Files:** `frontend` (Vitest setup); CI OpenAPI contract step

- [ ] **Step 1:** Add Vitest + Testing Library; one component test as the seed. (Full FE coverage is its own effort — this just establishes the harness + gate.)
- [ ] **Step 2:** Add CI step: `bunx openapi-typescript http://localhost:8000/openapi.json -o /tmp/types.generated.ts` then diff against committed `src/lib/api/types.ts`; fail if drift (closes the D1–D7 root cause).
- [ ] **Step 3:** Commit: `test(fe): add Vitest harness + OpenAPI contract drift gate`.

---

## Self-review (spec coverage E1–E30)

- E1→2.1, E2→2.2, E3→2.3, E4→2.4, E5→1.1/1.2, E6→0.3/0.4/6.1, E7→4.4(sub-plan), E8→0.1, E9→0.4/0.5/1.2, E10→3.1, E11→3.2, E12→2.6, E13→4.1, E14→4.5(sub-plan), E15→4.3, E16→5.1, E17→5.2, E18→3.3, E19→2.5, E20→4.2, E21→4.2, E22→5.4, E23→5.4, E24→5.3, E25→1.3, E26→1.3, E27→(folded into 4.4/4.5 shared-base extraction; standalone if not), E28→3.3, E29→6.1, E30→6.2/6.3.
- **Gap noted:** E27 (duplicated LLM-doc scaffold) has no dedicated task — it is best done opportunistically during 4.4/4.5 or as a small standalone `refactor(llm): extract shared LLMDocumentGenerator base`. Add as Task 4.6 if prioritized.

## Effort estimate (rough)

| Phase | Tasks | Est. |
|---|---|---|
| 0 Safety net | 5 | 1–2 days |
| 1 Data integrity | 3 | 1 day |
| 2 Concurrency/perf | 6 | 2–3 days |
| 3 Observability | 3 | 1 day |
| 4 Architecture | 5 (incl. 2 sub-plans) | 3–5 days (sub-plans extra) |
| 5 API/deps | 4 | 1–2 days |
| 6 Test depth | 3 | 2–3 days + ongoing |

Phases 0–2 (the high-value core) ≈ 1 week. Full program ≈ 3 weeks, matching team capacity (3 devs / parallelizable after Phase 0).
