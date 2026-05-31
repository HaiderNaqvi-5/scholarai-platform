# CLAUDE.md

Guidance for Claude Code in this repo.

## Repo
ScholarAI — AI scholarship platform. **Pakistan-pivot (PRD `D:/Downloads/SCHOLARAI_PAKISTAN_PRD.md`)** targeting Pakistani students applying to UK / US / CA / DE / AU. Display brand: **AidwiseAI**. Repo / backend / internal docs: ScholarAI.
**Current state (2026-05-30):** backend feature-complete, **565 backend pass / 2 skip / 1 xfail**. Clerk auth + Resend email live (locally, opt-in via env). Frontend design passes S88→S94 shipped; **S95 Wave 2 in progress (uncommitted)**. **Monday-blocking security audit findings closed (`1fd6e64`): C2 XXE (defusedxml), H9 PII export auth-gate, H2 recommendations rate-limit, M25 CORS/CSP, legal slug drift — backend tsc/lint green, NO_SECRETS.** Deploy not yet shipped — see `DEPLOYMENT_PLAN.md`. Active branch this session: `s95/frontend-design-pass-wave2`.

**Source of truth hierarchy:** PRD → `.codex/AGENTS.md` → `AGENTS.md` → `docs/scholarai/IMPLEMENTATION_STATUS_REPORT.md` → `docs/scholarai/01..14*.md` → this file. Legacy `docs/*.md` transitional.
**⚠️ SoT freshness caveat (2026-05-30):** the docs ranked above are STALE vs current code — trust this CLAUDE.md + `progress.md` for current state. Known drift: `IMPLEMENTATION_STATUS_REPORT.md` (May 18) still says "Canada-first scope" (product is Pakistan-pivot) + pre-Clerk RBAC narrative; `AGENTS.md` (May 14) prescribes `npm ci`/`npm run` + `playwright install chromium` (repo is **Bun** + Firecrawl, Playwright dropped from capture); `.codex/AGENTS.md` (Mar 15) pre-pivot. PRD lives off-repo at `D:/Downloads/SCHOLARAI_PAKISTAN_PRD.md`. Refresh tracked in Open work.

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

## Frontend (status: S88 rebuild → S94 design pass shipped; S95 Wave 2 in progress)
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
- **S95 Wave 2** — commit + verify end-to-end (uncommitted, see Frontend design pass section).
- **Deployment** — `DEPLOYMENT_PLAN.md` drafted (Vercel FE / DO App Platform BE / Supabase Postgres). Blockers are release-eng (no single deployable branch; deploy work split across `main`/`s93`/`s94`/`s95`), not features.
- **ip-pricing migration** — `ip-pricing.md` plans swapping `/upgrade` currency detection from CSP-blocked `ipwho.is` to Cloudflare `CF-IPCountry` header (needs CF orange-cloud proxy). Not yet implemented.
- **HIBP password breach check** — WIRED into `AuthService.register()` (top, fail-fast, email-agnostic), gated by `HIBP_BREACH_CHECK_ENABLED` (default **False** → offline-deterministic tests; enable per-deploy on local AUTH_PROVIDER; no-op under Clerk since `/register` 410s first). `is_pwned` k-anonymity + fail-open in `core/hibp.py`. 5 tests in `tests/unit/test_hibp.py` (range match/miss/fail-open + register reject-when-enabled / skip-when-disabled).
- Smoke selector re-point + `ci.yml:198` `continue-on-error` removal (needs 3 green local runs).
- Refresh `docs/scholarai/IMPLEMENTATION_STATUS_REPORT.md`, `frontend/README.md`, `.codex/AGENTS.md` for Pakistan pivot + Clerk (SoT lag — see below).
- **Redo ingestion ops surfaces** (rolled back 2026-05-26; capture/SSRF in `~/.claude/plans/quirky-waddling-sloth.md`). Remaining: (B) staggered per-source scheduled fan-out + `ingestion-health-check` Celery beat + `GET /api/v1/curation/ingestion-runs/scheduled-status` + `<ScheduledStatusBanner>` on `/admin/ingestion`. (A) obsolete (Playwright removed from capture).

