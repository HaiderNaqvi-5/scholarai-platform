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
P0+P1 closed (`SECURITY_AUDIT.md`). 396 unit + 63 integration pass; FE green; create_app() 112 routes.
- **S1 BE headers** SecurityHeadersMiddleware (HSTS/X-Frame DENY/X-CTO/Referrer/Permissions/COOP/CORP/CSP default-src 'none') + TrustedHostMiddleware gated by ALLOWED_HOSTS.
- **S2 FE headers** `next.config.ts:headers()` mirrors BE; CSP allows API origin; prod drops `'unsafe-eval'`.
- **S3/S4** `AUTO_SEED_DEMO_DATA=False` default; `OPENSEARCH_PASSWORD` setting + prod rejects defaults; `ALLOWED_HOSTS` required in prod.
- **S5** prod CORS rejects localhost. **S7** `ProxyHeadersMiddleware` when `TRUSTED_PROXY_HOPS > 0`.
- **S8 lockout** new `core/account_lockout.py` Redis sliding window per email (5 fail/15min → 15-min lock). Fail-open. 5/5 tests.
- **S10** `UserLogin.password min_length` dropped (422 leak fix). **S11 Dockerfile** `oven/bun:1-alpine` + `--frozen-lockfile` + tini + non-root + HEALTHCHECK.
- **S12** `capture_exception` in catch-all 500. **S13** Mailgun `_sanitize_header()` strips CR/LF/NUL.
- **S14** `pip-audit` in CI backend-sanity. **S15** `/health` public probe DB+version only.
- **Deferred** (`SECURITY_AUDIT.md`): S6 caddy/TLS, S9 refresh rotation, S16 httpOnly cookies, S17 TOTP, S18 Argon2id, S19 RS256.

## S89.1 cleanup pass (2026-05-18, branch `feat/s89-premium-cultural`)
Closes open items from S89 progress.md. Lint + tsc + build + emoji-grep green across 121 files.
- **Match alias**: `(student)/dashboard/scholarships/match/page.tsx` re-exports `/scholarships` — sidebar / onboarding / feed stop 404-ing.
- **StudentProfile sync 10→28 fields** mirroring `backend/app/schemas/students.py`. 5 new string-literal aliases.
- **/profile 3→6 cards** per §6.22 (Contact / Academic record / Test scores / Your goal w/ multi-select chips / Aspirations / Background). New `components/profile/MultiChip.tsx`.
- **Admin / mentor / partners** (12 routes) headers → `PageHeader`, KPI Fraunces 3xl → JBM 28/tabular-nums, `caution-stripe` on alert card, testids backfilled.
- **Backend gap quick wins**: Mailgun + Sentry keys appended to `.env.example` + `core/config.py`; `_init_sentry()` gated by `SENTRY_DSN` (no-op when unset, fail-soft on init).
- **Deferred** (need live backend + 3 green local runs): smoke selector re-point + `ci.yml:198` flag removal. Recipe in `progress.md`.

