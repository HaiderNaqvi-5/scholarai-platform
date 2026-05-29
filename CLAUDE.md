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
- **Redo ingestion ops surfaces** (rolled back 2026-05-26; capture/SSRF threads now landed in `~/.claude/plans/quirky-waddling-sloth.md`). Remaining: (B) staggered per-source scheduled fan-out + `ingestion-health-check` Celery beat + `GET /api/v1/curation/ingestion-runs/scheduled-status` + `<ScheduledStatusBanner>` on `/admin/ingestion`. (A) is obsolete now that Playwright has been removed from the capture path. Pop `stash@{0}` on `s93/auth-tier-1` first to restore auth-tier WIP.

## Scraper cadence + Firecrawl (2026-05-26)
- Capture path: **Firecrawl Cloud** (`app/services/ingestion/firecrawl_capture.py`). Set `FIRECRAWL_API_KEY` in env. Playwright + Chromium removed from `Dockerfile` (base now `python:3.12-slim-bookworm`, ~250 MB vs ~1.5 GB).
- SSRF guard: `app/utils/url_safety.py` — `assert_public_url` (DNS resolves, rejects private/loopback/link-local/CGNAT/IPv4-mapped IPv6) and `safe_get` (manual redirect loop, 5-hop cap, no `verify=False`). Wired into `_get_or_create_source` + every discovery `httpx` call. Closes C1 + H8 in `security-audit.md`.
- Cadence: every 10 days (1st / 11th / 21st @ 02:00 UTC) via `crontab(hour=2, minute=0, day_of_month="1,11,21")`. Beat task is `tasks.run_scheduled_ingestion`; `tasks.run_nightly_ingestion` is a back-compat alias removable next deploy. Cost: ~300 Firecrawl credits/mo, fits free tier.
- KPI alert contract (`fix(admin)` `8ac5c5e`): `schemas/health.KpiAlertItem(domain, severity, message)`; `kpi_snapshot_service._domain_alert_message` returns object so `(admin)/admin/page.tsx:39-54` renders badge + tag + message. Severity `"warn"` today.
- Mailgun → Resend: `notifications/channels.send_email` POSTs `api.resend.com/emails`; `MAILGUN_*` envs removed (`config.py`, `.env.example`, `.do/app.yaml`). Log-only fallback when `RESEND_*` unset.
- Dep bumps (forced by Docker rebuild): `httpx 0.27 → 0.28.1`, `pydantic 2.9 → 2.10.6` (both required by `clerk-backend-api 1.6.0`). `playwright==1.52.0` re-added in `fix(ci)` `6223f18` (test-only; Dockerfile no longer runs `playwright install chromium` so prod image stays small).
- Tests: 39 new `tests/unit/test_url_safety.py` + 7 new `tests/unit/test_firecrawl_capture.py`; discovery tests mock `safe_get`; scraper-stale 25h → 264h. 511 pass + 1 xfailed.
- Merge into `main` (`8095daa`) + missing migration commit `5770874` (`alembic/versions/20260521_0027_add_bs_degree_level.py` — `_0028`/`_0029` chained to it; was raising `KeyError`). All 5 CI jobs green on PR #102. Full plan: `~/.claude/plans/quirky-waddling-sloth.md`.

## Q1 retier (2026-05-16, branch `feat/pakistan-frontend-pass`)
Tasks 1-17 across 21 commits `23942f5..d20ab14`. **444 backend pass + 1 xpass**, frontend green, vocab guard 6+1xpass. Closeout `d20ab14`. Alembic head `20260516_0025`; scholarships 6 premium / 20 standard.
- New tables `sop_monthly_usage` (`_0024`) + `usage_ledger` (`_0025`); col `scholarships.tier` (`_0023` keyword backfill).
- `core/burn_cap.py` — 60% per-tier monthly budget, `assert_within_burn_cap` 429, ledger writers.
- Vocab guard `tests/unit/test_user_facing_vocab.py` blocks internal classification tokens leaking.
- Pricing: PKR 2,999 / 6,000 monthly. Caps free/pro/elite = 3/6/12 (matches + tracker). SOP quotas 1 lifetime / 5 / 10 monthly.
- Premium paywall on `/scholarships` catalog (list filter for `tier=standard` if anon/non-premium; detail/provenance via `_guard_premium_tier` → 402).
- WhatsApp-only Elite alerts; SMS removed; `fan_out_for_plan` async.
- Burn-cap LLM wrapper — `AnthropicClient.complete_with_accounting` pre-flights cap; sop_builder + visa evaluator + professor_email + strategy_report migrated.
- FE — neutral `MatchResponse`, new `CompatibilityMeter`, `(student)/scholarships/page.tsx` match UI, `upgrade/page.tsx` `tier`→`plan` rename.