## Scraper cadence + Firecrawl (2026-05-26)
- Capture path: **Firecrawl Cloud** (`app/services/ingestion/firecrawl_capture.py`). Set `FIRECRAWL_API_KEY` in env. Playwright + Chromium removed from `Dockerfile` (base now `python:3.12-slim-bookworm`, ~250 MB vs ~1.5 GB).
- SSRF guard: `app/utils/url_safety.py` — `assert_public_url` (DNS resolves, rejects private/loopback/link-local/CGNAT/IPv4-mapped IPv6) and `safe_get` (manual redirect loop, 5-hop cap, no `verify=False`). Wired into `_get_or_create_source` + every discovery `httpx` call. Closes C1 + H8 in `security-audit.md`.
- Cadence: every 10 days (1st / 11th / 21st @ 02:00 UTC) via `crontab(hour=2, minute=0, day_of_month="1,11,21")`. Beat task is `tasks.run_scheduled_ingestion`; `tasks.run_nightly_ingestion` is a back-compat alias removable next deploy. Cost: ~300 Firecrawl credits/mo, fits free tier.
- KPI alert contract (`fix(admin)` `8ac5c5e`): `schemas/health.KpiAlertItem(domain, severity, message)`; `kpi_snapshot_service._domain_alert_message` returns object so `(admin)/admin/page.tsx:39-54` renders badge + tag + message. Severity `"warn"` today.
- Mailgun → Resend: `notifications/channels.send_email` POSTs `api.resend.com/emails`; `MAILGUN_*` envs removed (`config.py`, `.env.example`, `.do/app.yaml`). Log-only fallback when `RESEND_*` unset.
- Dep bumps (forced by Docker rebuild): `httpx 0.27 → 0.28.1`, `pydantic 2.9 → 2.10.6` (both required by `clerk-backend-api 1.6.0`). `playwright==1.52.0` re-added in `fix(ci)` `6223f18` (test-only; Dockerfile no longer runs `playwright install chromium` so prod image stays small).
- Tests: 39 new `tests/unit/test_url_safety.py` + 7 new `tests/unit/test_firecrawl_capture.py`; discovery tests mock `safe_get`; scraper-stale 25h → 264h. 511 pass + 1 xfailed.
- Merge into `main` (`8095daa`) + missing migration commit `5770874` (`alembic/versions/20260521_0027_add_bs_degree_level.py` — `_0028`/`_0029` chained to it; was raising `KeyError`). All 5 CI jobs green on PR #102. Full plan: `~/.claude/plans/quirky-waddling-sloth.md`.

## Q1 retier + Air University trial (2026-05-16, `feat/pakistan-frontend-pass`) — summary (full in `~/.claude/plans/memoized-cooking-hopper.md`)
**Q1 retier** (closeout `d20ab14`, alembic `20260516_0025`): new tables `sop_monthly_usage` (`_0024`) + `usage_ledger` (`_0025`), col `scholarships.tier` (`_0023`); `core/burn_cap.py` 60% per-tier monthly budget (`assert_within_burn_cap` 429); vocab guard `test_user_facing_vocab.py`; pricing PKR 2,999/6,000, caps free/pro/elite 3/6/12, SOP quotas 1/5/10; premium paywall on `/scholarships` (`_guard_premium_tier` → 402); WhatsApp-only Elite alerts (SMS removed); burn-cap LLM wrapper `AnthropicClient.complete_with_accounting`; FE neutral `MatchResponse` + `CompatibilityMeter`. **Air University trial** (alembic `20260516_0026`, May-19 booth now past): `invite_codes` + `air_uni_*` user cols; `AuthService._redeem_invite_code` row-locked (Pro via `AIRU2026`, 100 uses, 30d); `tasks/trial_tasks.py:expire_trial_plans` Celery beat daily; CLI `seed_invite_codes.py`/`grant_invite_uses.py`/`generate_qr_flyers.py`; deps `qrcode[pil]==7.4.2`, `sentry-sdk[fastapi]==2.18.0`.

