# CLAUDE.md

<<<<<<< feat/phase-c-and-scraper-wip
Guidance for Claude Code in this repo.

## Repo
ScholarAI — AI scholarship platform. **Pakistan-pivot in progress (PRD `D:/Downloads/SCHOLARAI_PAKISTAN_PRD.md`)** targeting Pakistani students applying to UK / US / CA / DE / AU. Backend Features 1–10 complete (290 tests pass). Frontend Pass pending. Display brand: **GrantPath**. Repo / backend / internal docs: ScholarAI.

**Source of truth hierarchy:** PRD → `.codex/AGENTS.md` → `AGENTS.md` → `docs/scholarai/IMPLEMENTATION_STATUS_REPORT.md` → `docs/scholarai/01..14*.md` → this file. Legacy `docs/*.md` transitional.

## Stack
Next.js 16 + React 19 + TS + Tailwind 4 (frontend). FastAPI + SQLAlchemy 2 async + Alembic + Celery + Redis + pgvector on Postgres 16 (backend). Docker Compose. CI: `.github/workflows/ci.yml` (backend-sanity, kpi-regression, frontend-sanity, docs-governance, browser-smoke).

LLM = Anthropic Claude (`anthropic` SDK). Haiku 4.5 default; Sonnet 4.6 for SOP deep pass + Elite feedback. Prompt caching `cache_control: ephemeral` on static system prompts. Deterministic-template fallback when `ANTHROPIC_API_KEY` absent — CI + tests stay green offline.

## Commands
- Bootstrap: `cd backend && python scripts/bootstrap_local.py`
- API: `cd backend && python -m uvicorn app.main:app --reload`
- Tests: `pytest backend/tests/unit backend/tests/integration -q`
- Compile: `python -m compileall backend/app backend/tests`
- Migrations: `cd backend && alembic upgrade head`
- Pakistan seeds: `python backend/scripts/seed_pakistan_scholarships.py`, `seed_pakistan_universities.py`, `seed_visa_interview_questions.py`, `seed_legal_documents.py`, `demo_seed_pakistan.py` (orchestrator).
- Frontend (Bun): `cd frontend && bun dev` — port 3000. Also `bun run lint`, `bunx --bun tsc --noEmit`, `bun run build`.
- Stack: `docker compose up --build`.
- Docs gate: `python scripts/docs_governance_check.py`.
- Browser smoke: `python tests/e2e/playwright/run_smoke_suite.py` (selectors stale until Frontend Pass).

## Push gate (per AGENTS.md)
All must pass before push: backend unit+integration, KPI regression, frontend lint/typecheck/build, docs governance, browser smoke. Smoke relaxed on greenfield branch until S10 / Frontend Pass.

## Demo accounts
- student@example.com / strongpass1 (legacy seed)
- admin@example.com / strongpass1
- zara.khan@example.com / ScholarAI-Demo-2026! (Pakistan demo, plan=elite, after `demo_seed_pakistan.py`)

## Backend layout
- `main.py` — `create_app()`. `/api/v1` router. `ErrorEnvelope` + X-Request-ID middleware.
- `api/v1/__init__.py` — wires: health, auth, profile, scholarships, saved-opportunities, recommendations, documents, interviews, curation, mentor, analytics, access-control, **tracker**, **privacy**, **b2b**, **waitlist + upgrade**.
- `services/<domain>/` — `auth, students, recommendations, documents, interview, curation, ingestion, saved_opportunities, access_control, scholarships, tracker, visa_interview, privacy, llm`.
- `models/models.py` — single-file ORM. Enums `RecordState`, `IngestionRunStatus`, `DocumentProcessingStatus`, `InterviewSessionStatus`, `TrackerStage`, `UserPlan`.
- `core/` — `config.py`, `consent.py`, `plan_guard.py`, `authorization.py`, `dependencies.py`, `security.py`.
- `utils/cgpa_converter.py` — Pakistani CGPA→US GPA / UK class tiers.

