# CLAUDE.md

Guidance for Claude Code in this repo.

## Repo
ScholarAI — AI scholarship platform. **Pakistan-pivot in progress (PRD `D:/Downloads/SCHOLARAI_PAKISTAN_PRD.md`)** targeting Pakistani students applying to UK / US / CA / DE / AU. Backend Features 1–10 complete (290 tests pass). Frontend Pass pending. Display brand: **AidwiseAI**. Repo / backend / internal docs: ScholarAI.

**Source of truth hierarchy:** PRD → `.codex/AGENTS.md` → `AGENTS.md` → `docs/scholarai/IMPLEMENTATION_STATUS_REPORT.md` → `docs/scholarai/01..14*.md` → this file. Legacy `docs/*.md` transitional.

## Stack
Next.js 16 + React 19 + TS + Tailwind 4 (frontend). FastAPI + SQLAlchemy 2 async + Alembic + Celery + Redis + pgvector on Postgres 16 (backend). Docker Compose. CI: `.github/workflows/ci.yml` (backend-sanity, kpi-regression, frontend-sanity, docs-governance, browser-smoke). CI `frontend-sanity` + `browser-smoke` run on Bun (`oven-sh/setup-bun@v2`, `bun install --frozen-lockfile`); the project has no `package-lock.json`.

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