## S87 Pakistan Frontend Pass (2026-05-15, `feat/pakistan-frontend-pass`)
**369 backend pass** (312 unit + 57 integration); FE green; docs gov 0 fails; KPI regression 17 pass. BE: `/auth/me` exposes plan/currency/country; professor_email + strategy_report (Elite 402, mig `_0022`); notifications log-only fan-out; alert/reminder Celery tasks; new routes `POST /documents/professor-email` + `POST /reports/strategy`; 28 new tests. FE: `isPlanRequiredError` + 6 new endpoint modules; `UpgradeWall` 402 verbatim; `app/upgrade` 4 tiers + 5-currency + waitlist; `(student)/{tracker,documents/sop,documents/professor-email,interviews/visa}`; PK landing; `(partners)/*` + PARTNER_ROLES in `RoleGuard`; sidebar adds Tracker + Visa-practice. `User` extended w/ plan/currency/country. Trust boundary: student excludes university; partner excludes every student role.

## Dev env notes (2026-05-12→15) — summary (full in `~/.claude/plans/memoized-cooking-hopper.md`)
Key live invariants: OpenSearch 2.11 needs `DISABLE_SECURITY_PLUGIN=true` + `DISABLE_INSTALL_DEMO_CONFIG=true`. `CORS_ORIGINS` covers `:3000`+`:3001`; backend roles lowercase StrEnum mirrored by FE `RoleGuard.ROLE_GROUPS`. `StudentProfile` 28 fields, `extra="forbid"`. `CurationService.list_records()` returns `(items, total)` w/ `page`/`page_size`. Signup min password 12 (backend Pydantic); login no min. Healthcheck split: `/livez` process-only, `/readyz` DB-ping, `/health` DB+version; per-service healthchecks in `docker-compose.yml`. `.gitignore` excludes `graphify-out/`. **S86 Scraper Ingestion** (2026-05-15, mig `_0021`): destination geo, JSON-LD+microdata, fuzzy-dedup `SequenceMatcher≥0.9`, snapshot drift sha256, multi-pagination, `GET /scholarships/{id}/provenance`, source-health (healthy/degraded/down at 0-2/3-5/≥6 fails).

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

**✅ FIXED (2026-05-31) — 3 contract crashes closed + runtime-verified.** Prior note found the documented curation split was never applied; it (and 2 sibling bugs) are now done:
- **/admin/curation/[id] + list** — `types.ts` `CurationRecord` split into `CurationRecordSummary`/`CurationRecordDetail` (alias `CurationRecord=Detail`) mirroring `schemas/curation.py`; pages read `record_state`/`review_notes`/typed fields; dead audit-log card removed (backend detail has no `audit_log`).
- **/discover** — backend `ScholarshipListItem` ENRICHED (`summary/funding_summary/funding_amount_min/max/source_url/field_tags/degree_levels`, optional/additive — catalog tests still pass) + populated in `routes/scholarships.py:_serialize_list_item`; detail builder de-duplicated (those kwargs now flow via `model_dump()`). FE `ScholarshipListItem` type + `ScholarshipCard` read the enriched lean shape (`scholarship_id`, guarded `field_tags`); `endpoints.scholarships.list` returns `ScholarshipListItemResponse`.
- **/feed recommendations** — FE `RecommendationItem`/`RecommendationListResponse` flattened (+`RecommendationResponseMeta`) to match flat backend; `feed/page.tsx` reads `item.*` not `item.scholarship.*`.
- **Deleted** `components/scholarship/RecommendationCard.tsx` (0 importers, obsolete nested contract; broke under reshape).
- Verified: `tsc --noEmit` 0, `eslint` 0; backend rebuilt → live `GET /scholarships` returns `field_tags`/`funding_summary`; browser drive (local-auth) → /discover (18 cards), /feed (dashboard+matches), /admin/curation/[id] (full detail) all render, 0 error boundaries. Admin analytics/audit/users P0s were already fixed. Full report: `progress.md` (2026-05-31).