## Test coverage (Pakistan PRD)
- 306 backend tests pass (`pytest tests/unit tests/integration`). Suites map 1:1 to PRD sections: §0.5 plan guard + waitlist/pricing, §0.6 privacy/B2B + trust-boundary AST guard, §1 profile Pakistan fields, §2 cgpa converter, §3 pakistan dataset, §4 recommendation_pakistan, §5 scholarship match service, §6 tracker service (incl. hec_attestation default), §7 SOP builder, §8 visa interview (70-question bank check), §10 demo seed pakistan (zara persona, plan=elite, 2099 expiry, 5 consents, ≥10 scholarships / ≥30 unis / ≥70 visa Q).
- `tests/unit/test_b2b_trust_boundary.py` AST-walks `app/services/recommendations` and `app/services/scholarships` and fails if they ever reference `Institution`/`InstitutionStudent`/`ReferralEnrollment`/`UniversityLead` or those table names — enforces PRD §0.6 trust boundary in CI.
- `tests/unit/test_demo_seed_pakistan.py` is a source-level pin on `scripts/demo_seed_pakistan.py`; it catches accidental demo regressions without needing a live DB.
- Frontend tests: none yet (no `*.test.*` under `frontend/src`). Coverage relies on Playwright smoke at `tests/e2e/playwright/`.

## Pakistan pivot status (backend complete)
**Migrations 0014–0018** add: User plan/billing/consent cols, StudentProfile Pakistan + B2B fields, target_countries[], universities table, application_tracker_items (6-stage Kanban + JSONB checklist incl. hec_attestation), visa_interview_questions, consent_audit_log, data_export_requests, data_deletion_requests, university_leads, legal_documents, waitlist, institution_students, referral_enrollments.

**New endpoints:**
- `POST /api/v1/scholarships/match` — Pakistan match w/ eligible/partial/stretch buckets, free-tier blur after 3.
- `GET/POST/PATCH/DELETE /api/v1/tracker` + `/tracker/{id}/stage` + `/tracker/{id}/checklist`. Free cap = 3 items.
- `POST /api/v1/documents/sop/draft` — Pakistan-context SOP via Claude. Free = 1 SOP. Elite = line-by-line feedback.
- `POST /api/v1/interviews/visa/start` + `/visa/{id}/answer` + `/visa/{id}/summary`. Free cuts at Q3. Elite gets transcript persisted as `DocumentRecord`.
- `POST/GET /api/v1/privacy/consent`, `GET /api/v1/legal/{slug}`, `POST/GET /api/v1/privacy/data-export`, `POST/DELETE /api/v1/privacy/account-deletion`.
- `POST /api/v1/b2b/share` — institution-tier only. Gated by `b2b_share_consent` AND `institutions.dpa_signed_at`.
- `POST /api/v1/waitlist`, `GET /api/v1/upgrade/pricing?currency=PKR|GBP|EUR|AED|USD`.

**Seeds:** 20 PK scholarships (Chevening / Fulbright / DAAD / Commonwealth / HEC Overseas + tier 2 + 10 GTA/GRA), 30 universities (10 UK + 8 US + 7 CA + 5 DE), 70 visa interview questions (20 UK + 20 US + 15 CA + 15 DE), 5 legal docs v1.0.

## Critical rules
- Validated structured data is authoritative for eligibility / deadlines / funding. RAG advisory only.
- Public `/scholarships` returns **published** only.
- Recommendation engine **MUST NOT** import from `university_leads` / `institutions` matching tables — keep B2B effects out of the matching graph (PRD §0.6 trust boundary). Verified.
- Sensitive PDPB categories (religion / politics / biometric) never collected — no schema columns.
- B2B share requires `b2b_share_consent=true` AND `institutions.dpa_signed_at IS NOT NULL`. Snapshot at share time (no retro-leak).
- Consent grants log IP + user-agent + sha256 of doc body. Latest grant wins. Version mismatch → HTTP 451.
- 30-day account deletion window. 7-year consent audit retention.
- Liability cap **PKR 1,000 or 6 months fees**, LCIA arbitration, class-action waiver (terms v1.0).
- Plan tiers: `free < pro < elite < institution`. Institution-tier hidden from student UI; backend filters in Frontend Pass.
- Do not import from `backend/legacy/`, `ai_services/`, `setup/`.
- Backend Pydantic schemas authoritative; `frontend/src/lib/api/types.ts` hand-synced.
- New feature = new service module inside FastAPI app, not a new deployable.
- Use pgvector for MVP; do not add a second search engine.
- Estimated Scholarship Fit Score — never frame as acceptance prediction.
- Visa university approval rates seeded as **estimates** (0.62–0.85). Provenance: educated estimates, not measured. Add disclaimer in UI badges.

