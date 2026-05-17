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
- **v4 spec authored 2026-05-17** (`Front-upgrade.md`, 2646 lines, 11 sections / 36 screen specs). Premium Cultural: ivory `#FBF7EE` + ink-deep `#0E1A1F` + lapis `#1B3A6B` + gold-leaf `#B08A3E` + sindoor `#B94A48`; Fraunces italic display + Inter body + JetBrains Mono data. Every screen: states + backend contract + anti-slop ban list + verbatim copy + a11y + telemetry. Banned-phrase grep in §7.5. Prior v3 at `Front-upgrade.legacy.md`.
- **S88 Premium Cultural rebuild landed 2026-05-17** — foundations + 9 routes + cookie banner + visual audit. See `frontend/CLAUDE.md` "S88" section. Lint + typecheck + build all clean. 21/24 audit routes 200 (only `/legal/privacy` missing — future task). Playwright audit runner at `frontend/scripts/visual-audit.mjs`; screenshots at `frontend/audit-out/`.
- **Brand rename 2026-05-15:** GrantPath → **AidwiseAI**. `grantpath.*` localStorage keys kept (renaming logs users out).

## Open work
- ~~Frontend Pass~~ **landed 2026-05-15** on branch `feat/pakistan-frontend-pass`. Remaining: re-point Playwright smoke selectors to new routes and remove `continue-on-error: true` from the `browser-smoke` step in `.github/workflows/ci.yml`; consent UI + cookie banner + settings privacy.
- ~~Apply migrations 0014–0018 against live dev DB and run seed orchestrator before manual smoke.~~ **Done 2026-05-12**: alembic at head `20260511_0018`; `demo_seed_pakistan.py` ran (20 PK scholarships, 30 universities, 70 visa Q, 5 legal docs, demo `zara.khan@example.com`). Q1 retier (2026-05-16) advanced head to `20260516_0025`.
- Update `docs/scholarai/IMPLEMENTATION_STATUS_REPORT.md`, `frontend/README.md`, `.codex/AGENTS.md` to reflect Pakistan pivot.

## Q1 retier (2026-05-16, branch `feat/pakistan-frontend-pass`)
Closed Tasks 1–17 across 21 commits `23942f5..d20ab14`. **444 backend tests pass + 1 xpass**, frontend lint/tsc/build green, docs governance 0 failures, vocab guard **6 pass + 1 xpass**. Push-gate closeout commit: `d20ab14`. Live DB at `alembic head = 20260516_0025`; `scholarships` row mix = 6 premium / 20 standard.
- **New tables:** `sop_monthly_usage` (per-plan SOP quota + lifetime counter, migration `20260516_0024`), `usage_ledger` (burn-cap accounting rows for LLM + WhatsApp cost, migration `20260516_0025`).
- **New column:** `scholarships.tier` (`standard` | `premium`, migration `20260516_0023` with premium backfill on title/provider keywords; downgrade idempotent).
- **New module:** `backend/app/core/burn_cap.py` — 60% per-tier monthly budget accounting, `assert_within_burn_cap` (HTTP 429 on breach), `record_llm` / `record_whatsapp` ledger writers, deterministic-template path emits zero-cost rows.
- **New test file:** `backend/tests/unit/test_user_facing_vocab.py` — vocab-guard CI test (6 pass + 1 xpass) preventing internal classification tokens (`eligible`, `partially_eligible`, `stretch`, `locked`, `tier`) from leaking into pricing bullets, serialised match responses, or frontend user-visible strings.
- **Pro / Elite pricing:** PKR **2,999 / 6,000** monthly (Q1 retier neutral bullets in `backend/app/api/v1/routes/waitlist.py`).
- **Caps free / pro / elite** for `matches` + `tracker` = **3 / 6 / 12** (`backend/app/core/plan_guard.py`, applied in `services/scholarships/match_service.py` + `services/tracker/service.py`).
- **SOP quotas free / pro / elite** = **1 lifetime / 5 monthly / 10 monthly** (`services/documents/sop_builder.py`).
- **Premium scholarship paywall** on public catalog (`api/v1/routes/scholarships.py`): list filter for `tier=standard` when caller is anonymous or non-premium; detail/provenance route premium rows through `_guard_premium_tier` → 402 for anon/free, 200 for pro/elite/institution; new `get_optional_user` dep wraps `get_current_user`.
- **WhatsApp-only Elite alerts** — SMS channel removed from `services/notifications/channels.py`; `fan_out_for_plan(db, user, message)` is async; `tasks/alert_tasks.py` + `tasks/reminder_tasks.py` migrated.
- **Burn-cap-aware LLM wrapper** — `AnthropicClient.complete_with_accounting` pre-flights cap then records real usage tokens; offline path writes synthetic ledger row. Callers migrated: `sop_builder.draft`, `visa_interview/evaluator.evaluate_answer` (now async), `professor_email`, `strategy_report` (the latter switched from public `match()` to `ScholarshipMatchService.match_internal()` to keep buckets).
- **Frontend (Task 15 + 17)** — neutral match shape in `lib/api/types.ts` (`MatchResponse { items, unlock_offer }`), new `CompatibilityMeter.tsx`, new `(student)/scholarships/page.tsx` (MatchCard + UnlockBlock + blurred locked placeholders + "Unlock with Elite" CTA), `EligibilityMatrix.tsx` aria-labels neutralised, `upgrade/page.tsx` `tier`→`plan` rename + Q1 comparison rows.