## S89 Premium Cultural pass (2026-05-17 → 2026-05-18, branch `feat/s89-premium-cultural`)
Closes the student-core delta routes + 6 missing routes from `Front-upgrade.md` §3.1 IA. Two commits: `cb9cfbb` (audit harness + missing routes + repaints) and the landing polish follow-up. Lint + tsc + build all green. `emoji-grep` 0 hits across 119 source files.
- **Audit harness** at `frontend/scripts/audit/`: state-matrix runner over routes × viewports × states. Uses `@axe-core/playwright` (severity ≥ serious blocks), copy-grep against §7.5 banned-phrase ledger, source-tree emoji guard, `page.route()` mocks for 402/500/empty/loading, token-injecting auth as `zara.khan` for `(student)` routes. Output: `audit-out/REPORT.md`. Scripts: `bun run audit` / `audit:public` / `audit:emoji` / `audit:self-test`.
- **6 missing routes**: `/not-found.tsx`, `/error.tsx` + `/global-error.tsx`, `/offline`, `/denied`, `/maintenance`, `/legal/[slug]` (server component with `generateStaticParams` over `[terms, privacy, dpa, cookie, refund]`, prints to body-only via `print.css`). `OfflineBanner` + `ConsentBar` mounted globally in `providers.tsx`.
- **/saved rewrite**: Kanban → list + sort dropdown (Recently saved / Deadline) + inline Promote-to-tracker (POST `/tracker` then DELETE saved, optimistic + rollback) + Remove. `setStatus` mutation pattern preserved. Touch-friendly kebab replaces drag.
- **/documents/new deleted**: not in IA §3.1. All references updated to `/documents/sop`.
- **Repaints**: /documents (Add dropdown via Radix DropdownMenu, URL-stateful FilterChips, lg+ table / sm cards, status labels Draft / Final / Failed-retry), /documents/[id] (explicit border-left stripes via `@utility validated-stripe`/`generated-stripe`, Fraunces 24 italic title), /profile (6-card spec frame within current `StudentProfile` type, PageHeader + StickySaveFooter), /settings (6-tab structure: Account / Privacy / Notifications / Appearance / Plan / Danger; TypedConfirm "DELETE MY ACCOUNT" wires to existing `/privacy/account-deletion` 30-day window), /interviews (TrendStrip with 5 rubric chips + RubricSparkline, two CTAs Practice visa / generic), /scholarships/[id] (sticky AsideAtAGlance — deadline + funding + "Estimated Scholarship Fit Score" verbatim + source), /discover (Pagination component prev / numbered / next with ellipsis ≥5).
- **Landing polish (2026-05-18)**: hero now 2-col at lg+ with right editorial preview card (3 live providers + "See 17 more →"), FAQ section (6 Q's, native `<details>`, no JS), closing CTA before footer ("Start the application your consultant won't draft."), 5 section eyebrows lifted `text-ink-subtle` → `text-lapis` for palette presence within spec restraint ("one accent per screen" §2.1 respected).
- **Endpoint module**: `lib/api/endpoints/legal.ts` exports `legal.{document, consentState, grant}` + `privacy.{requestExport, exportStatus, scheduleDeletion, cancelDeletion}`. New types: `LegalDocument`, `ConsentState`, `ConsentGrantInput`, `DataExportResponse`, `DataDeletionRequestResponse`.
- **11 data-testids** backfilled for future smoke re-point: `saved-list`, `documents-list`, `discover-grid`, `interviews-list`, `profile-form`, `settings-tabs`, `legal-doc`, `scholarships-list`, `tracker-board`, `visa-setup-form`, `interview-session-shell`.
- **Deferred**: smoke selector re-point in `tests/e2e/playwright/*.py` + removal of `.github/workflows/ci.yml:198` `continue-on-error: true` require 3 consecutive green local runs against `docker compose up` first (plan mitigation #3).

## Backend gap audit (2026-05-17 → 18, post-PR-#87)
Frontend out of scope. Open items strictly on backend / ops. ✅ = resolved in S89.1.

| Area | Gap | Status |
|------|-----|--------|
| Env docs | `backend/.env.example` lacks Mailgun + Sentry keys. | ✅ S89.1 — keys appended. |
| Observability | `sentry-sdk[fastapi]` bundled, not initialised. | ✅ S89.1 — `_init_sentry()` in `app/main.py`, gated by `SENTRY_DSN`. |
| CI flag | `.github/workflows/ci.yml:198` `continue-on-error: true` on browser-smoke. | Open — needs 3 green local smoke runs first (S89.1 P7 recipe in progress.md). |
| Docs | `docs/scholarai/IMPLEMENTATION_STATUS_REPORT.md` predates Pakistan pivot + Q1 + Air-Uni + S89. | Open — refresh to reflect `alembic head 20260516_0026`. |
| Prod seed | Supabase prod not seeded with `AIRU2026` invite. | Open — `python scripts/seed_invite_codes.py` before booth. |
| Demo persona | `zara.khan@example.com` only on local. | Open decision. |
| Trial tests | `test_trial_tasks.py` unit only; no end-to-end. | Open — add `tests/integration/test_trial_lifecycle.py`. |
| Burn-cap reset | `usage_ledger` grows unbounded. | Open — Celery beat `tasks.run_usage_ledger_prune` first of month, purge rows older than 13 months. |

Soft / deferred: `broker_connection_retry_on_startup` celery deprecation warning; `pytest.mark.asyncio` mis-mark on `test_document_service.py:286`.

Sticky knowns (do not re-investigate):
- `users.id` is `UUID(as_uuid=True)` — every new model + migration must use `postgresql.UUID(as_uuid=True)` for FK columns.
- `Scholarship` ORM uses `title` + `provider_name` (NOT `name` / `provider`) — backfills/regex must match.
- Mailgun send returns `True` on log-only fallback so callers stay deterministic offline.