## Frontend (status: S1–S9 greenfield, Pakistan Frontend Pass pending)
- Path alias `@/* → src/*`. shadcn over Radix. Lucide icons only. Sora / IBM Plex Sans / Mono via `next/font`.
- localStorage tokens: `grantpath.access_token` / `grantpath.refresh_token` / `grantpath.access_expires_at`.
- API base: `NEXT_PUBLIC_API_BASE_URL` (default `http://localhost:8000/api/v1`).
- RoleGuard ROLE_GROUPS: `student`, `mentor`, `admin`, `owner`.
- Hard UX constraints (PR-blocking): validated vs AI-generated visually distinct, no emoji-as-UI, no streaming theatre on REST, skeleton once per route, optimistic mutations w/ rollback toast, `/` focuses search, 44×44 tap targets, LCP <1.8s on `/feed`, INP <200ms, initial JS ≤180KB gzipped.

## Session rules (device-global, also in `~/.claude/CLAUDE.md`)
1. Update project `CLAUDE.md` after every completed task. Keep <200 lines.
2. Write `progress.md` before `/clear` or session end. Overwrite each time.
3. Trace requirements → code → e2e before declaring feature done. Evidence > assertion.

## Open work
- Frontend Pass: onboarding 4-step Pakistan → /scholarships/match → /tracker Kanban → SOP two-panel → visa interview UI → /upgrade pricing → UpgradeWall → Pakistan landing → consent UI + cookie banner + settings privacy → re-point smoke selectors.
- ~~Apply migrations 0014–0018 against live dev DB and run seed orchestrator before manual smoke.~~ **Done 2026-05-12**: alembic at head `20260511_0018`; `demo_seed_pakistan.py` ran (20 PK scholarships, 30 universities, 70 visa Q, 5 legal docs, demo `zara.khan@example.com`).
- Update `docs/scholarai/IMPLEMENTATION_STATUS_REPORT.md`, `frontend/README.md`, `.codex/AGENTS.md` to reflect Pakistan pivot.
- Run KPI regression + docs governance to clear push gate.