## Air University exhibition trial launch (2026-05-16, branch `feat/pakistan-frontend-pass`)
Backend for May-19 booth — Pro plan via shared invite `AIRU2026`, 100 redemptions, 30 days/user. Push gate **454 pass + 1 xpass**.
- Migration `20260516_0026` adds `invite_codes` + 4 user cols (`air_uni_*`, `redeemed_invite_code` indexed).
- `AuthService._redeem_invite_code` row-locked; 400 on unknown/inactive/out-of-window/exhausted. Sets plan + expiry + code on success.
- `tasks/trial_tasks.py:expire_trial_plans` Celery beat daily 02:00 UTC. Idempotent UPDATE.
- Mailgun `send_email` POSTs to `${MAILGUN_BASE_URL}/${MAILGUN_DOMAIN}/messages` via httpx; fail-soft to log-only when keys absent.
- Dockerfile bakes Chromium for scraper worker (`playwright install --with-deps chromium`, image ≈1.2GB).
- CLI: `seed_invite_codes.py` (AIRU2026, 100 uses, May 19→26 PKT), `grant_invite_uses.py`, `generate_qr_flyers.py` (900×900 PNG of signup URL).
- New deps: `anthropic==0.39.0`, `qrcode[pil]==7.4.2`, `sentry-sdk[fastapi]==2.18.0`.
- Tests: `test_trial_tasks.py` (4 pass) + 6 invite-redemption cases in `test_auth_service.py`.

## S87 Pakistan Frontend Pass (2026-05-15, `feat/pakistan-frontend-pass`)
**369 backend pass** (312 unit + 57 integration); FE green; docs gov 0 fails; KPI regression 17 pass. BE: `/auth/me` exposes plan/currency/country; professor_email + strategy_report (Elite 402, mig `_0022`); notifications log-only fan-out; alert/reminder Celery tasks; new routes `POST /documents/professor-email` + `POST /reports/strategy`; 28 new tests. FE: `isPlanRequiredError` + 6 new endpoint modules; `UpgradeWall` 402 verbatim; `app/upgrade` 4 tiers + 5-currency + waitlist; `(student)/{tracker,documents/sop,documents/professor-email,interviews/visa}`; PK landing; `(partners)/*` + PARTNER_ROLES in `RoleGuard`; sidebar adds Tracker + Visa-practice. `User` extended w/ plan/currency/country. Trust boundary: student excludes university; partner excludes every student role.

## Dev env notes (2026-05-12)
- OpenSearch 2.11 needs `DISABLE_SECURITY_PLUGIN=true` + `DISABLE_INSTALL_DEMO_CONFIG=true` or backend never starts.
- Backend Dockerfile stage-2: `--find-links=/wheels -r requirements.txt --default-timeout=600 --retries 10`; `pip install /wheels/*` re-fetches CUDA wheels + times out.
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

## PR #87 + Q1 retier live (2026-05-17)
PR https://github.com/HaiderNaqvi-5/scholarai-platform/pull/87 all-green after 4 root-cause fixes. Alembic head `20260516_0026 (head)`. All checks SUCCESS, mergeStateStatus=CLEAN. Key fixes: missing FE imports cluster (`f5a8391`), `InviteCode` model re-export (`ee94799`), `MatchResponse` schema re-apply (`8140338`), empty commit to clear stuck Vercel build (`24ba352`).