## Clerk + Resend migration (2026-05-26→28, branch `s93/auth-tier-1`) — summary
Full Task 1–17 log (commit shas + per-task deviations) archived in `~/.claude/plans/memoized-cooking-hopper.md`; current Clerk state = "Clerk integration audit" section below + `CLERK_AUDIT.md` + `docs/operations/clerk-runbook.md`. What shipped: backend `AUTH_PROVIDER` switch (`config.py`), `User.clerk_user_id` (mig `20260526_0029`, applied), JWKS RS256 verifier (`integrations/clerk/jwt_verify.py`), lazy SDK client + `ensure_local_user[_async]` (`user_sync.py`, email-collision link), dual-mode `get_current_user` dispatcher (`dependencies.py`), Svix webhook `POST /api/v1/webhooks/clerk` (created/updated/deleted), legacy `/register /login /refresh /logout` → 410 when `provider=clerk`, Resend `send_transactional` (CRLF reject) + 7-template registry + `send_templated_email_best_effort` (best-effort, never 5xx), daily Celery reminder/alert emails templated, `clerk_bulk_import.py` + `clerk_seed_demo.py`. **Frontend (Task 10+17):** opt-in scaffold gated on `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`; Clerk OAuth (Google live) + magic-link + `ConnectedAccountsPanel`; `/sso-callback` route; CSP adds `*.clerk.accounts.dev` + `worker-src 'self' blob:`. **561 pass + 1 xfail.** Known: `clerk-backend-api 1.6.0` SDK is **sync** (no `await` on `api.users.*`); Resend SDK returns **dict** (`response["id"]`).

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
- **Prod CSP** — DONE (`fb069b2`, branch `s95/...wave2`): `frontend/next.config.ts` now adds `NEXT_PUBLIC_CLERK_FAPI` to connect/script/frame-src alongside `*.clerk.accounts.dev`. Operator must still **set `NEXT_PUBLIC_CLERK_FAPI`** to the deployed Clerk FAPI origin (e.g. `https://clerk.aidwiseai.com`) at build time; unset → dev-only hosts (no behavior change).
- **Activate iss/azp**: set `CLERK_ISSUER` + `CLERK_AUTHORIZED_PARTIES` in prod env to turn on the new binding.
- **`login/page.tsx` `?next=` open-redirect** — DONE (`fb069b2`): only same-origin relative paths honored; protocol-relative/backslash/absolute rejected.
- **`ScholarshipCard` external `source_url`** — DONE (`fb069b2`): `safeHttpUrl()` (new in `lib/utils.ts`) gates anchor href to http(s) only; blocks `javascript:`/`data:`/`blob:` from feeds. (Also repaired dangling ref — `safeHttpUrl` was used but undefined, build was broken.)
- Deferred lower-sev: CSP `'unsafe-inline'`→nonce; no backend session-revocation (clerk sessions honored until exp); frontend has zero test infra (proxy.ts/client.ts clerk branch/sso-callback untested); IntegrityError first-login race; `.env.example` stale `RESEND_FROM_ADDRESS` + `AUTO_SEED_DEMO_DATA=true`.

## Frontend design pass S94 + S95 Wave 2 (2026-05-29→30)
**S94 (SHIPPED, committed `dbf65c2`/`822b884`/`477c875` on `s94/frontend-design-pass`; full detail in `frontend/CLAUDE.md` S94 row + `~/.claude/plans/synthetic-popping-avalanche.md`):** audit P0/P1 + 3 competitor features. Mobile nav drawer, login split, outcome CTAs ("See my matches"), consultant-vs-AidwiseAI comparison table, **live scrollable scholarships rail** `components/marketing/ScholarshipsRail.tsx` (real `listPublic()` data, scroll-snap, edge-fade), role-mixing fix `primaryGroup(role)` in `RoleGuard.tsx`, password meter, scroll-driven progress bar. tsc+lint+build green (41 routes). **Flagged backend ticket (DECISION=enrich backend list, NOT FE):** `/discover`+`ScholarshipCard` read `s.id`/`s.field_tags` but `GET /scholarships` returns lean `ScholarshipListItem` → /discover crashes on live data; fix by enriching `ScholarshipListItem` (funding/field_tags/degree_levels/amount).
**S95 Wave 2 (IN PROGRESS, uncommitted on `s95/frontend-design-pass-wave2`; plan in `~/.claude/plans/`):** remaining P2 polish — rail autoplay, skeleton→content crossfade (`content-fade-in` util in `globals.css`), FAQ topic chips (`page.tsx`), admin/discover/feed grid crossfade, footer `LAST_UPDATED` constants, `button.tsx` tweak. tsc clean per session log; not yet committed/verified end-to-end.