## Air University exhibition trial launch (2026-05-16, branch `feat/pakistan-frontend-pass`)
Backend bundle for the May-19 booth launch — Pro plan via shared invite code `AIRU2026`, 100 redemptions, 30 days per user from redemption. Push gate: **454 passed + 1 xpassed**. Frontend bundle queued in `Front-upgrade.md` §16.
- **Migration `20260516_0026`** adds `invite_codes` table (code PK, cohort, grants_plan, trial_days, max_uses, uses, valid_from/until, is_active) + 4 user cols (`air_uni_uni`, `air_uni_dept`, `air_uni_batch`, `redeemed_invite_code` indexed). Reuses existing `User.marketing_consent` rather than duplicating.
- **`AuthService._redeem_invite_code`** (in `services/auth/service.py`) — row-locked invite redemption raises 400 on unknown/inactive/out-of-window/exhausted; on success sets `user.plan = invite.grants_plan` + `plan_expires_at = now + trial_days` + `redeemed_invite_code`. `UserCreate` / `UserResponse` extended.
- **`app/tasks/trial_tasks.py`** — `expire_trial_plans` async + `run_expire_trial_plans` Celery task scheduled daily 02:00 UTC. Idempotent UPDATE: free + null-expiry where `plan_expires_at < now AND plan != 'free'`.
- **Mailgun email** — `services/notifications/channels.send_email` now POSTs to `${MAILGUN_BASE_URL}/${MAILGUN_DOMAIN}/messages` via httpx. Fail-soft to log-only when MAILGUN_API_KEY / MAILGUN_DOMAIN absent. New settings: `MAILGUN_API_KEY`, `MAILGUN_DOMAIN`, `MAILGUN_BASE_URL`, `MAILGUN_TIMEOUT_SECONDS`, `BRAND_DISPLAY_NAME`, `EMAIL_FROM_LOCALPART`.
- **Dockerfile** bakes Chromium for the scraper Celery worker — `playwright install --with-deps chromium` with `PLAYWRIGHT_BROWSERS_PATH=/opt/playwright-browsers`. Image ≈ 1.2 GB, fits DO App Platform Basic S (1 GB dedicated).
- **CLI scripts** — `scripts/seed_invite_codes.py` (AIRU2026 100 uses, May 19 09:00 → May 26 23:59 PKT), `scripts/grant_invite_uses.py CODE N` (atomic on-spot bump), `scripts/generate_qr_flyers.py` (900×900 PNG of `https://aidwiseai.com/signup?invite=AIRU2026`).
- **New deps** in `requirements.txt`: `anthropic==0.39.0`, `qrcode[pil]==7.4.2`, `sentry-sdk[fastapi]==2.18.0`.
- **New tests** — `tests/unit/test_trial_tasks.py` (4 pass) + 6 invite-redemption cases in `test_auth_service.py`.