## S20 Security hardening pass (2026-05-18, `feat/s89-premium-cultural`)
P0+P1 closed (`SECURITY_AUDIT.md`). 396 unit + 63 integration pass; FE green; create_app() 112 routes. Shipped: SecurityHeadersMiddleware (HSTS/X-Frame DENY/CSP) + TrustedHostMiddleware gated by ALLOWED_HOSTS; `next.config.ts:headers()` mirror; `AUTO_SEED_DEMO_DATA=False` default; OPENSEARCH_PASSWORD prod-reject defaults; CORS rejects localhost in prod; `ProxyHeadersMiddleware` when `TRUSTED_PROXY_HOPS>0`; `core/account_lockout.py` Redis 5/15min sliding window (fail-open, 5 tests); `UserLogin.password min_length` dropped (422-leak fix); FE Dockerfile `oven/bun:1-alpine` + tini + non-root + HEALTHCHECK; `capture_exception` in 500 handler; Mailgun `_sanitize_header()` CR/LF/NUL strip; `pip-audit` in CI; `/health` DB+version only. **Deferred:** S6 TLS, S9 refresh rotation, S16 httpOnly cookies, S17 TOTP, S18 Argon2id, S19 RS256.

## S89.2 landing rotator + IP currency (2026-05-18, branch `feat/s89-premium-cultural`)
Commits `02bc5bb` + `7b85c46`. Lint + tsc + build green (40 routes); 0 emoji / 0 gradient text / 0 heavy backdrop-blur / 0 heavy shadow across 123 files.
- **Hero word cycler**: `frontend/src/components/marketing/RotatingDegree.tsx` cycles `bachelor's → master's → PhD` in landing h1 (opacity fade 320ms, 2.2s hold, `aria-live="polite"`, `prefers-reduced-motion` honored, `min-w-[5ch]` no layout jump).
- **Auto IP currency**: `lib/geo/useGeoCurrency.ts` hits `ipwho.is`, 24h localStorage cache (`aidwise.geo_currency`), maps to supported set, PKR fallback. `/upgrade` 5-button switcher deleted → `DetectedCurrency` chip; precedence `?currency=` > `auth.user.plan_currency` > geo > PKR; error-state "Show in PKR" preserved via internal override.
- **Stripe consistency**: `(mentor)/mentor/documents/[id]` `ListEditor` danger tone swapped raw `border-l-2 border-l-danger pl-3` for `danger-stripe` `@utility`.

## S89.1 cleanup pass (2026-05-18, branch `feat/s89-premium-cultural`)
Closes S89 progress.md items. Lint + tsc + build + emoji-grep green across 121 files. Match alias at `(student)/dashboard/scholarships/match` re-exports `/scholarships`. `StudentProfile` type sync 10→28 fields mirroring `backend/app/schemas/students.py` (5 new string-literal aliases). `/profile` 3→6 cards per §6.22 (Contact / Academic / Test scores / Goal w/ multi-select chips / Aspirations / Background) via new `components/profile/MultiChip.tsx`. Admin / mentor / partners (12 routes) headers → `PageHeader`, KPI Fraunces 3xl → JBM 28/tabular-nums, `caution-stripe` on alert card, testids backfilled. Backend gaps: Mailgun + Sentry keys appended to `.env.example` + `core/config.py`; `_init_sentry()` gated by `SENTRY_DSN`. Deferred (need 3 green local runs): smoke selector re-point + `ci.yml:198` flag removal.

## S89 Premium Cultural pass (2026-05-17 → 2026-05-18, branch `feat/s89-premium-cultural`)
Closes student-core delta + 6 missing routes (not-found/error/offline/denied/maintenance/legal[slug]). Audit harness at `frontend/scripts/audit/`. /saved Kanban→list + Promote-to-tracker. /documents/new deleted → /sop. Repaints: /documents, /documents/[id], /profile (6 cards), /settings (6 tabs + TypedConfirm), /interviews, /scholarships/[id] (sticky aside), /discover (pagination). Legal endpoint module `lib/api/endpoints/legal.ts`. 11 testids backfilled. Deferred: smoke selector re-point + `ci.yml:198` flag removal.