## Dev env notes (2026-05-12)
- OpenSearch 2.11 needs `DISABLE_SECURITY_PLUGIN=true` + `DISABLE_INSTALL_DEMO_CONFIG=true` (in `docker-compose.yml`) — default HTTPS-only blocks the HTTP healthcheck → backend never starts.
- Backend Dockerfile stage-2 install must use `--find-links=/wheels -r requirements.txt` with `--default-timeout=600 --retries 10`; `pip install /wheels/*` re-fetches transitive CUDA wheels and times out.
- Dev rate limits relaxed via `.env.example`: `AUTH_RATE_LIMIT_LOGIN_REQUESTS=50`, `REGISTER=30`, `REFRESH/LOGOUT=100`.
- `CORS_ORIGINS` covers `:3000` and `:3001`.
- Backend role values are lowercase StrEnum (`student`, `admin`, `owner` …). Frontend `Role` type + `RoleGuard.ROLE_GROUPS` must mirror — uppercase ENUM names cause blanket "Not available" guard.
- `StudentProfile` shape (backend canonical): `citizenship_country_code`, `gpa_value`, `gpa_scale`, `target_field` (single string), `target_degree_level`, `target_country_code`, `language_test_type`, `language_test_score`. `extra="forbid"` — no `full_name` / `field_tags[]` / `language_scores[]`. Frontend onboarding/profile map to this exactly.
- Curation route fix: `services.CurationService.list_records()` returns `(items, total)` tuple and takes `page`/`page_size`, **not** `limit`. Hot-patched in `app/api/v1/routes/curation.py:288`.
- Admin endpoints verified 200: `access-control/users`, `access-control/role-changes`, `recommendations/benchmarks`, `analytics`, `curation/records`, `curation/ingestion-runs`. Pakistan endpoints verified 200: `scholarships/match`, `tracker`, `upgrade/pricing`, `privacy/consent`, `privacy/legal/{slug}`.
- Frontend `/login` now has Student / Admin demo-fill buttons.
- Signup min password length is **12** (backend Pydantic requires it).
- Healthcheck architecture (2026-05-12): liveness/readiness split. `GET /livez` (process-only, no I/O) is the Docker HEALTHCHECK target; `GET /readyz` (DB ping) is the LB readiness gate; `GET /health` (DB + KPI alerts) is the ops dashboard endpoint. Image `HEALTHCHECK` directive removed from `backend/Dockerfile` — the backend image is process-agnostic (uvicorn / celery worker / celery beat share it), so healthchecks live in `docker-compose.yml` per service: backend → `/livez`, celery-worker → `celery inspect ping`, celery-beat → `grep beat /proc/1/cmdline`, neo4j → bash TCP probe on 7687 (replaces JVM cypher-shell which timed out at 5s).
- Scraper optimization pass (2026-05-13 → 14, branch `feat/phase-c-and-scraper-wip`): four PRs landed on top of pakistan-pivot.
  1. **Conditional GET** (commit `1bdde98`): IngestionService stores last `ETag` / `Last-Modified` per source; subsequent fetches send `If-None-Match` / `If-Modified-Since` and short-circuit on `304 Not Modified` (no parse, no LLM, no DB write). Cuts unchanged-source cost to a single HEAD-equivalent round-trip.
  2. **Sitemap + RSS/Atom feed discovery** (commit `457b047`, migration `20260514_0020_ingestion_caching.py`): new `source_feed` table (`source_id FK source_registry`, `kind ∈ {sitemap, rss, atom}`, `url`, `etag`, `last_modified`, `last_seen_at`). IngestionService now resolves a source's `robots.txt` → sitemap index → URLs, and parses RSS/Atom feeds before falling back to full-page scrape. Feed-driven runs only fetch URLs whose `<lastmod>` / `<updated>` is newer than the row's `last_seen_at`.
  3. **DiscoveryService** (commit `fbdf473`, `app/services/ingestion/discovery.py`): given a seed aggregator URL, crawl one level deep, keyword-filter outbound links (`scholarship`/`award`/`fellowship`/`grant`/`bursary`), classify each candidate via Claude as scholarship-source-likely, return high-confidence `DiscoveredSource` rows for admin review. No auto-registration — surfaces candidates only. Exported from `app/services/ingestion/__init__.py` (commit `5db76fb`).
  4. **Tests** (commit `779490f`): `test_ingestion_service` covers ETag short-circuit + feed parsing; `test_discovery_service` covers keyword filtering + monkeypatched LLM classifier + confidence thresholding; `test_b2b_trust_boundary` enforces PRD §0.6 ("recommendation engine MUST NOT import from `university_leads` / `institutions`"); `test_demo_seed_pakistan` covers the orchestrator (20 scholarships / 30 universities / 70 visa Qs / 5 legal docs). `test_privacy_and_b2b._profile` fixture extended with every new B2B snapshot field. All 14+ b2b/privacy + new ingestion tests pass.
- B2B data-capture Phase C done (2026-05-13): profile-edit page (`frontend/src/app/(student)/profile/page.tsx`) rewritten to 6 cards (Contact / Academic / Tests / Goal / Aspirations / Background) exposing all 25+ editable fields. University shortlist picker live-queries `/api/v1/universities?country=<first target>`. `target_countries` / `target_fields` / `target_degree_level` are chip multi-selects. `research_publication_count` auto-derives `has_research_publications`. `services/privacy/b2b_share.py::_profile_snapshot` extended to surface every new field — institutions snapshotted with `gmat_score`, `sat_score`, `budget_pkr_max`, `target_university_ids`, `current_university_id`, `household_income_band`, `current_employer`/`title`/`years_work_experience`, `linkedin_url`, `github_url`, `referral_source`, `phone_e164`/`whatsapp_e164`, `city_of_origin`, `intake_target`, `funding_requirement`, `degree_subject`, `hec_degree_level`. `bunx tsc --noEmit` profile-clean (only pre-existing `EligibilityMatrix.tsx` drift). DPA + `b2b_share_consent` enforcement unchanged; snapshot still taken once at share time (no retro-leak).
- `.gitignore`: `graphify-out/` (4.7M of AST cache from the graphify skill) now excluded.
=======
This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository

ScholarAI — modular monolith for AI-assisted scholarship discovery, eligibility-aware ranking, document feedback, and interview practice. FYP scope: 3 devs, 16 weeks, limited budget. Scope is **Canada-first MS-only (DS/AI/Analytics) plus Fulbright** — enforced in discovery and recommendation flow.

**Source-of-truth hierarchy:**
- Repo governance: `.codex/AGENTS.md` (mission + architecture defaults)
- Agent workflow: `AGENTS.md` (commands + push gate)
- Live implementation status: `docs/scholarai/IMPLEMENTATION_STATUS_REPORT.md`
- Canonical product/architecture docs: `docs/scholarai/01..14*.md`
- Acceptance gates: `docs/scholarai/v0_1_slc_acceptance_checklist.md`
- Legacy `docs/*.md` are transitional — do not treat as current.

## Common commands

### Backend (`backend/`, Python 3.12 recommended)
- Install: `python -m pip install -r backend/requirements.txt`
- Bootstrap DB + seed demo: `cd backend && python scripts/bootstrap_local.py` (Alembic upgrade head w/ retries; seeds demo if `AUTO_SEED_DEMO_DATA=true`)
- Run API: `cd backend && python -m uvicorn app.main:app --reload`
- Celery worker: `celery -A app.tasks.celery_app:celery_app worker -l info`
- Celery beat: `celery -A app.tasks.celery_app:celery_app beat -l info`
- Tests: `pytest backend/tests/unit backend/tests/integration -q`
- Single test: `pytest backend/tests/unit/path/to/test_file.py::test_name -q`
- Compile sanity: `python -m compileall backend/app backend/tests`
- Migrations: `alembic upgrade head` / `alembic revision --autogenerate -m "msg"` (run from `backend/`)
- API rehearsal: `cd backend && python scripts/rehearse_seeded_demo.py`

### Frontend (`frontend/`, Node 20)
- Install: `cd frontend && npm ci`
- Dev: `npm run dev` — http://localhost:3000
- Build: `npm run build`
- Start prod: `npm run start -- --hostname 0.0.0.0 --port 3000`
- Lint: `npm run lint`
- Typecheck: `npm run typecheck` (`tsc --noEmit`)

### Full stack
- `docker compose up --build` then UI at `http://localhost:3000`, API at `http://localhost:8000/health`, Swagger at `http://localhost:8000/docs`.
- After adding/renaming Next.js routes while dev server is running, restart it — stale process serves false 404s.

### Browser smoke (matches CI)
- Install browser once: `python -m playwright install chromium`
- Full suite: `python tests/e2e/playwright/run_smoke_suite.py`
- Demo rehearsal: `python tests/e2e/playwright/rehearse_seeded_demo.py`
- Direct entrypoints: `public_scholarship_browse_smoke.py`, `auth_dashboard_smoke.py`, `seeded_recommendations_smoke.py`, `document_feedback_smoke.py`, `interview_practice_smoke.py`, `curation_smoke.py`

### Docs governance
- `python scripts/docs_governance_check.py` (CI gate).

### Push gate (per `AGENTS.md`)
Before any push to GitHub, run all of: backend unit/integration, KPI regression, frontend lint/typecheck/build, docs governance, browser smoke. Push only after all pass.

### Demo accounts (seeded locally)
- student: `student@example.com` / `strongpass1`
- admin: `admin@example.com` / `strongpass1`

## Architecture

### Stack
- **Frontend:** Next.js 16 + React 19 + TypeScript + Tailwind 4. Standalone output. Path alias `@/* → src/*`.
- **Backend:** FastAPI modular monolith (`backend/app/`), SQLAlchemy 2 async, Pydantic v2, Alembic, Celery + Redis, pgvector on PostgreSQL 16. Neo4j is provisioned but the Knowledge-Graph Layer is currently a *logical* relational abstraction (per `docs/scholarai/05_system_architecture.md`).
- **Search:** pgvector embeddings on `ScholarshipChunk`; default embedding model `sentence-transformers/all-MiniLM-L6-v2`.
- **Async:** Celery worker + beat. Beat schedule (`backend/app/tasks/celery_app.py`):
  - `nightly-scholarship-ingestion` @ 02:00 UTC
  - `kpi-snapshot-retention-cleanup` (when `KPI_SNAPSHOT_RETENTION_ENABLED=true`)
  - Task includes: `recommendation_tasks`, `scraper_tasks`, `kpi_tasks`.