## Session S87 — Pakistan Frontend Pass (2026-05-15, branch `feat/pakistan-frontend-pass`)
Closes the full PRD frontend gap + four missing backend items. **369 backend tests pass** (312 unit + 57 integration), frontend lint/typecheck/build green, docs governance 0 failures, KPI regression 17 pass.
- **Backend**: `/auth/me` exposes `plan` + `plan_currency` + `billing_country` (`schemas/auth.py`); `services/documents/professor_email.py` + `services/reports/strategy_report.py` (Elite-gated 402 via `assert_plan_or_raise`, deterministic-template fallback, persist as `DocumentRecord` with new `DocumentType.PROFESSOR_EMAIL` / `STRATEGY_REPORT`); `services/notifications/channels.py` (log-only `send_email` / `send_sms` / `send_whatsapp` + `fan_out_for_plan` channel matrix); `tasks/alert_tasks.py` (`tasks.run_priority_scholarship_alerts`, daily 06:07) + `tasks/reminder_tasks.py` (`tasks.run_deadline_reminders`, 30-day silent stop for free, daily 06:30); migration `20260515_0022_document_type_pakistan_elite.py` adds the two enum values; new routes `POST /api/v1/documents/professor-email` + `POST /api/v1/reports/strategy`; 28 new unit tests (`test_professor_email`, `test_strategy_report`, `test_alert_tasks`, `test_reminder_tasks`). Trust boundary holds — `services/reports/` sources only from profile + tracker + match service.
- **Frontend**: `lib/api/client.ts` exports `isPlanRequiredError` + `PlanRequiredDetail`; 6 new endpoint modules (`tracker`, `scholarshipMatch`, `sopBuilder`, `visaInterview`, `upgrade`, `reports`); `components/UpgradeWall/index.tsx` (consumes 402 `detail` verbatim, renders feature blurred behind, optional `partial_summary`); `app/upgrade/page.tsx` (4-tier cards from `/upgrade/pricing` + 5-currency switcher + comparison table + waitlist form + mailto for institution); `app/(student)/tracker/page.tsx` (6-column native-DnD Kanban using real `TrackerStage` enum, per-card 14-key checklist incl. `hec_attestation`, deadline urgency banner, free 402 → `UpgradeWall`); `app/(student)/documents/sop/page.tsx` (two-panel SOP builder, Elite line feedback panel); `app/(student)/documents/professor-email/page.tsx`; `app/(student)/interviews/visa/page.tsx` (country setup + Q&A loop + study-mode rubric meters + summary with `RubricRadar` normalised 0–10→0–5); `app/page.tsx` rewritten to AidwiseAI Pakistan landing; `app/universities/page.tsx` (public B2B); `(partners)/layout.tsx` + `partners/page.tsx` + `partners/universities/page.tsx` with new `PARTNER_ROLES` (university/admin/owner) in `RoleGuard.ROLE_GROUPS`; sidebar gains Tracker + Visa-practice links. `User` type extended with `plan` / `plan_currency` / `billing_country` and exported `Plan` / `Currency`.
- **Trust boundary verified**: student `ROLE_GROUPS.student` excludes `university`; `partner` group excludes every student role; no student-side nav links into `/universities` or `(partners)`.

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
- **Session S86 — Scraper Ingestion Completion** (2026-05-15, migration `20260514_0021_source_health.py`): destination-aware geo inference (PK default + GB/US/DE/AU/CA hints), JSON-LD + microdata extraction, structured deadline/funding parsing, fuzzy-dedup at `SequenceMatcher ≥ 0.9` → advisory `review_recommended: true`, snapshot drift sha256 (`provenance_payload.needs_revalidation`), rel=next + Load-More + numbered pagination, parser-diagnostic + provenance APIs (`GET /scholarships/{id}/provenance`), async orchestration threshold `AUTO_WORKER_RECORD_THRESHOLD=10`, nightly catch-up `NIGHTLY_MAX_AGE_HOURS=25`, source-health table (`healthy/degraded/down` at 0-2/3-5/≥6 consecutive failures). Tests: 369 passed at landing.