## Backend gap audit (2026-05-17 → 18, post-PR-#87)
S89.1 closed: env-docs + Sentry init. Open: `ci.yml:198` `continue-on-error` (needs 3 green local smoke runs); IMPLEMENTATION_STATUS_REPORT refresh; prod `AIRU2026` seed; `zara.khan` demo persona decision; `tests/integration/test_trial_lifecycle.py`; Celery beat `tasks.run_usage_ledger_prune` (purge `usage_ledger` >13 months). Soft: celery `broker_connection_retry_on_startup` warning; `pytest.mark.asyncio` mis-mark `test_document_service.py:286`.

## /admin/curation crash fix (2026-05-27, branch `s93/auth-tier-1`)
**Symptom:** `TypeError: ...reading 'length'` post-hydration → root `app/error.tsx` "Something went wrong on our side."
**Real root cause:** Docker container `scholarai-platform-frontend` was binding :3000; `bun dev` never started; container served stale build with `r.audit_log.length>0` (old schema). Two contributing bugs: stale `CurationRecord` type in `frontend/src/lib/api/types.ts` + corrupted `.next/turbopack` (0-byte file).
**Fix:** `frontend/src/lib/api/types.ts` — split `CurationRecord` into `CurationRecordSummary` + `CurationRecordDetail` + `CurationRecordListResponse` mirroring `backend/app/schemas/curation.py:126-168`; back-compat alias `export type CurationRecord = CurationRecordDetail`. `frontend/src/lib/api/endpoints/curation.ts` return types updated.
**Outstanding drift (same class, not fixed):** `RoleChangeAudit` consumers in `/admin/audit/page.tsx:67,69,75,76,127`; `PlatformAnalytics` in `/admin/page.tsx`; `AccessControlManagedUser` missing export. See `security-audit.md` D2–D4 / D7.