- **Deploy:** Docker Compose. CI: `.github/workflows/ci.yml` with `backend-sanity`, `kpi-regression`, `frontend-sanity`, `docs-governance`, `browser-smoke` jobs.

### Backend layout (`backend/app/`)
- `main.py` — `create_app()` factory. Mounts `api_v1_router` at `/api/v1`. Lifespan calls `seed_demo_data_if_enabled()`. Global handlers map `ScholarAIException`, validation, SQLAlchemy, and unhandled errors to a uniform `ErrorEnvelope` (`code`, `message`, `request_id`, `status`). X-Request-ID middleware wraps every request.
- `api/v1/__init__.py` — wires the active router set:
  `health`, `auth`, `profile` (+ `profiles` alias), `scholarships`, `saved-opportunities`, `recommendations`, `documents`, `interviews`, `curation`, `mentor` (+ `mentors` alias), `analytics`, `access-control`. `app/api/v2/` exists but is empty — do not assume v2 contracts.
- `services/<domain>/` — one folder per domain (`auth`, `students`, `recommendations`, `documents`, `interview`, `curation`, `ingestion`, `saved_opportunities`, `access_control`). Pattern in `recommendations/`: `service.py` orchestration + helpers `hybrid_retriever.py`, `eligibility.py`, `evaluation.py`, `benchmark_registry.py`. **No formal repository pattern** — services use `AsyncSession` injected via DI from `app/core/dependencies.py` and return Pydantic schemas, never raw ORM models.
- `models/models.py` — single-file ORM. Enums encode the curation state machine: `RecordState ∈ {raw, validated, published, archived}`, `IngestionRunStatus`, `DocumentProcessingStatus`, `InterviewSessionStatus`. `Scholarship` carries provenance (`record_state`, `imported_at`, `provenance_payload`, `source_last_seen_at`, validate/publish/reject audit columns).
- `core/config.py` — Pydantic `Settings` (env-driven). `validate_production_settings()` rejects default `SECRET_KEY`/`NEO4J_PASSWORD`/`DATABASE_URL` when `ENVIRONMENT=production`.
- `tasks/` — Celery app + `recommendation_tasks`, `scraper_tasks`, `kpi_tasks`, `graph_sync_tasks`.
- `backend/legacy/` — quarantined; do not import. `ai_services/` and `setup/` flagged for archive.

### Frontend layout (`frontend/src/`)
- `app/<route>/` — App Router pages: `scholarships` (public), `recommendations`, `dashboard`, `document-feedback`, `interview`, `curation`, `mentor`, `admin`, `owner`, `onboarding`, `profile`, `login`, `signup`. Root `layout.tsx` wraps in `AuthProvider`.
- `lib/api.ts` — single fetch wrapper with Bearer-token injection, `cache: "no-store"`, normalized error parsing. Base URL from `NEXT_PUBLIC_API_BASE_URL` (default `http://localhost:8000/api/v1`).
- `components/auth/auth-provider.tsx` — Context auth. Tokens in `localStorage` (`scholarai.access_token`, `scholarai.refresh_token`, `scholarai.access_token_expires_at`); refresh fires 60s before expiry; cross-tab sync via `storage` event; 401 triggers refresh-and-retry.
- `lib/routes.ts` — role priority routing (student → `/dashboard`, admin → `/curation`, owner → `/owner`, mentor → `/mentor`).
- `lib/types.ts` — frontend type contracts. **No** generated SDK; backend Pydantic schemas are authoritative — types kept in sync by hand (`shared/contracts/README.md`).