## Backend engineering remediation (2026-05-30, branch `chore/backend-eng-remediation`)
Rebased onto `s93/auth-tier-1` (`ad14fef`). Closes engineering-standard gaps E1–E30 from `docs/superpowers/plans/2026-05-29-backend-engineering-remediation.md` (full plan + audit). **Phase 0 + Phase 1 shipped (7 commits); Phases 2–6 still pending.**
- **Phase 0 (test infra + CI gates):** test-only deps split into `backend/requirements-dev.txt` (E8); `asyncio_mode=auto` + dropped 16 blanket `pytestmark` (E30); **real Postgres `db_session`/`app_client` fixtures** in `tests/conftest.py` + `tests/integration/test_db_fixture_smoke.py`, Postgres-only, skip when `TEST_DATABASE_URL` unset (E6 keystone); new `backend-integration` CI job (pgvector/pg16 + redis) + root `permissions: contents: read` + concurrency-cancel + pip caching (E6/E9, closes sec-audit N34); coverage floor `--cov-fail-under=72` on backend-sanity (E9, actual 77%).
- **Phase 1 (data integrity):** synced `StudentProfile` to migration 0019 — 5 cols (`current_university_id`+FK, `target_university_ids`, `gmat_score`, `sat_score`, `budget_pkr_max`) + indexes + CHECKs the ORM never declared, so autogenerate no longer proposes dropping live columns (**E5 data-loss footgun closed**); added `User.plan` CHECK; removed 2 duplicate kpi-snapshot indexes that broke `create_all` (E31); reconciled all remaining ORM↔DB drift and wired **`alembic check` as a blocking CI gate** (E9/Task 1.2). `universities` rate cols aligned model→Float to match deployed `double precision`.
- **Deferred (decisions needed, NOT done):** **E32** — `compare_server_default=True` surfaces 38 server-default mismatches (DB has `gen_random_uuid()`/`'free'`/booleans the model sets Python-side only); needs an app-vs-DB default-strategy decision before enabling. **Task 1.3** (JSON→JSONB + missing indexes E25/E26) + **Phases 2–6** (concurrency E1–E4, observability, architecture, deps, test-depth) not started.
- **Verification (local):** real Postgres test DB `scholarai_test` (vector ext). `alembic check` clean; up/down round-trip clean; full suite **558 pass / 2 skip / 1 xfail** at the 561 baseline; coverage gate exit 0 (77%).

Sticky knowns (do not re-investigate):
- The Postgres test fixture uses **per-test drop/create** isolation, not savepoint — pytest-asyncio 1.3.0 session-vs-function loop-scope mismatch blocks the savepoint recipe. `import app.models.models` in conftest shadows the `app` fixture → use `importlib.import_module`.
- `users.id` is `UUID(as_uuid=True)` — every new model + migration must use `postgresql.UUID(as_uuid=True)` for FK columns.
- `Scholarship` ORM uses `title` + `provider_name` (NOT `name` / `provider`) — backfills/regex must match.
- `User.full_name` is NOT NULL with no server default — all User() test fixtures must include `full_name=`.
- `backend/tests/db/conftest.py` provides synchronous SQLite `db_session` fixture (does not need pgvector/ARRAY types).
- Mailgun send returns `True` on log-only fallback so callers stay deterministic offline.
- **Dev mode port conflict:** `docker compose up` binds frontend on :3000. While that container runs, `bun dev` cannot bind the port. Symptom: edits appear ignored because container serves stale build. Always `docker compose stop frontend` before `bun dev`. Backend container can stay up.
- **Turbopack cache fragility:** running `bun run build` while `bun dev` is also active corrupts `.next/turbopack` to a 0-byte file. Symptom: stale chunks served, runtime crashes on shape mismatches. Don't mix; wipe `.next/` if observed.
- **Frontend types are hand-synced** to backend Pydantic. `frontend/src/lib/api/types.ts` drifts every backend schema change. Run `bunx --bun tsc --noEmit` after touching `backend/app/schemas/`. Long-term fix tracked as `security-audit.md` D7 (OpenAPI codegen + CI diff gate).