## Clerk + Resend migration (2026-05-26, branch `s93/auth-tier-1`)
Task 1: `backend/app/core/config.py` — Clerk/Resend settings + `AUTH_PROVIDER` (commits `d9ad076` + `600b04a`).
Task 2: `User.clerk_user_id` (String 64, nullable, unique, indexed) added to model + migration `20260526_0029` (parent `20260525_0028`) + tests in `backend/tests/db/` with SQLite in-memory `db_session` fixture (commit `68bc086`). Migration not yet applied (no live DB in session). Alembic head after Task 2: `20260526_0029`.
Task 3: `backend/app/integrations/clerk/jwt_verify.py` — JWKS-cached RS256 verifier (`verify_clerk_jwt`, `ClerkClaims`, `ClerkAuthError`). PyJWT 2.9.0 added to `requirements.txt`. 4/4 tests in `backend/tests/integrations/test_clerk_jwt_verify.py` pass. Commit `e616b47`.
Task 4: `backend/app/integrations/clerk/client.py` (lazy-import `Clerk` SDK) + `user_sync.py` (`ensure_local_user`: lookup → Clerk fetch → email-collision link → create with `full_name`). `tests/integrations/conftest.py` re-exports `db_session` fixture. 3/3 tests pass, 7/7 integrations green. Commit `ede6c51`. Deviation: `clerk_backend_api` import deferred inside function to avoid `ModuleNotFoundError` in test environments where the package can't be built (pydantic-core wheel fails on Python 3.14).
Task 5: Dual-mode `get_current_user` dispatcher. `dependencies.py`: existing body moved verbatim to `_get_user_from_local_jwt`; `_get_user_from_clerk_jwt` added (verify_clerk_jwt → ensure_local_user_async → sets `_token_capabilities` from `get_role_capabilities`; uses ScholarAIException not HTTPException). `user_sync.py`: `ensure_local_user_async` (AsyncSession sibling) added; sync version unchanged. `tests/api/test_clerk_protected_route.py`: 2 tests (reject bad token → 401, accept mock clerk JWT → 200). 518 pass + 1 xfail, 0 regressions. Commit `c632eb4`.
Task 6: `backend/app/api/v1/routes/clerk_webhook.py` — `POST /api/v1/webhooks/clerk`. Svix HMAC verification; handles user.created (ensure_local_user_async), user.updated (email+full_name sync), user.deleted (is_active=False soft-delete). Wired in `api/v1/__init__.py`. 3/3 tests in `tests/integrations/test_clerk_webhook.py` (TestClient + duck-typed fake async session + dependency_overrides[get_db]). 524 pass + 1 xfail. Commit `6b328e4`. Note: pre-existing failure in `test_config_clerk_resend.py::test_prod_rejects_blank_clerk_when_provider_clerk` (Task 1 config validation order bug, not Task 6).
Task 7: `backend/app/integrations/resend/` — `send_transactional` wrapper with CRLF injection rejection, Pydantic `TransactionalRequest` (`EmailStr` + `Literal` template), 2-template registry (`welcome`, `data_export_ready`). `email-validator==2.2.0` added to `requirements.txt`. `configure()` reads env var at call-time (not Settings singleton) so monkeypatch works. 3/3 tests pass. Full suite: 528 pass + 1 xfail. Commit `e4a7e01`. Known production divergence: `resend.Emails.send()` returns `dict` with `"id"` key in real SDK 2.5.1, but `send.py` calls `response.id` (attribute access) which matches the `MagicMock(id=...)` test mock. In production this will raise `AttributeError` — workaround: `response["id"]` or SDK wraps it in an object (verify at deploy time).
Task 8: `send_email_notification(*, to, template, context) -> str` added to `backend/app/services/notifications/channels.py` as a thin wrapper over `send_transactional`. Additive only — existing `send_email` (async, free-text, User object) left intact. `from app.integrations.resend.send import send_transactional` import added. `backend/tests/services/__init__.py` + `test_notifications_resend.py` created. 1/1 test pass. Full suite: 529 pass + 1 xfail. Commit `935eb6b`.
Task 9: `_ensure_local_provider()` helper + `_LOCAL_PROVIDER_DEP = Depends(...)` on `auth.py` `/register /login /refresh /logout` returns 410 when `AUTH_PROVIDER=clerk`; `/me` ungated. 4/4 tests, 533 pass + 1 xfail. Commit `76cd469`.
Task 10: Frontend Clerk scaffold (opt-in via `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`). `(auth)/sign-in` + `sign-up` routes (Clerk components); `middleware.ts` gates on env flag (pass-through when blank); `providers.tsx` wraps in `<ClerkProvider>` only when key set; `next.config.ts` CSP adds `*.clerk.accounts.dev`, `clerk-telemetry.com`, `challenges.cloudflare.com` to `connect-src` / `script-src` / `frame-src`. Local auth path stays intact. Deferred: `lib/api/client.ts` token-source rewrite, `/login` `/signup` redirects, Playwright tests. Commit (forthcoming).
Task 11: `backend/scripts/clerk_bulk_import.py` (`import_user` idempotent on `User.clerk_user_id`) + `clerk_seed_demo.py` (admin/mentor/student). Placed under `backend/scripts/` (not repo-root `scripts/`) to avoid pytest namespace-package shadowing. `backend/tests/scripts/test_clerk_bulk_import.py` 2/2 pass. Commit (forthcoming).
Task 12: `docs/operations/clerk-runbook.md` (key rotation, webhook re-delivery, GDPR deletion, rollback). CLAUDE.md + `progress.md` updated. Commit (forthcoming).
Task 13 (2026-05-27): Transactional email surface wired. 5 templates registered in `app/integrations/resend/send.py:_TEMPLATES` — `welcome`, `data_export_ready`, `account_deletion_scheduled`, `account_deletion_cancelled`, `waitlist_confirmation`. All call sites use `send_templated_email_best_effort(*, to, template, context, source)` (new helper in `app/services/notifications/channels.py`) — best-effort try/except so Resend outage never 5xx's the trigger endpoint. Welcome fires only on genuinely-new Clerk `user.created` (pre-existence check by `clerk_user_id` AND `email`; linked/returning users skipped). New `FRONTEND_BASE_URL` setting drives CTA links (`/login`, `/settings/privacy`). Pre-existing `extra=forbid` Settings bug fixed by adding `extra="ignore"` to `SettingsConfigDict`.