### Module boundaries
| Module | Routes | Owns | Must not own |
|--------|--------|------|--------------|
| `auth` | `/auth/*` | JWT tokens, role checks, session lifecycle | Scholarship data |
| `students` | `/profile` | Profile CRUD | Recommendations |
| `scholarships` | `/scholarships/*` | Discovery, detail, publication workflow | Document feedback |
| `recommendations` | `/recommendations` | Eligibility → retrieval → rerank → explanation | Curation writes |
| `documents` | `/documents/*` | Upload lifecycle, grounded feedback | Scholarship truth |
| `interviews` | `/interviews/*` | Practice sessions, rubric outputs | Student scoring logic |
| `curation` | `/curation/*` | raw → validated → published, ingestion review | Recommendation ranking |
| `access_control` | `/access-control/*` | Owner role mgmt + audited reverts | Domain data |

### Recommendation pipeline
Stages from `docs/scholarai/08_recommendation_and_ml.md`:
0. Scope filter (published, MS, DS/AI/Analytics, Canada+Fulbright)
1. KG eligibility filter (citizenship/GPA/language/field/degree)
2. pgvector similarity rerank
3. ML rerank — **Estimated Scholarship Fit Score**, not acceptance prediction
4. Explanation generation

**Current runtime: Phase 1 active.** Stages 0–2 wired (relational eligibility graph + pgvector retrieval). Stage 3 uses calibrated heuristic rerank with guardrail floor/cap + policy version, plus rules-only fallback parity. Benchmark dataset registry + `GET /api/v1/recommendations/benchmarks` and `POST /api/v1/recommendations/benchmarks/{dataset_id}/evaluate`. KPI snapshot recording + MRR@K instrumentation live. **Never present scores as causal/acceptance probabilities.**

### Curation state machine
`Source registry → fetch → parse → schema validate → normalize → dedupe → review queue → curator decision → published`. States `raw → validated → published` enforced in DB and curation routes. Public `/scholarships` returns **published only**. Dedup keys: `source_record_hash`, `source_url`, `(normalized title, provider, deadline)`.

### RBAC
Six-role bundle: `ENDUSER_STUDENT`, `INTERNAL_USER`, `DEV`, `ADMIN`, `UNIVERSITY`, `OWNER`. Capability-based authorization matrix; institution-scoped university access; compatibility-window migration from legacy role claims to capability claims. Owner governance via `/api/v1/access-control/*` (managed-user listing, role updates, audited role reverts).

## Backend conventions

### Service layer
```python
class <Domain>Service:
    def __init__(self, db: AsyncSession): self.db = db
    async def method(self, payload: SchemaIn) -> SchemaOut: ...
```
- Always `await` SQLAlchemy calls; never mix sync + async.
- Domain errors raise `ScholarAIException` with `ErrorCode` enum + status code (no generic `Exception`).
- Services return Pydantic schemas, never ORM models.

### API routes
- One `APIRouter` per domain in `backend/app/api/v1/routes/<domain>.py`.
- Dependencies injected via `Depends()`.
- List endpoints normalize to `{ items: [...], total: int }`.
- Errors flow through the global `ErrorEnvelope` handler.

### Schemas
- Request/response in `backend/app/schemas/`.
- Pydantic `BaseModel` with `Field(..., description=...)` for OpenAPI.
- Domain enums in `backend/app/models/models.py`.

## Phase 2 API surface (Canada-first fixed)
- `POST /api/v1/documents` — accepts optional scholarship grounding identifiers.
- `POST /api/v1/documents/{id}/feedback` — returns explicit grounded-context partitions: validated scholarship facts, retrieved writing guidance, generated guidance, limitations.
- `POST /api/v1/interviews` — accepts `practice_mode` + optional `scholarship_id`.
- `GET /api/v1/interviews/{id}` — returns session history + rubric trend summary used by adaptive follow-up.
- Invalid grounding identifiers fail cleanly with structured errors.

## Implementation status (live — see `IMPLEMENTATION_STATUS_REPORT.md` for evidence links)

### Test health snapshot (verified 2026-05-10 on `main@5549d52`)
- `pytest backend/tests/unit` — **118 passed**, 0 failed (29.3s)
- `pytest backend/tests/integration` — **50 passed**, 0 failed (5.3s)
- `python -m compileall backend/app backend/tests` — clean
- `python scripts/docs_governance_check.py` — 0 terminology / link / canonical-tail failures
- Rerun: `pytest backend/tests/unit backend/tests/integration -q && python scripts/docs_governance_check.py`