## PR #87 merge + Q1 retier live (2026-05-17)
PR https://github.com/HaiderNaqvi-5/scholarai-platform/pull/87 all-green after 4 root-cause fixes on `feat/pakistan-frontend-pass`. Alembic head: `20260516_0026 (head)`. Latest checks: backend-sanity / kpi-regression-gate / frontend-sanity / docs-governance / browser-smoke / **Vercel** all SUCCESS. mergeStateStatus=`CLEAN`.
- **Merge of origin/main** (`d4a063d`) — resolved CLAUDE.md + progress.md conflicts. Initial Vercel deploy failed at 16s because Q1 frontend imported `@/lib/brand` / `@/lib/countries` / `@/lib/tracker/*` / `endpoints.scholarshipMatch` / `endpoints.upgrade` that were never committed (Next.js fast-fails on resolve).
- **S87 WIP cluster landed** (`f5a8391`, 58 files) — UpgradeWall, full `(student)` page set (tracker / sop / professor-email / visa), `(partners)`, `/universities`, kanban, endpoint modules, `lib/brand`, `lib/countries`, `lib/tracker/*`, sidebar partner roles, `RubricRadar` 0-10→0-5, landing rewrite. Backend: provenance schema, `/auth/me` plan fields, professor-email + strategy-report services + routes + tests, ingestion S86 hardening, migration `20260515_0022_document_type_pakistan_elite.py` (chains 0023).
- **Invite-codes cluster** (`ee94799`) — `class InviteCode(Base)` in models.py was missing despite `__init__.py` re-export → CI `ImportError`. Landed model + migration `20260516_0026_invite_codes_and_trial.py` + `tasks/trial_tasks.py` + scripts (`seed_invite_codes` / `grant_invite_uses` / `generate_qr_flyers`).
- **Schema fix** (`8140338`) — merge with main reverted Task 7 `scholarships_match.py` to legacy bucketed shape → conftest `ImportError: cannot import name 'MatchResponse'`. Re-applied neutral `MatchResponse` / `UnlockOffer` / `ScholarshipMatchOut`.
- **Vercel trigger** (`24ba352`) — empty commit cleared a stuck 35-min PENDING build (rapid-push queue congestion). Deployment succeeded on the same tree.

## Backend gap audit (2026-05-17, post-PR-#87)
Frontend out of scope. Open items strictly on backend / ops:

| Area | Gap | Action |
|------|-----|--------|
| Env docs | `backend/.env.example` lacks `MAILGUN_API_KEY` / `MAILGUN_DOMAIN` / `MAILGUN_BASE_URL` / `MAILGUN_TIMEOUT_SECONDS` / `BRAND_DISPLAY_NAME` / `EMAIL_FROM_LOCALPART` (all live in `config.py:94-99`). Setup will fail-soft to log-only but operators have no signpost. | Append keys to `.env.example` + `docs/deployment.md`. |
| Observability | `sentry-sdk[fastapi]==2.18.0` in `requirements.txt` but zero `sentry_sdk` references in `backend/app/`. Bundled, not initialised. | Wire `sentry_sdk.init(...)` in `app/main.py` `create_app()` gated by `SENTRY_DSN`; add the env key. |
| CI flag | `.github/workflows/ci.yml:198` carries `continue-on-error: true` on browser-smoke (TODO marker at `:192`). Green smoke ≠ smoke passed. | Remove flag once Playwright selectors re-pointed to S87 routes. Per CLAUDE.md "Open work". |
| Docs | `docs/scholarai/IMPLEMENTATION_STATUS_REPORT.md` predates Pakistan pivot + Q1 retier + Air-Uni trial. | Refresh to reflect alembic head `20260516_0026` + new endpoints + Q1 caps + invite-code cohort flow. |
| Prod seed | Supabase production not yet seeded with `AIRU2026` invite (`scripts/seed_invite_codes.py` is idempotent, awaits run). | `DATABASE_URL=...supabase... python scripts/seed_invite_codes.py` before May-19 booth. |
| Demo persona | `zara.khan@example.com` exists on local dev DB via `demo_seed_pakistan.py`; not seeded on production. | Decide whether prod gets a demo persona or not (privacy + tier consequences). |
| Trial tests | `test_trial_tasks.py` covers `expire_trial_plans` unit-level; no integration test for end-to-end signup → invite-redeem → plan flip → expire after 30 days. | Add integration test in `tests/integration/test_trial_lifecycle.py`. |
| Burn-cap reset | Monthly counters in `usage_ledger` partitioned by `period_yyyymm` but no rollup or pruning task. Table grows unbounded. | Add Celery beat `tasks.run_usage_ledger_prune` on first of month — purge rows older than 13 months. |

Hard items above. Soft / deferred:
- Consent UI + cookie banner + settings privacy panel (backend routes shipped; frontend pending in S88).
- `broker_connection_retry_on_startup` celery deprecation in `app/tasks/celery_app.py` (warning, not failure).
- `pytest.mark.asyncio` mis-mark on `test_document_service.py:286` (sync test wrapped as async).

Sticky knowns (do not re-investigate):
- `users.id` is `UUID(as_uuid=True)` — every new model + migration must use `postgresql.UUID(as_uuid=True)` for FK columns.
- `Scholarship` ORM uses `title` + `provider_name` (NOT `name` / `provider`) — backfills/regex must match.
- Mailgun send returns `True` on log-only fallback so callers stay deterministic offline.