Task 14 (Phase 2, 2026-05-27): Daily Celery email channels migrated to templates. `deadline_reminder` + `priority_alert` added to `_TEMPLATES` (registry now 7). `fan_out_for_plan` signature changed to `(db, user, *, email_template, email_context, whatsapp_message)` — email branch dispatches via `send_templated_email_best_effort`, WhatsApp branch unchanged (still log-only + `record_whatsapp` ledger row). `tasks/reminder_tasks.py` builds `upcoming: [{title, deadline_iso, days_left}]`; `tasks/alert_tasks.py` builds `scholarships: [{title, deadline_iso, country}]`. Free-text email path through `send_email(user, message)` no longer used by either daily task. `test_reminder_tasks.py` + `test_alert_tasks.py` updated with `_patch_channels` over `send_templated_email_best_effort`. **561 pass + 1 xfail** (was 553).

Task 15 (Phase 3a, runbook only): Clerk Dashboard procedure documented for re-branding the 4 lifecycle emails (verification / magic link / password reset / invitation) as AidwiseAI. Logo + sender + reply-to + subject table in `docs/operations/clerk-runbook.md` "Clerk lifecycle email branding" section. No code; dashboard work owned by operator per environment.

Task 16 (Phase 3b, optional, runbook only): Resend-as-Clerk-SMTP setup documented. Sub-domain split (`mail.aidwiseai.com` for Clerk lifecycle, apex `aidwiseai.com` for product-transactional). Defer until Clerk volume >500/day.

Task 17 (Clerk OAuth + magic-link + connected-accounts, 2026-05-27→28, commits `334df4d`/`94fe605`/`6b3ab67`/`df37604`/`83eb589`): `clerkAdapter` adds `useClerkSocialLogin`/`useClerkSocialSignup`/`useClerkMagicLink` + `SOCIAL_PROVIDERS` single-source array (Google live; Microsoft/Facebook/LinkedIn strategy maps kept on disk, just narrowed out of UI). `components/auth/SocialAuthButtons` 2×2 grid above email form (inline brand SVGs, no npm dep). `app/sso-callback/page.tsx` mounts `<AuthenticateWithRedirectCallback signInFallbackRedirectUrl="/feed" signUpFallbackRedirectUrl="/onboarding"/>` (explicit props — Clerk defaults to dashboard `/` otherwise). `/login` adds password→magic-link→magic-sent mode toggle (30s resend cooldown); `/signup` adds `<div id="clerk-captcha"/>` mount (silences Smart-CAPTCHA console warning). `components/settings/ConnectedAccountsPanel` lists `user.externalAccounts`; Disconnect/Connect rows refuse to orphan last identification method. `proxy.ts` adds `/sso-callback` to public matcher. `next.config.ts` CSP adds `worker-src 'self' blob:` (Clerk Web Workers) + `*.clerk.accounts.dev` on connect-src/script-src/frame-src. **Bugfix `df37604`**: `clerk-backend-api 1.6.0` SDK is sync — dropped `await` on `api.users.get(user_id=...)` in both `ensure_local_user` + `ensure_local_user_async` (TypeError in prod; tests mocked with `AsyncMock` so never caught it). **Env wire-up**: root `.env` = `ENV_FILE=backend/.env` so compose loads real Clerk keys instead of `.env.example`; `backend/.env` DB/Redis URLs switched from `localhost` to docker service hostnames (`postgres`, `redis`); migration `20260526_0029` (clerk_user_id column) applied via `docker compose exec backend alembic upgrade head`. **Live**: Google → `/sso-callback` → `/feed`, `/me` returns 200, reload-still-authed.