### Done
- FastAPI modular monolith + Alembic migration-driven bootstrap + seeded demo dataset + rehearsal scripts.
- CI sanity + KPI regression + browser-smoke gates.
- Auth: register/login/me/refresh; access-token + refresh; frontend session persistence; protected/admin/owner route guards.
- Public scholarship browse/search/filters/detail; profile save+load; functional onboarding.
- Recommendation API + stage-aware explanation; pgvector retrieval; calibrated heuristic rerank; rules-only fallback parity; benchmark registry + evaluate endpoints; KPI snapshots; MRR@K.
- Saved opportunities + tracker status transitions (saved/in-progress/applied/closed) on dashboard.
- Document submission + scholarship-grounded bounded feedback with explicit grounded-context partitions.
- Interview mode-aware sessions, adaptive weakest-dimension follow-up, structured rubric, history/trend summary, deterministic action-plan items.
- Curation: raw/validated/published handling; review/edit/approve/reject/publish/unpublish; audit-log foundation.
- Ingestion: source-registry runs, capture path, parsing, raw-record creation, retry API/UI, diagnostics filtering, queue assignment, bulk retry, captured HTML snapshot management.
- Role homes (student/admin/owner/mentor/test-user) all complete in v0.1 acceptance checklist.
- Acceptance: SLC-CORE-004/005, SLC-ROLE-001..005, SLC-OPS-003, SLC-TRUST-001..003, SLC-UI-001..003 marked Complete.

### Remaining
- Recommendation: continuous online drift monitoring; ongoing calibration ops + alerting loops.
- Grounding depth: expand bounded guidance library; raise citation density across broader scholarship coverage.
- Long-horizon coaching: richer multi-session interview plans; voice path; AI-generated longitudinal intervention automation.
- Ingestion coverage: parser coverage still heuristic and narrow; deeper parser resilience; broader provider expansion (DAAD deferred).
- API contracts: detail responses, pagination metadata, route naming still diverge from `10_backend_api_and_repo.md` (e.g. `profile` vs docs label `profiles`).
- Async orchestration for larger document-feedback jobs.
- DevOps: release management, rollback drills, production-like hardening.
- Open SLC IDs without execution evidence yet: SLC-CORE-001/002/003, SLC-OPS-001/002.
- `shared/` and `infra/` remain documentation scaffolding only.
- Deferred: broad geography, marketplace/mentor commerce, partner APIs, institution analytics, tenant partitioning, graph experimentation, ML reranking ablations, larger judged-set evaluation tooling.

### Known low-priority issues (from 2026-05-10 audit)
- `backend/tests/unit/test_document_service.py:286` — `test_retrieve_bounded_guidance_expands_degree_and_field_dimensions` carries `@pytest.mark.asyncio` but is sync; pytest-asyncio warns and skips the async path. Drop the decorator or make the test `async def`.
- Local `.venv` drifts from `backend/requirements.txt` pins (Python 3.14 + fastapi 0.135 + sqlalchemy 2.0.48 vs pinned Python 3.12 + fastapi 0.115 + sqlalchemy 2.0.35). CI uses Python 3.12; local devs should rebuild with `py -3.12 -m venv .venv312 && .venv312\Scripts\python -m pip install -r backend/requirements.txt`.

### Next 3 priorities (per status report)
1. Expand grounding depth + citation density across broader scholarship coverage.
2. Expand recommendation benchmark dataset coverage; calibrate rerank weights with judged samples.
3. Strengthen ingestion coverage (richer parsers + captured HTML snapshot management).

## Critical rules
- Structured validated data is authoritative for eligibility, deadlines, funding rules. RAG is advisory; never the authority for scholarship rules.
- Public `/scholarships` returns **published only**.
- Eligibility = relational queries through the Knowledge-Graph Layer, not AI guesses.
- Do not import from `backend/legacy/`, `ai_services/`, `setup/`.
- Backend Pydantic schemas are the authoritative API contract; `frontend/src/lib/types.ts` is hand-synced.
- New feature = new service module inside the FastAPI app, not a new deployable.
- Use pgvector for MVP; do not introduce a separate search engine without justification.
- When updating runtime behavior, update `docs/scholarai/IMPLEMENTATION_STATUS_REPORT.md` in the same PR.
>>>>>>> main
