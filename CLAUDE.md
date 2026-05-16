# CLAUDE.md

Guidance for Claude Code in this repo.

## Repo
ScholarAI — AI scholarship platform. **Pakistan-pivot in progress (PRD `D:/Downloads/SCHOLARAI_PAKISTAN_PRD.md`)** targeting Pakistani students applying to UK / US / CA / DE / AU. Backend Features 1–10 complete (290 tests pass). Frontend Pass pending. Display brand: **AidwiseAI**. Repo / backend / internal docs: ScholarAI.

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

## Front-upgrade planning docs (2026-05-15)
- `Front-upgrade.md` (fresh AidwiseAI design spec, 15 sections) + `Front-upgrade.html` (9-sprint delta plan, ~21 dev-days) at repo root. Reconciled against live `frontend/src` — supersede `DESIGN_SPEC.md` / `FRONTEND_ENHANCEMENT_PLAN.html`. Key finding: Pakistan API layer + `UpgradeWall` already built; gap is the student-facing pages. `globals.css` lacks `--color-gold` token — add in S3.
- **Brand rename 2026-05-15:** GrantPath → **AidwiseAI** in `Front-upgrade.md`, `Front-upgrade.html`, root `CLAUDE.md`, `frontend/CLAUDE.md`. Codebase still hardcodes "GrantPath" in `app/page.tsx` + `Sidebar.tsx`; rename happens in S1 + S3 sprints. Lowercase `grantpath.*` localStorage keys (`grantpath.access_token` / `grantpath.refresh_token` / `grantpath.access_expires_at` / `grantpath.onboarding_draft`) **kept** — they are code identifiers in `client.ts`, renaming them logs every user out. `frontend/CLAUDE.md:11` historical "GrantPath AI metadata" line left intact (factual record of the wiped old frontend). Brand-derived mailto updated: `partnerships@aidwiseai.pk`.

## Open work
- ~~Frontend Pass~~ **landed 2026-05-15** on branch `feat/pakistan-frontend-pass`. Remaining: re-point Playwright smoke selectors to new routes and remove `continue-on-error` on the browser-smoke job; consent UI + cookie banner + settings privacy.
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
- **Session S86 — Scraper Ingestion Completion (Pakistan-first)** (2026-05-15, branch `feat/scraper-ingestion-completion` off `feat/phase-c-and-scraper-wip`, migration `20260514_0021_source_health.py`): closes the 11 doc-cited ingestion gaps.
  - **Pakistan-first parser geo flip** — `_infer_country_code` is destination-aware (`PK` default, plus `GB`/`US`/`DE`/`AU`/`CA` from URL/source hints); `FIELD_KEYWORD_MAP` extended to engineering / business / medicine / law / social sciences / CS / agriculture / education; `_is_fulbright_source` generalised to `_is_known_program_source` (Fulbright / Chevening / DAAD / Commonwealth / HEC); `scope_policy` metadata flipped to `pakistan_first_destination_aware`.
  - **Richer parser extraction** — new microdata pass (`_candidates_from_microdata` with itemscope/itemprop), structured deadline (`_extract_structured_deadline` reading JSON-LD `applicationDeadline` + free-text date cues), structured funding amount/currency (`_extract_funding_structured` → `provenance_payload["funding_structured"]` covering PKR/GBP/EUR/AUD/USD).
  - **Fuzzy dedup** — `_normalize_title` + `_select_fuzzy_match` (`difflib.SequenceMatcher ≥ 0.9`) + `_find_fuzzy_duplicate` route near-identical titles under the same provider to advisories with `review_recommended: true` (not hard-skipped).
  - **Snapshot drift detection** — `_snapshot_signature` (whitespace-normalized sha256) + `_load_prior_snapshot_html` + `_detect_snapshot_drift` flag published records via `provenance_payload.{needs_revalidation, drift_flagged_at, drift_run_id}` and merge a `drift` block into `run_metadata`.
  - **Pagination expansion** — `_capture_source_with_pagination` now follows `rel=next` / "Next" then "Load More" (`data-url`/`href`) then numbered (`?page=N` / `/page/N`).
  - **Diagnostics + provenance APIs** — `GET /api/v1/curation/ingestion-runs?parser_diagnostic=fallback_used` (or `microdata_candidates`, etc.) filters by `run_metadata.parser.<key>` truthiness; new `GET /api/v1/scholarships/{scholarship_id}/provenance` returns `ScholarshipProvenanceResponse` (source key / display / url / content_hash / provenance_payload / originating_run_id / capture_mode), published-only — non-published yields 404.
  - **Data-quality regression suite** — `tests/integration/test_data_quality_regression.py` pins: `CurationRawImportRequest` carries no `record_state`/`published*` fields, `ParsedScholarshipCandidate` likewise, `Scholarship.record_state` column default is RAW, public list + detail routes constrain on `record_state == RecordState.PUBLISHED`, and provenance columns exist.
  - **Async orchestration** — `IngestionService._resolve_execution_mode` makes `execution_mode="auto"` threshold-driven (`AUTO_WORKER_RECORD_THRESHOLD=10`): small jobs run inline, larger jobs dispatch to Celery; explicit `"inline"`/`"worker"` pass through.
  - **Nightly catch-up** — `scraper_tasks._nightly_run_is_stale` + `_load_last_nightly_completion` + `_should_run_nightly`; `run_nightly_ingestion` now skips when a successful nightly within `NIGHTLY_MAX_AGE_HOURS=25` exists, so an hourly catch-up beat won't double-run.
  - **Source-health monitoring** — migration `20260514_0021` adds `source_registry.last_success_at`, `last_failure_at`, `consecutive_failures`, `health_status` (default `unknown`). `IngestionService._record_source_health(source, success)` updates after every capture; `_classify_source_health` thresholds: 0–2 healthy, 3–5 degraded, ≥6 down (with a `logger.warning` on first transition to `down`). `GET /api/v1/curation/source-health` returns `SourceHealthListResponse` (institution-scoped like `list_runs`).
  - Test suite: **369 passed, 0 failed, 8 pre-existing warnings** on full unit+integration run. Tests added: 4 (Phase 1) + 3 (Phase 2) + 7 (Phase 3) + 4 (Phase 4 unit) + 5 (Phase 4 regression) + 5 (Phase 5 ingestion) + 3 (Phase 5 nightly).