## Clerk integration audit + fixes (2026-05-29→30, branch `s93/auth-tier-1`)
Full report: `CLERK_AUDIT.md` (25 confirmed findings, 6-dimension adversarially-verified). Verdict: Clerk structurally correct, but had defects masked by a CI gap. Fixed this session (all surgical, **561 backend pass + 1 xfail** across all test dirs):
- **CI collected 0 of 42 Clerk/Resend tests** — `ci.yml:29` ran `tests/integration` (singular); Clerk suites live in `tests/integrations` (plural) + `tests/api|core|db|services|scripts`. Added all dirs. This gap hid every bug below.
- **`tests/integrations/test_clerk_user_sync.py`** stale `AsyncMock`→`MagicMock` (sync SDK). 14/14 clerk tests green.
- **`resend/send.py:68`** `response.id`→`response["id"]` (SDK 2.5.1 returns dict; was a silent total-email-outage in prod, swallowed by best-effort wrapper). Test mocks flipped to real dict.
- **`scripts/clerk_bulk_import.py` + `clerk_seed_demo.py`** dropped `await` on sync `api.users.create()` (same class as df37604). Test mock `AsyncMock`→`MagicMock`.
- **`jwt_verify.py`** JWKS httpx error now → `ClerkAuthError` (was raw 500 across authed surface); removed dead `lru_cache` import.
- **`jwt_verify.py` + `config.py`** added **env-gated** `iss`/`azp` validation (`CLERK_ISSUER`, `CLERK_AUTHORIZED_PARTIES` CSV). OFF until set → no behavior change. Closes cross-app token-reuse.
- **`dependencies.py`** `_get_user_from_clerk_jwt` maps `ValueError` (no primary email)→401 not 500.
- **`tests/unit/test_auth_claim_enforcement.py`** pinned `AUTH_PROVIDER=local` (autouse fixture) — was failing locally because ambient `.env` sets `AUTH_PROVIDER=clerk`, routing local-path tests to clerk path.

**Open (need operator decisions / values, NOT done):**
- **Prod CSP** `frontend/next.config.ts` only allows `*.clerk.accounts.dev`; a production custom-domain Clerk instance (e.g. `clerk.aidwiseai.com`) is blocked on connect/script/frame-src → silent auth break in prod. Add the prod FAPI host (needs the deployed Clerk domain).
- **Activate iss/azp**: set `CLERK_ISSUER` + `CLERK_AUTHORIZED_PARTIES` in prod env to turn on the new binding.
- Deferred lower-sev: CSP `'unsafe-inline'`→nonce; no backend session-revocation (clerk sessions honored until exp); frontend has zero test infra (proxy.ts/client.ts clerk branch/sso-callback untested); `login/page.tsx` `?next=` open-redirect; IntegrityError first-login race; `.env.example` stale `RESEND_FROM_ADDRESS` + `AUTO_SEED_DEMO_DATA=true`.

Sticky knowns (do not re-investigate):
- `users.id` is `UUID(as_uuid=True)` — every new model + migration must use `postgresql.UUID(as_uuid=True)` for FK columns.
- `Scholarship` ORM uses `title` + `provider_name` (NOT `name` / `provider`) — backfills/regex must match.
- `User.full_name` is NOT NULL with no server default — all User() test fixtures must include `full_name=`.
- `backend/tests/db/conftest.py` provides synchronous SQLite `db_session` fixture (does not need pgvector/ARRAY types).
- Mailgun send returns `True` on log-only fallback so callers stay deterministic offline.
- **Dev mode port conflict:** `docker compose up` binds frontend on :3000. While that container runs, `bun dev` cannot bind the port. Symptom: edits appear ignored because container serves stale build. Always `docker compose stop frontend` before `bun dev`. Backend container can stay up.
- **Turbopack cache fragility:** running `bun run build` while `bun dev` is also active corrupts `.next/turbopack` to a 0-byte file. Symptom: stale chunks served, runtime crashes on shape mismatches. Don't mix; wipe `.next/` if observed.
- **Frontend types are hand-synced** to backend Pydantic. `frontend/src/lib/api/types.ts` drifts every backend schema change. Run `bunx --bun tsc --noEmit` after touching `backend/app/schemas/`. Long-term fix tracked as `security-audit.md` D7 (OpenAPI codegen + CI diff gate).