**CI temp flag (PR #84):** the `browser-smoke` step in `.github/workflows/ci.yml` carries `continue-on-error: true` because the greenfield rebuild left smoke `data-testid` selectors stale. The step still runs and logs, but a green `browser-smoke` job does NOT mean smoke passed — check the step log. **This flag must be removed during S10 / Frontend Pass, once smoke selectors are re-pointed to the rebuilt UI.**

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

## Front-upgrade planning docs
- **Front-upgrade.md v4** (2026-05-17, 2646 lines, 11 sec / 36 screens). Premium Cultural: ivory `#FBF7EE` + ink-deep `#0E1A1F` + lapis `#1B3A6B` + gold-leaf `#B08A3E` + sindoor `#B94A48`. Fraunces italic display + Inter body + JBM data. Every screen has states + contract + anti-slop bans + copy + a11y + telemetry. Banned-phrase grep §7.5. Prior v3 at `Front-upgrade.legacy.md`.
- **S88 rebuild 2026-05-17** — foundations + 9 routes + cookie banner + visual audit. See `frontend/CLAUDE.md` S88. Lint + tsc + build clean. 21/24 audit routes 200. Audit runner at `frontend/scripts/visual-audit.mjs`.
- **Brand rename 2026-05-15**: GrantPath → AidwiseAI. `grantpath.*` localStorage keys kept (renaming logs users out).
- **Security audit 2026-05-18** — see `SECURITY_AUDIT.md`. P0+P1 closed; S6/S9/S16/S17/S18/S19 deferred.

## Open work
- Smoke selector re-point + `ci.yml:198` `continue-on-error` removal (needs 3 green local runs).
- Settings privacy panel polish (backend routes shipped).
- Refresh `docs/scholarai/IMPLEMENTATION_STATUS_REPORT.md`, `frontend/README.md`, `.codex/AGENTS.md` for Pakistan pivot.

## Q1 retier (2026-05-16, branch `feat/pakistan-frontend-pass`, merged)
21 commits `23942f5..d20ab14`; **444 backend pass + 1 xpass**. Alembic head `20260516_0025`. Adds: `sop_monthly_usage` (_0024), `usage_ledger` (_0025), `scholarships.tier` (_0023). `core/burn_cap.py` 60% per-tier monthly + 429 + ledger writers. `tests/unit/test_user_facing_vocab.py` blocks classification tokens. Pricing PKR 2,999/6,000; free/pro/elite caps 3/6/12; SOP quotas 1/5/10. Premium paywall on `/scholarships` (402 via `_guard_premium_tier`). WhatsApp-only Elite alerts (SMS removed). `AnthropicClient.complete_with_accounting` pre-flights burn cap — sop_builder + visa evaluator + professor_email + strategy_report migrated. FE: neutral `MatchResponse` + `CompatibilityMeter`.

## Air University exhibition trial (2026-05-16, branch `feat/pakistan-frontend-pass`, merged)
Backend for May-19 booth — Pro via invite `AIRU2026`, 100 redemptions, 30d/user. **454 pass + 1 xpass**. Migration `_0026`: `invite_codes` + 4 user cols (`air_uni_*`, `redeemed_invite_code` indexed). `AuthService._redeem_invite_code` row-locked (400 on unknown/inactive/expired/exhausted). `tasks/trial_tasks.py:expire_trial_plans` Celery beat 02:00 UTC, idempotent UPDATE. Mailgun fail-soft to log-only when keys absent. Dockerfile bakes Chromium for scraper (≈1.2GB). CLI: `seed_invite_codes.py`, `grant_invite_uses.py`, `generate_qr_flyers.py`. New deps: `anthropic==0.39.0`, `qrcode[pil]==7.4.2`, `sentry-sdk[fastapi]==2.18.0`. Tests: 4 trial tasks + 6 invite-redemption cases.

## S87 Pakistan Frontend Pass (2026-05-15, `feat/pakistan-frontend-pass`)
**369 backend pass** (312 unit + 57 integration); FE green; docs gov 0 fails; KPI regression 17 pass. BE: `/auth/me` exposes plan/currency/country; professor_email + strategy_report (Elite 402, mig `_0022`); notifications log-only fan-out; alert/reminder Celery tasks; new routes `POST /documents/professor-email` + `POST /reports/strategy`; 28 new tests. FE: `isPlanRequiredError` + 6 new endpoint modules; `UpgradeWall` 402 verbatim; `app/upgrade` 4 tiers + 5-currency + waitlist; `(student)/{tracker,documents/sop,documents/professor-email,interviews/visa}`; PK landing; `(partners)/*` + PARTNER_ROLES in `RoleGuard`; sidebar adds Tracker + Visa-practice. `User` extended w/ plan/currency/country. Trust boundary: student excludes university; partner excludes every student role.

## Dev env notes (2026-05-12, updated 2026-05-24)
- **Dockerfile base: `mcr.microsoft.com/playwright/python:v1.52.0-noble`** (Ubuntu 24.04, Python 3.12.3). Resolves `enum.StrEnum` + `datetime.UTC` (Python 3.11+ features). `build-essential` required in apt — noble does not pre-include gcc unlike jammy.
- **`shap==0.46.0`** (0.44.0 yanked from PyPI; 0.46.0 has cp312 binary wheel). **`pydantic-settings==2.7.0`** (2.5.0 had `issubclass()` bug). `requirements-dev.txt` splits out pytest deps; `.dockerignore` excludes tests/docs from build context.
- OpenSearch 2.11 needs `DISABLE_SECURITY_PLUGIN=true` + `DISABLE_INSTALL_DEMO_CONFIG=true` or backend never starts.
- Dev rate limits relaxed in `.env.example`: LOGIN=50, REGISTER=30, REFRESH/LOGOUT=100.
- `CORS_ORIGINS` covers `:3000` + `:3001`. Backend roles lowercase StrEnum; FE `Role` + `RoleGuard.ROLE_GROUPS` must mirror.
- `StudentProfile` (S89.1 sync'd) — 28 fields incl. PK pivot + research + financial. `extra="forbid"`.
- Curation route fix: `CurationService.list_records()` returns `(items, total)` w/ `page`/`page_size` (not `limit`). Patched `curation.py:288`.
- Verified 200 admin: `access-control/users`, `role-changes`, `recommendations/benchmarks`, `analytics`, `curation/*`. Verified 200 PK: `scholarships/match`, `tracker`, `upgrade/pricing`, `privacy/consent`, `privacy/legal/{slug}`.
- Signup min password 12 (backend Pydantic). Login no min (S10).
- Healthcheck split (2026-05-12): `/livez` process-only (Docker HEALTHCHECK), `/readyz` DB-ping (LB gate), `/health` DB+version (S20 stripped KPI). Image HEALTHCHECK removed; healthchecks per-service in `docker-compose.yml`.
- Scraper opt (2026-05-13→14, `feat/phase-c-and-scraper-wip`, 4 PRs): conditional GET (`1bdde98`), sitemap+RSS+`source_feed` table (`457b047`, mig `_0020`), `DiscoveryService` Claude classification (`fbdf473`), tests (`779490f`).
- B2B Phase C (2026-05-13): `/profile` 6-card 25-field editor; `b2b_share.py::_profile_snapshot` snapshots every new field at share time.
- `.gitignore` excludes `graphify-out/` (4.7M AST cache).
- **S86 Scraper Ingestion** (2026-05-15, mig `_0021`): destination geo (PK default + GB/US/DE/AU/CA), JSON-LD + microdata extraction, fuzzy-dedup (`SequenceMatcher≥0.9`), snapshot drift sha256, multi-pagination (rel=next + Load-More + numbered), parser-diagnostic + `GET /scholarships/{id}/provenance`, source-health table (healthy/degraded/down at 0-2/3-5/≥6 failures). Tests 369 pass.

## Recent history (2026-05-17 → 2026-05-18)
- **PR #87** (Q1 retier + invite) merged green. Alembic head `20260516_0026`. Key fixes: FE import cluster, `InviteCode` re-export, `MatchResponse` schema, Vercel build clear.
- **S20 Security**: SecurityHeadersMiddleware (HSTS/CSP/COOP/CORP), TrustedHostMiddleware, prod CORS rejects localhost, ProxyHeadersMiddleware, `core/account_lockout.py` (5fail/15min Redis sliding window), Mailgun `_sanitize_header()`, pip-audit in CI, `/health` DB+version only. **Deferred**: S6 TLS, S9 refresh rotation, S16 httpOnly, S17 TOTP, S18 Argon2id, S19 RS256 (`SECURITY_AUDIT.md`).
- **S89 + S89.1 + S89.2** Premium Cultural FE pass: audit harness (`frontend/scripts/audit/`), 6 routes (`/not-found`, `/error`, `/offline`, `/denied`, `/maintenance`, `/legal/[slug]`), `/saved` Kanban→list+Promote-to-tracker, 6-card `/profile`, 6-tab `/settings` w/ TypedConfirm deletion, `RotatingDegree` h1 cycler, `useGeoCurrency` (ipwho.is, 24h cache, PKR fallback). 11 testids backfilled. `StudentProfile` FE type 10→28 fields. `lib/api/endpoints/legal.ts` shipped. **Deferred**: smoke re-point + `ci.yml:198` `continue-on-error` removal (needs 3 green local runs).

## Backend audit 2026-05-23 (live, branch `feat/s89-premium-cultural`)
**State:** 8/8 containers healthy. Alembic head `20260521_0027` single + current. **396 unit pass + 1 xfailed + 1 warning** (54.67s host). 22/22 endpoint smoke pass (student + admin tokens). **96 routes** in openapi (v1 + v2 mirror).
- **Crash root cause + recovery**: backend crash-loop traced to `pydantic-settings==2.5.0` (image) vs `==2.7.0` (requirements.txt). `langchain-community` downgraded transitive; 2.5.0 had `issubclass(list[str], RootModel)` bug → `Settings()` init `TypeError`. Image rebuilt to `pydantic-settings==2.7.0` + new base `mcr.microsoft.com/playwright/python:v1.52.0-noble` (Py 3.12.3). Backend back up; match endpoint 200 end-to-end.
- **Sub-agent false positives caught**: `/health` "duplicate" (different paths, `/health` vs `/api/v1/health`), alembic "circular" (linear `0008→0011→0009→0010`), `mentors.ts` "wrong path" (backend has `/mentors` alias `api/v1/__init__.py:45`), beat task names "wrong" (decorator explicit `name="tasks.X"`), `scholarships.py:52` bare except (documented `# noqa: BLE001`). Verification-before-edit blocked 5 needless changes.
- **Fixed this session**: `broker_connection_retry_on_startup=True` in `backend/app/tasks/celery_app.py:19` (closes Celery 5.1 deprecation warning).
- **Real open items**:
  - 🟡 `app/api/v1/schemas.py` — 7 dead duplicate Pydantic classes vs `app/schemas/*` (UserCreate, UserLogin, UserResponse, TokenResponse, StudentProfileResponse, ScholarshipListItem, InterviewAnswerRequest). Routes import from `app/schemas/*`; safe to delete.
  - 🟡 `app/ai_services/model_router.py` — dead, never imported. CLAUDE.md bans `ai_services/`. Safe to delete.
  - 🟡 `requirements.txt` transitive drift: `langchain-community` resolves pydantic-settings older. Add to constraints or `pip install --upgrade --upgrade-strategy=eager pydantic-settings` in Dockerfile. Long-term: `pip-compile` lockfile.
  - 🟢 `test_document_service.py:286` — `@pytest.mark.asyncio` on sync function. 1-line removal.
  - 🟢 OpenSearch memory 1.64GB/2GB (82%) — watch; bump compose limit if persistent.
- **Carried over from prior gap audit**:
  - CI flag `ci.yml:198` `continue-on-error: true` removal (needs 3 green local smoke runs).
  - `docs/scholarai/IMPLEMENTATION_STATUS_REPORT.md` refresh to `_0027`.
  - Prod `AIRU2026` invite seed before booth.
  - `tests/integration/test_trial_lifecycle.py` end-to-end add.
  - `tasks.run_usage_ledger_prune` Celery beat monthly (13-month retention).

## S90 + S90.1 + S91 Frontend audit remediation (2026-05-24/25, branch `s90/audit-remediation`, **PR #100 open**)
19 commits. Audit matrix **0 FAIL / 7 WARN / 349 PASS of 356 cells** (baseline 188/96/48). Token contrast darken (`ink-subtle 6E7984→5C6772`, `gold-leaf B08A3E→6E521B`, validated/caution/sindoor too) + 7 `?? []` guards + `ConsentBar` auth-gated + backend `GET /api/v1/geo/currency` proxy (kills CSP ipwho.is block) + 3 banned `unlock` strings replaced + Sparkles 9→4 + `StickySubNav` for <md + a11y fixes + harness `chromium.launch({channel: "chrome"})` + per-route mock stubs. Harness: `cd frontend && node scripts/audit/runner.mjs` (~25min full).

## S92 backend CVE bumps (2026-05-25, branch `s92/cve-bumps`, in flight)
CI `pip-audit --strict` step in PR #100 flagged 29 CVEs in 13 transitive deps. S92 ships 6 safe bumps (others deferred):
- requirements.txt: `python-dotenv 1.0.1→1.2.2`, `python-jose 3.3.0→3.4.0`, `python-multipart 0.0.9→0.0.27`, `lxml 5.3.0→6.1.0`, `orjson 3.10.7→3.11.5`.
- requirements-dev.txt (split file): `pytest 8.3.0→9.0.3`, `pytest-asyncio 0.24.0→1.3.0`.
- Deferred S93: langchain stack (6 CVEs — LLM regression risk), transformers (2 CVEs — ML inference regression risk), starlette (capped by fastapi 0.115.0 — needs fastapi co-bump).

## Staggered ingestion + beat health + admin status (2026-05-26, branch `scraper/stealth-cleanup`)
Closed the 3 ops gaps in the nightly ingestion pipeline. No alembic migration; uses existing `SourceRegistry` columns.
- **Staggered fan-out.** Single 02:00 UTC beat keeps firing `tasks.run_nightly_ingestion`; the task now queries `SourceRegistry` where `is_active=True AND source_key != "nightly_sync_main"` and dispatches one `run_source_ingestion.apply_async` per source with `countdown = index * INGESTION_STAGGER_SECONDS` (default 300s). Legacy `nightly_sync_main` path preserved as fallback when zero active sources exist. `_should_run_nightly` guard still wraps the whole path.
- **Beat health check.** New beat `tasks.run_ingestion_health_check` runs every `INGESTION_HEALTH_CHECK_INTERVAL_MINUTES` (default 30). Reads `_load_last_nightly_completion`; if stale > `INGESTION_STALE_HOURS` (default 26) → `logger.error("ingestion.health.stale", ...)` + `sentry_sdk.capture_message` (guarded by `SENTRY_DSN`) + `send_email(ADMIN_ALERT_EMAIL, ...)` (fail-soft if either unset). Reuses existing Mailgun fallback in `notifications/channels.py:66`.
- **Admin rollup endpoint + banner.** New `GET /api/v1/curation/ingestion-runs/nightly-status` (declared BEFORE `/{run_id}` to avoid UUID-parse collision) returns `NightlyStatusResponse` (last_completed_at + last_status + last_run_id + hours_since + is_stale + stale_threshold_hours + next_expected_at + stagger_seconds + active_source_count + sources[SourceHealthSummary]). Frontend `<NightlyStatusBanner>` mounted at top of `/admin/ingestion`; 30s refetch via react-query; shows status pill (Healthy/Stale), next-run ETA, per-source health grid.
- **Settings added (config.py):** `INGESTION_STAGGER_SECONDS=300`, `INGESTION_STALE_HOURS=26`, `INGESTION_HEALTH_CHECK_INTERVAL_MINUTES=30`, `ADMIN_ALERT_EMAIL=None`. All fail-soft when unset.
- **Tests:** +4 unit (`test_run_nightly_dispatches_one_task_per_active_source`, `test_run_nightly_falls_back_to_legacy_when_no_active_sources`, `test_ingestion_health_check_alerts_when_stale`, `test_ingestion_health_check_quiet_when_fresh`). Full suite: 400 pass + 1 xfailed (was 396 + 1).
- **Verify:** `python -m compileall backend/app` clean. `bunx --bun tsc --noEmit` clean. Docker rebuild needed for `celery-beat` + `celery-worker` containers to pick up new beat entry.

## Scraper stealth + cleanup (2026-05-25, branch `scraper/stealth-cleanup`)
Evaluated CloakBrowser swap; declined — scholarship portals (Chevening/Fulbright/DAAD/HEC) are not bot-hostile, CloakBrowser 200MB no-redistribute binary + macOS patch gap + vendor lock-in not worth it. Cheaper wins shipped instead:
- `playwright-stealth==1.0.6` added to `requirements.txt`. Applied to page in `ingestion/service.py:_capture_source_once` via lazy import (no hard dep if absent).
- `HTTP_PROXY`/`HTTPS_PROXY` env honored: Playwright `launch_kwargs["proxy"]` set; httpx already respects via default `trust_env=True`.
- Structured fallback telemetry: `logger.warning("ingestion.capture.fallback", extra=...)` on Playwright→httpx transition. Existing `transport_errors` metadata kept.
- `backend/legacy/services/scraper_service.py` deleted — verified orphan (only doc mention), CLAUDE.md bans `backend/legacy/` imports.
- 50/50 ingestion + scraper-task unit tests green; `compileall` clean.
- Revisit CloakBrowser if: source behind Cloudflare added, capture rate <90% on any source, or user-paste-URL feature lands.

## Open work
- S92: local pytest verify → pip-audit verify → docker build → commit + PR.
- **IP-based pricing fix on s92** — see `ip-pricing.md`. s90 shipped backend `/api/v1/geo/currency` via ipwho.is proxy; new plan swaps to **Cloudflare `CF-IPCountry` header** (orange-cloud proxy + DO firewall allowlist + 10-LOC backend). Working tree `s92/cve-bumps` is missing the s90 geo files; do not rebuild from current tree until CF plan applied.
- Smoke selector re-point + `ci.yml:198` `continue-on-error` removal (fails on `[data-testid="scholarship-browse-shell"]` in `public_scholarship_browse_smoke.py:11` — selector predates greenfield rebuild).
- S93 sprint: langchain + transformers + fastapi+starlette CVE bumps.
- Settings privacy panel polish; `docs/scholarai/IMPLEMENTATION_STATUS_REPORT.md` refresh to `_0027`.
- `tests/integration/test_trial_lifecycle.py` end-to-end; `tasks.run_usage_ledger_prune` Celery beat monthly.

## Knowledge graph (graphify)
- Location: `graphify-out/` (gitignored). Built 2026-05-25.
- Files: `graph.json` (raw, 3866 nodes / 7573 edges / 302 communities, 60 labeled), `graph.html` (interactive viz), `GRAPH_REPORT.md` (audit + god nodes + surprising connections + suggested questions), `manifest.json` (file fingerprints for `/graphify --update`), `cache/` (per-file semantic extraction cache), `cost.json` (token ledger).
- Corpus: 516 files (413 code + 103 docs). 418 frontend images skipped to save vision tokens.
- Token reduction: ~669× vs naive corpus read (~2.9k tokens/query vs ~1.96M).
- Top god nodes: `IngestionService` (177), `UserRole` (63), `FakeSession` (60), `DocumentService` (59), `Scholarship` (51), `InterviewSessionService` (52).
- Update: `/graphify C:\Users\HP\scholarai-platform --update` (re-extracts changed files only). Query: `/graphify query "<question>"`, path: `/graphify path A B`, explain: `/graphify explain X`.

Sticky knowns (do not re-investigate):
- `users.id` is `UUID(as_uuid=True)` — every FK col must use `postgresql.UUID(as_uuid=True)`.
- `Scholarship` ORM uses `title` + `provider_name` (NOT `name` / `provider`).
- Mailgun send returns `True` on log-only fallback (deterministic offline).
- Backend `/api/v1/health` (router) AND `/health` (app) are DISTINCT paths — both intentional.
- Mentor router included at both `/mentor` AND `/mentors` (alias) — neither is wrong.
- Alembic chain `0008→0011→0009→0010→...` non-monotonic naming but linear, single head.
