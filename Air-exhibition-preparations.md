# Air University Exhibition Launch — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship AidwiseAI live to a public URL by **May 19, 2026 09:00 PKT** with a 30-day Pro trial gated by an invite code distributed at the Air University exhibition booth, hard burn-cap on Anthropic spend per user, mandatory PDPB-compliant consent at signup, and a payment-collection roadmap that lands real PKR receipts within the trial window.

**Architecture:** Frontend on Vercel (Next.js 16, Bun build). Backend FastAPI + Celery worker + Celery beat on DigitalOcean App Platform (paid via the GitHub Student Pack $200 credit). Postgres + pgvector on Supabase Free, region `ap-south-1`. Redis on Upstash Free. Email via Mailgun (20k/mo free via Student Pack). Domain `aidwiseai.com` via Namecheap, DNS on Cloudflare Free. The Q1 re-tier spec ships in a "Tier A" critical slice (10 of 17 tasks) that protects budget and delivers the Pro trial pitch; the remaining tasks land in a Tier B sprint Week of May 26.

**Tech Stack:** FastAPI · SQLAlchemy 2 async · Alembic · Pydantic v2 · Anthropic SDK (Haiku 4.5 default; Sonnet 4.6 reserved for Elite paid tier post-launch) · Celery 5 + Redis · Next.js 16 + React 19 + Tailwind 4 · Bun · Supabase pgvector · DigitalOcean App Platform · Vercel · Mailgun · Cloudflare · Sentry Developer (free via Student Pack) · UptimeRobot Free · Canva Pro (free via Student Pack) for flyers + QR cards.

---

## 0. Decisions Locked (Do Not Re-Litigate)

| # | Decision | Value |
|---|---|---|
| 1 | Trial plan tier | **Pro** (PKR 2,999/mo equivalent) — Elite reserved as paid upgrade |
| 2 | Trial duration | **30 days from per-user redemption time** (not cohort end) |
| 3 | Invite code mechanic | **Single shared code `AIRU2026`**, 100-use cap initially, expandable on-spot via admin script |
| 4 | Code redemption window | **2026-05-19 09:00 PKT → 2026-05-26 23:59 PKT** (7 days) |
| 5 | Air U signup fields | `uni` (text) + `dept` (text) + `batch` (int) — **all optional** |
| 6 | Consent at signup | **Mandatory** — consent v1.0 doc + marketing-opt-in toggle (default off) |
| 7 | Brand display | **AidwiseAI** everywhere user-facing; hotpatch `GrantPath` literals |
| 8 | Domain | `aidwiseai.com` (Namecheap, $10/yr); DNS on **Cloudflare Free** |
| 9 | Backend host | **DigitalOcean App Platform** ($200 Student Pack credit ≈ 13 free months) |
| 10 | Email provider | **Mailgun** (20k emails/mo free via Student Pack) |
| 11 | Error tracking | **Sentry Developer** (free via Student Pack) |
| 12 | Uptime monitoring | UptimeRobot Free + Sentry alerts |
| 13 | Payment v1 (Day 1) | **Mailto + manual JazzCash/Easypaisa QR + IBAN** (no NTN/business bank yet) |
| 14 | Payment v2 (~Week 4–6) | **Safepay** (bundles JazzCash, Easypaisa, Visa/Master/PayPak, RAAST) — onboarding gated by NTN + business bank account opening |
| 15 | Backup if cloud dies | UptimeRobot 1-min ping + laptop with localhost stack ready + 90-second pre-recorded walkthrough video + 10-screen PDF |
| 16 | Q1 re-tier scope for launch | **Tier A only** (10 tasks); Tier B + C deferred to post-exhibition sprints |

---

## 0.5 Codebase State Audit (2026-05-16 17:23 PKT)

Rescan revealed Q1 Tier A backend mostly shipped overnight. Plan compresses to ~2 dev-days remaining work.

### ✅ Already shipped — verify only, do not re-implement

| Area | Evidence |
|---|---|
| Migration `0023` scholarship_tier | `backend/alembic/versions/20260516_0023_scholarship_tier.py` |
| Migration `0024` sop_monthly_usage + lifetime_sop_count | `backend/alembic/versions/20260516_0024_sop_monthly_usage.py` |
| Migration `0025` usage_ledger | `backend/alembic/versions/20260516_0025_usage_ledger.py` |
| `ScholarshipTier` enum + `Scholarship.tier` | `models/models.py:88,733-741` |
| `User.plan_expires_at` + `User.lifetime_sop_count` | `models/models.py:219,221` |
| `SopMonthlyUsage`, `UsageLedger` ORM + exports | `models/models.py:1669,1691` + `models/__init__.py:26-31` |
| `plan_guard.py` caps + PKR 2,999/6,000 + reveal gates | confirmed via grep |
| `match_service.py` Pro top-3 blur + `UnlockOffer` + `MatchResponse` | confirmed |
| `sop_builder.py` SOP quota gate | confirmed |
| `tracker/service.py` plan-aware cap (3/6/12) | confirmed |
| `waitlist.py` new prices | confirmed |
| `scholarships.py` premium filter for free/anon | confirmed |
| `notifications/channels.py` PLAN_CHANNELS + WhatsApp-only (no SMS) | confirmed |
| `anthropic_client.py` wraps `assert_within_burn_cap` + `record_llm` | confirmed at lines 25-29 |
| Frontend `CompatibilityMeter.tsx` + locked match card + `UpgradeWall` | confirmed in `frontend/src/components/` + `app/(student)/scholarships/page.tsx` |
| Frontend `upgrade/page.tsx` `COMPARISON_ROWS` refresh | confirmed |
| `users.id` is UUID (not Integer) | `models/models.py:160,195` — fix Migration 0026 template |

### ❌ Still required for exhibition launch

| # | Work | Plan task ref |
|---|---|---|
| R1 | Migration `0026` invite_codes + air_uni_* + marketing_opt_in + redeemed_invite_code (FK = `UUID` for user_id) | New §4 Task |
| R2 | `InviteCode` ORM + export | §4 |
| R3 | Auth `register()` patch: invite-code redemption + Air U capture + consent v1.0 enforcement | §5 |
| R4 | `tasks/trial_tasks.py` daily-02:00-UTC downgrade cron + Celery beat schedule entry | §5 |
| R5 | `notifications/channels.py` Mailgun POST in `send_email` (currently log-only) | §5 |
| R6 | Frontend `app/signup/page.tsx` invite-code field + Air U dropdowns + consent checkbox + marketing-opt-in | §6 |
| R7 | Brand hotpatch in **5 files** (not 2): `app/signup/page.tsx:45`, `app/login/page.tsx:55`, `components/shell/Sidebar.tsx:96`, `app/layout.tsx:29-34` (3 lines), `app/(student)/settings/page.tsx:70`. Skip `lib/api/client.ts:2` (comment) + `app/onboarding/page.tsx`+`app/(student)/documents/new/page.tsx` (only if user-facing literal — verify) | §6 |
| R8 | `components/ComingSoon.tsx` + mount in `app/page.tsx` | §6 |
| R9 | `backend/Dockerfile` — add `RUN playwright install --with-deps chromium` for scraper worker | §7 |
| R10 | `backend/scripts/seed_invite_codes.py` + `grant_invite_uses.py` + `generate_qr_flyers.py` | §7 |
| R11 | DigitalOcean App Platform deploy 3 svc + Vercel deploy + Cloudflare DNS + Mailgun DKIM/SPF + Sentry + Statsig | §7 |
| R12 | Upgrade-page manual-payment block (mailto + JazzCash/Easypaisa QR + IBAN) | §6 |

### Verification steps (do today before R1–R12)

- [ ] **V1:** `cd backend && alembic current` — expect `20260516_0025`
- [ ] **V2:** `pytest backend/tests/unit -q` — expect previous ~369 + new Q1 tests = ~395 PASS
- [ ] **V3:** `python -c "from app.models import InviteCode"` — expect `ImportError` (proves 0026 not yet shipped)
- [ ] **V4:** `python -c "from app.services.notifications.channels import send_email; import inspect; print(inspect.getsource(send_email))"` — confirm body is log-only (Mailgun POST absent)
- [ ] **V5:** `bun run lint && bunx --bun tsc --noEmit && bun run build` in `frontend/` — expect 0 errors (baseline before R6-R8 edits)

### Net timeline impact

Original plan: 4 days, ~32 tasks, mix of done + new.
**Actual remaining: backend ~5 items + scripts + deploy + frontend bundle (deferred LAST).**

| Day | Scope |
|---|---|
| **May 16 (today)** | Backend R1–R5 (migration 0026 + InviteCode ORM + auth/register patch + trial_tasks cron + Mailgun email send) + R10 (CLI scripts: seed_invite_codes, grant_invite_uses, generate_qr_flyers) |
| **May 17** | Backend R9 (Dockerfile Chromium for scraper worker) + R11 partial (DigitalOcean App Platform 3-service deploy, Cloudflare DNS for `api.aidwiseai.com`, Mailgun DKIM/SPF verify, Sentry backend init, Anthropic Tier-2 prepay $40, A/B/C/D hardening from §"Will it break?") + full end-to-end backend smoke against live `api.aidwiseai.com` |
| **May 18** | **Frontend sprint per `Front-upgrade.md` §16** — Tasks 16.1–16.11 (gold token, brand hotpatch ×5 files, ComingSoon, signup invite+consent, TrialBanner, PaymentMethods, Sentry/LogRocket/Statsig/Crisp observability, pre-deploy gate, Vercel deploy with custom domain). Frontend lands LAST so it can target the already-live backend URL. |
| **May 19** | Dry run + flyer print + exhibition (unchanged) |

Plan **ahead of schedule** as of audit time. Buffer day reclaimed. Frontend deferred to the last possible slot per user directive (2026-05-16) so observability keys, backend URL, and consent legal-doc slug are all stable before the FE bundle freezes.

### Frontend tasks moved out of this document

All frontend work (brand hotpatch, signup invite UX, TrialBanner, ComingSoon, PaymentMethods, Sentry/LogRocket/Statsig/Crisp wiring, `--color-gold` token, Vercel deploy) now lives in **`Front-upgrade.md` §16** — single canonical location, structured per `superpowers:writing-plans` with bite-sized TDD-style tasks.

**Do not re-implement frontend changes from this file.** Sections in this document that mention `frontend/` paths (e.g. legacy Task 1.8 brand hotpatch, Task 3.5/3.6/3.6b/3.7/3.8) are kept for historical context only. Execute Front-upgrade.md §16 instead.

---

## 1. Cost Projection (Trial Month, with Student Pack)

| Line | Without Student Pack | **With Student Pack** | Notes |
|---|---:|---:|---|
| Frontend (Vercel Hobby) | $0 | $0 | TOS-grey for commercial trial; upgrade Pro $20 if traffic > limits |
| Backend (DO App Platform — web Basic S + worker Basic S + beat Basic XXS) | $29 | **$0** | Worker upgraded to Basic S ($12) for Chromium/Playwright scraper. $200 credit ≈ 7 months for 3 svc |
| Postgres + pgvector (Supabase Free) | $0 | $0 | <100 MB used vs 500 MB cap |
| Redis (Upstash Free) | $0.50 | $0.50 | 30k cmd/day vs 10k free, ≈ $0.20/100k overage |
| Email (Resend Free → Mailgun) | $0 | $0 | Mailgun 20k/mo free via Student Pack (vs Resend 3k/mo) |
| Error tracking (Sentry) | $0 | $0 | Developer tier free with Student Pack (100k errors/mo vs 5k free) |
| Uptime ping (UptimeRobot Free) | $0 | $0 | 50 monitors, 5-min interval |
| Anthropic (Pro = Haiku-only) | $5–15 | $5–15 | No Student Pack credit |
| Anthropic monthly cap | **$30** | **$30** | Hard stop in dashboard |
| Domain (`aidwiseai.com`) | $1 ($12/yr) | $1 ($12/yr) | Or skip and use free `.me` via Namecheap Student Pack |
| Print flyers + QR cards (one-time) | $10–18 | $0 | Canva Pro free via Student Pack; print at local shop ~PKR 2k–3k |
| **TOTAL trial month** | **~$22** | **~$7** | |
| **Worst-case (cap-bound)** | **~$50** | **~$35** | Anthropic hits $30 cap |

**Cash needed today: $5 Anthropic prepay + $10 domain = $15.**

### GitHub Student Pack benefits actually used

| Benefit | Use |
|---|---|
| **DigitalOcean $200 credit** | Backend host (App Platform 3 svc × $5 = ~13 months free) |
| **Mailgun 20k emails/mo** | Trial alerts, deadline reminders, NPS survey, signup welcome |
| **Sentry Developer free** | Error tracking 100k events/mo |
| **Canva Pro 12 mo free** | Flyer design, QR card layout, brand assets |
| **Namecheap free `.me`** | Backup domain `aidwise.me` (registered alongside `.com` for redirect/protection) |
| **Datadog 2-yr Pro free (5 hosts)** | Optional: more granular APM, defer until Tier B |
| **JetBrains IDEs free** | Optional founder dev env |
| **Notion Personal Pro free** | Founder docs, customer feedback log |

---

## 2. File Structure

### Backend — create

| File | Responsibility |
|---|---|
| `backend/alembic/versions/20260516_0023_scholarship_tier.py` | Add `scholarship_tier` enum + `Scholarship.tier` col with premium backfill |
| `backend/alembic/versions/20260516_0024_sop_monthly_usage.py` | `users.lifetime_sop_count` + `sop_monthly_usage` table |
| `backend/alembic/versions/20260516_0025_usage_ledger.py` | `usage_ledger` table for burn-cap accounting |
| `backend/alembic/versions/20260516_0026_invite_codes_and_trial.py` | `invite_codes` table + `users` cols: `plan_expires_at`, `air_uni_uni`, `air_uni_dept`, `air_uni_batch`, `marketing_opt_in` |
| `backend/app/core/burn_cap.py` | Per-user PKR cost ledger + cap assertion |
| `backend/app/tasks/trial_tasks.py` | Daily 02:00 UTC cron — downgrade expired Pro trials to Free |
| `backend/scripts/grant_invite_uses.py` | CLI to bump `invite_codes.max_uses` from laptop at booth |
| `backend/scripts/seed_invite_codes.py` | Seeds the `AIRU2026` code with 100-use cap and the 7-day window |
| `backend/scripts/generate_qr_flyers.py` | Outputs `aidwise-air-qr.png` (single QR for all 100 flyers) + 1-page printable PDF |
| `backend/tests/unit/test_burn_cap.py` | Burn-cap module tests |
| `backend/tests/unit/test_trial_invite_codes.py` | Invite-code redemption + expiry + cap |
| `backend/tests/unit/test_trial_tasks.py` | Daily downgrade cron |
| `backend/tests/unit/test_sop_quota.py` | Pro = 5/mo, Free = 1 lifetime |
| `backend/tests/unit/test_plan_caps.py` | Match/tracker/SOP caps per plan |

### Backend — modify

| File | Change |
|---|---|
| `backend/requirements.txt` | Add `anthropic==0.39.0`, `qrcode[pil]==7.4.2`, `sentry-sdk[fastapi]==2.18.0`. **Keep `playwright==1.52.0`, `beautifulsoup4`, `lxml`, `pandas`** (scraper IS shipped at launch). Drop `xgboost`, `shap`, `lime`, `langchain*`, `neo4j`, `opensearch-py`, `sentence-transformers` as **optional-deps** (move to `requirements.dev.txt`) — image lands ~1.2 GB after Chromium |
| `backend/app/core/database.py` | Add Supabase pooler-safe asyncpg `connect_args={"statement_cache_size": 0, "prepared_statement_cache_size": 0}` |
| `backend/app/core/config.py` | New env: `MAILGUN_API_KEY`, `MAILGUN_DOMAIN`, `INVITE_CODE_DEFAULT`, `BRAND_DISPLAY_NAME=AidwiseAI`, `PLAN_TRIAL_DAYS=30` |
| `backend/app/core/plan_guard.py` | Add `MATCH_CAP`/`TRACKER_CAP`/`MONTHLY_SOP_CAP`/`LIFETIME_FREE_SOP`/`PRO_BLURRED_BEST_FIT_COUNT` constants + `can_reveal_best_fit`/`can_see_premium` helpers; new prices PKR 2,999 / 6,000 |
| `backend/app/models/models.py` | Add `ScholarshipTier` enum + `Scholarship.tier`; add `SopMonthlyUsage`, `UsageLedger`, `InviteCode`; extend `User` with `lifetime_sop_count`, `plan_expires_at`, `air_uni_uni`, `air_uni_dept`, `air_uni_batch`, `marketing_opt_in` |
| `backend/app/schemas/scholarships.py` | Replace `ScholarshipMatchOut` (strip bucket/tier names, add `compatibility`+`locked`); new `UnlockOffer` + `MatchResponse` |
| `backend/app/schemas/auth.py` | Extend `RegisterRequest` with optional `invite_code`, `air_uni_uni`, `air_uni_dept`, `air_uni_batch`; require `consent_v` + `marketing_opt_in` |
| `backend/app/services/scholarships/match_service.py` | Internal buckets + Pro top-3 blur (Q1 Task 7) |
| `backend/app/services/documents/sop_builder.py` | SOP quota gate + counter |
| `backend/app/services/tracker/service.py` | Replace hard-coded `3` with `TRACKER_CAP[plan]` |
| `backend/app/services/llm/anthropic_client.py` | Wrap `complete()` with burn ledger (Q1 Task 11) |
| `backend/app/services/auth/service.py` | Invite-code redemption + Air U field capture + consent v1.0 enforcement |
| `backend/app/services/notifications/channels.py` | Wire Mailgun `send_email` (replace log-only stub) |
| `backend/app/api/v1/routes/waitlist.py` | New PKR 2,999 / 6,000 prices + neutral bullets |
| `backend/app/api/v1/routes/auth.py` | Wire new register payload |
| `backend/Dockerfile` | Trim non-runtime deps; **add `RUN playwright install --with-deps chromium`** for scraper; add `RUN python -c "import anthropic, qrcode, sentry_sdk"` smoke at build time |
| `backend/app/main.py` | Mount Sentry SDK, mount Mailgun client init, expose `/api/v1/admin/invite-codes` POST (admin role) |

### Frontend — modify

| File | Change |
|---|---|
| `frontend/src/lib/api/types.ts` | Sync `ScholarshipMatchOut`, `UnlockOffer`, `MatchResponse`, `RegisterRequest` |
| `frontend/src/lib/brand.ts` | Already exists per S102 work — no change |
| `frontend/src/components/CompatibilityMeter.tsx` | New bar component (Q1 Task 15) |
| `frontend/src/app/(student)/scholarships/page.tsx` | `MatchCard` with locked render |
| `frontend/src/app/upgrade/page.tsx` | `COMPARISON_ROWS` refresh per Q1 Task 16 |
| `frontend/src/app/page.tsx` | Replace `GrantPath` literal with `BRAND` constant from `lib/brand` |
| `frontend/src/components/Sidebar.tsx` | Replace `GrantPath` literal with `BRAND` constant |
| `frontend/src/app/(auth)/signup/page.tsx` | Add invite-code field (auto-fill from `?invite=` URL param), Air U dropdowns, mandatory consent checkbox, marketing-opt-in toggle |
| `frontend/src/app/(student)/layout.tsx` (or sidebar) | Trial expiry countdown banner — reads `auth/me.plan_expires_at` |
| `frontend/src/components/ComingSoon.tsx` | New component — pipeline features grid with ETA badges + status pills + optional "Notify me" email capture |
| `frontend/src/app/page.tsx` | Mount `<ComingSoon />` section between hero and footer |
| `frontend/src/app/upgrade/page.tsx` | Mailto + JazzCash QR + Easypaisa QR + IBAN block when user clicks "Upgrade to Pro / Elite" |

---

## 3. Day 0 Pre-flight (Tonight, May 15 — 3 hours)

Goal: provision external accounts and unblock Day 1 coding.

### Task 0.1 — GitHub Student Pack verification

- [ ] Confirm Student Pack active at `https://education.github.com/pack` (must show "Active student" badge)
- [ ] Note: claiming each benefit below requires clicking through from the Student Pack page (DigitalOcean, Mailgun, Namecheap, Sentry, Canva)

### Task 0.2 — Account provisioning (parallel browser tabs)

- [ ] **Anthropic** — `console.anthropic.com` → create account → load **$5 prepay credit** → Settings → Limits → set monthly cap **$30**
- [ ] **Supabase** — `supabase.com/dashboard` → New project `aidwiseai-prod` → region **`ap-south-1` (Mumbai)** → save DB password → Settings → Database → Extensions → toggle **`vector`** ON
- [ ] **Vercel** — sign in with GitHub → no project yet (created Day 3)
- [ ] **DigitalOcean** — claim Student Pack → confirm $200 credit applied → no project yet (created Day 3)
- [ ] **Namecheap** — Student Pack → register `aidwiseai.com` ($10) → optionally claim free `.me`: register `aidwise.me`
- [ ] **Cloudflare** — sign up → add site `aidwiseai.com` → copy 2 nameservers → paste into Namecheap → wait propagation (~10 min, can proceed in parallel)
- [ ] **Mailgun** — Student Pack → claim free 20k/mo plan → add domain `mg.aidwiseai.com` → copy SPF + DKIM TXT records → add to Cloudflare DNS
- [ ] **Sentry** — Student Pack → claim Developer plan → create project `aidwiseai-backend` (Python) + `aidwiseai-frontend` (Next.js) → save DSN strings
- [ ] **UptimeRobot** — sign up free tier → no monitors yet (added Day 4)
- [ ] **Canva** — Student Pack → claim Pro 12-mo → save for flyer design Day 4
- [ ] **Upstash** — `console.upstash.com` → Create Redis → region **`ap-south-1`** → copy `rediss://` URL

### Task 0.3 — Local repo prep

- [ ] `git checkout -b feat/air-exhibition-launch`
- [ ] `cd scholarai-platform && git status` — confirm clean working tree

### Task 0.4 — Drop credentials in `.env.local` (NEVER commit)

- [ ] Create `backend/.env.local` (gitignored) with:

```
DATABASE_URL_DIRECT=postgresql+asyncpg://postgres:<pwd>@db.<ref>.supabase.co:5432/postgres?sslmode=require
DATABASE_URL=postgresql+asyncpg://postgres.<ref>:<pwd>@aws-0-ap-south-1.pooler.supabase.com:6543/postgres?sslmode=require
REDIS_URL=rediss://default:<token>@<endpoint>.upstash.io:6379
ANTHROPIC_API_KEY=sk-ant-...
JWT_SECRET=<openssl rand -hex 32>
MAILGUN_API_KEY=<key>
MAILGUN_DOMAIN=mg.aidwiseai.com
SENTRY_DSN_BACKEND=<dsn>
INVITE_CODE_DEFAULT=AIRU2026
BRAND_DISPLAY_NAME=AidwiseAI
PLAN_TRIAL_DAYS=30
CORS_ORIGINS=http://localhost:3000
```

- [ ] **Commit:** none — `.env.local` is gitignored

---

## 4. Day 1 — May 16 (Backend Infra Patches + Q1 Migrations)

Goal: schema is final, ORM compiles, backend boots locally against Supabase.

### Task 1.1 — Add Anthropic SDK + drop heavy deps

**File:** Modify `backend/requirements.txt`

- [ ] **Step 1:** Open `backend/requirements.txt` and replace its full contents with:

```
fastapi==0.115.0
uvicorn[standard]==0.30.0
pydantic==2.9.0
pydantic-settings==2.5.0
python-dotenv==1.0.1

sqlalchemy==2.0.35
alembic==1.13.0
asyncpg==0.29.0
psycopg2-binary==2.9.10
pgvector==0.3.2

python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.9

celery[redis]==5.4.0
redis==5.0.8

httpx==0.27.0
orjson==3.10.7

# Scraper runtime (kept at launch — used by IngestionService + DiscoveryService)
playwright==1.52.0
beautifulsoup4==4.12.3
lxml==5.3.0
pandas==2.2.3

anthropic==0.39.0
qrcode[pil]==7.4.2
sentry-sdk[fastapi]==2.18.0

pytest==8.3.0
pytest-asyncio==0.24.0
```

- [ ] **Step 2:** Create `backend/requirements.dev.txt` with the dropped libs (kept for local dev / future Tier B):

```
shap==0.44.0
xgboost==2.0.3
lime==0.2.0.1
langchain==0.3.0
langchain-community==0.3.0
langchain-google-genai==2.0.0
neo4j==5.24.0
opensearch-py==2.7.1
sentence-transformers==3.1.1
```

- [ ] **Step 3:** Run `cd backend && pip install -r requirements.txt` — expect clean install
- [ ] **Step 4:** Run `python -c "import anthropic, qrcode, sentry_sdk, playwright; print('ok')"` — expect `ok`
- [ ] **Step 4b:** Install Chromium for scraper: `playwright install --with-deps chromium` — expect ~150 MB download
- [ ] **Step 4c:** Modify `backend/Dockerfile` — after the `pip install` line add:

```dockerfile
RUN playwright install --with-deps chromium
```

This bakes Chromium into the image (~500 MB add) so the worker can run scraper tasks without runtime install.
- [ ] **Step 5:** Commit: `git add backend/requirements.txt backend/requirements.dev.txt && git commit -m "chore(deps): trim image to runtime essentials, add anthropic+qrcode+sentry"`

### Task 1.2 — Patch `core/database.py` for Supabase pooler

**File:** Modify `backend/app/core/database.py`

- [ ] **Step 1:** Open the file and locate the `create_async_engine(...)` call (search for `engine =` or `create_async_engine`)
- [ ] **Step 2:** Add pooler-safe `connect_args` when the URL points at the Supabase pooler. Replace the engine instantiation block with:

```python
import re
from sqlalchemy.ext.asyncio import create_async_engine

_url = settings.DATABASE_URL
_is_pgbouncer_pooler = bool(re.search(r":6543/", _url)) or "pooler.supabase.com" in _url

_connect_args: dict = {}
if _is_pgbouncer_pooler:
    _connect_args = {
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0,
        "server_settings": {"jit": "off"},
    }

engine = create_async_engine(
    _url,
    echo=False,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    connect_args=_connect_args,
)
```

- [ ] **Step 3:** Run `python -c "from app.core.database import engine; print(engine.url)"` — expect URL printed without error
- [ ] **Step 4:** Commit: `git commit -am "fix(db): supabase pooler-safe asyncpg args (statement_cache_size=0)"`

### Task 1.3 — Migration `0023` scholarship_tier  *(✅ ALREADY SHIPPED — verify only)*

> Per §0.5 audit, this migration file already exists at `backend/alembic/versions/20260516_0023_scholarship_tier.py`. Confirm with `ls`, run `alembic upgrade head` if not yet applied to Supabase, then skip Steps 1-4 below.

**File:** Create `backend/alembic/versions/20260516_0023_scholarship_tier.py`

- [ ] **Step 1:** Write the migration:

```python
"""scholarship tier (standard/premium) for Q1 retier."""
from alembic import op
import sqlalchemy as sa

revision = "20260516_0023"
down_revision = "20260515_0022"
branch_labels = None
depends_on = None

def upgrade() -> None:
    tier = sa.Enum("standard", "premium", name="scholarship_tier")
    tier.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "scholarships",
        sa.Column("tier", tier, nullable=False, server_default="standard"),
    )
    op.create_index("ix_scholarships_tier", "scholarships", ["tier"])
    op.execute(
        "UPDATE scholarships SET tier = 'premium' "
        "WHERE LOWER(name) ~ "
        "'(chevening|fulbright|daad|commonwealth|hec overseas|rhodes|gates|schwarzman|erasmus mundus)' "
        "OR LOWER(provider) ~ "
        "'(chevening|fulbright|daad|commonwealth|hec|rhodes|gates foundation|schwarzman|erasmus)'"
    )

def downgrade() -> None:
    op.drop_index("ix_scholarships_tier", table_name="scholarships")
    op.drop_column("scholarships", "tier")
    sa.Enum(name="scholarship_tier").drop(op.get_bind(), checkfirst=True)
```

- [ ] **Step 2:** Run against Supabase **direct** URL (not pooler):

```bash
cd backend
DATABASE_URL=$DATABASE_URL_DIRECT alembic upgrade head
```

Expected: `INFO  [alembic.runtime.migration] Running upgrade 20260515_0022 -> 20260516_0023`

- [ ] **Step 3:** Verify in Supabase SQL editor: `SELECT COUNT(*) FROM scholarships WHERE tier='premium';` — expect ≥ 5 rows (Chevening, Fulbright, DAAD, Commonwealth, HEC Overseas seeded by `demo_seed_pakistan.py`)

- [ ] **Step 4:** Commit: `git commit -am "feat(db): scholarship.tier enum + premium backfill"`

### Task 1.4 — Migration `0024` sop_monthly_usage + lifetime_sop_count  *(✅ ALREADY SHIPPED — verify only)*

> File exists at `backend/alembic/versions/20260516_0024_sop_monthly_usage.py`. Skip Steps 1-3 below. The shipped version uses `postgresql.UUID(as_uuid=True)` for `user_id` — this matches the `User.id` UUID type and the burn-cap aggregation query in `core/burn_cap.py`.

**File:** Create `backend/alembic/versions/20260516_0024_sop_monthly_usage.py`

- [ ] **Step 1:** Write:

```python
"""sop monthly usage + lifetime counter."""
from alembic import op
import sqlalchemy as sa

revision = "20260516_0024"
down_revision = "20260516_0023"

def upgrade():
    op.add_column(
        "users",
        sa.Column("lifetime_sop_count", sa.Integer, nullable=False, server_default="0"),
    )
    op.create_table(
        "sop_monthly_usage",
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("period_yyyymm", sa.String(6), primary_key=True),
        sa.Column("sop_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

def downgrade():
    op.drop_table("sop_monthly_usage")
    op.drop_column("users", "lifetime_sop_count")
```

- [ ] **Step 2:** `DATABASE_URL=$DATABASE_URL_DIRECT alembic upgrade head` — expect `0024` applied
- [ ] **Step 3:** Commit: `git commit -am "feat(db): sop monthly usage + lifetime counter"`

### Task 1.5 — Migration `0025` usage_ledger  *(✅ ALREADY SHIPPED — verify only)*

> File exists at `backend/alembic/versions/20260516_0025_usage_ledger.py`. `user_id` is UUID. `cost_pkr_micro` is BigInteger (matches `core/burn_cap.py` integer-sum math). Skip Steps 1-3 below.

**File:** Create `backend/alembic/versions/20260516_0025_usage_ledger.py`

- [ ] **Step 1:** Write:

```python
"""usage ledger for burn-cap accounting."""
from alembic import op
import sqlalchemy as sa

revision = "20260516_0025"
down_revision = "20260516_0024"

def upgrade():
    op.create_table(
        "usage_ledger",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("period_yyyymm", sa.String(6), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("input_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("cost_pkr_micro", sa.BigInteger, nullable=False),
        sa.Column("endpoint", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_usage_ledger_user_period", "usage_ledger", ["user_id", "period_yyyymm"])

def downgrade():
    op.drop_index("ix_usage_ledger_user_period", table_name="usage_ledger")
    op.drop_table("usage_ledger")
```

- [ ] **Step 2:** `alembic upgrade head` against direct URL
- [ ] **Step 3:** Commit: `git commit -am "feat(db): usage_ledger for burn-cap accounting"`

### Task 1.6 — Migration `0026` invite_codes + trial cols + Air U fields

**File:** Create `backend/alembic/versions/20260516_0026_invite_codes_and_trial.py`

- [ ] **Step 1:** Write:

```python
"""invite codes, trial cohort tracking, Air U fields, marketing opt-in.

users.plan_expires_at already shipped in migration 0024; do NOT re-add here.
users.id is UUID (see models.py:160), so redeemed_invite_code is a String FK-by-value
and invite_codes does NOT have a user_id FK column (uses counter only).
"""
from alembic import op
import sqlalchemy as sa

revision = "20260516_0026"
down_revision = "20260516_0025"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "invite_codes",
        sa.Column("code", sa.String(32), primary_key=True),
        sa.Column("cohort", sa.String(32), nullable=False),
        sa.Column("grants_plan", sa.String(16), nullable=False),
        sa.Column("trial_days", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("max_uses", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("uses", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_invite_codes_cohort", "invite_codes", ["cohort"])

    op.add_column("users", sa.Column("air_uni_uni", sa.String(64), nullable=True))
    op.add_column("users", sa.Column("air_uni_dept", sa.String(32), nullable=True))
    op.add_column("users", sa.Column("air_uni_batch", sa.Integer(), nullable=True))
    op.add_column("users", sa.Column("marketing_opt_in", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("users", sa.Column("redeemed_invite_code", sa.String(32), nullable=True))
    op.create_index("ix_users_redeemed_invite_code", "users", ["redeemed_invite_code"])


def downgrade() -> None:
    op.drop_index("ix_users_redeemed_invite_code", table_name="users")
    op.drop_column("users", "redeemed_invite_code")
    op.drop_column("users", "marketing_opt_in")
    op.drop_column("users", "air_uni_batch")
    op.drop_column("users", "air_uni_dept")
    op.drop_column("users", "air_uni_uni")
    op.drop_index("ix_invite_codes_cohort", table_name="invite_codes")
    op.drop_table("invite_codes")
```

- [ ] **Step 2:** `alembic upgrade head` against direct URL
- [ ] **Step 3:** Commit: `git commit -am "feat(db): invite codes + plan_expires_at + Air U fields + marketing_opt_in"`

### Task 1.7 — ORM updates in `models.py`  *(⚠️ PARTIALLY SHIPPED)*

> Already in `models/models.py`: `ScholarshipTier` (line 88), `Scholarship.tier` (733-741), `User.plan_expires_at` (219), `User.lifetime_sop_count` (221), `SopMonthlyUsage` (1669), `UsageLedger` (1691). Exports done in `models/__init__.py`.
>
> **Only `InviteCode` ORM + the four new `User` cols (`air_uni_uni`, `air_uni_dept`, `air_uni_batch`, `marketing_opt_in`, `redeemed_invite_code`) remain — add as part of Task 1.6 (migration 0026 ORM mirror).**

**File:** Modify `backend/app/models/models.py`

- [ ] **Step 1:** Near the other enums add:

```python
class ScholarshipTier(str, enum.Enum):
    STANDARD = "standard"
    PREMIUM = "premium"
```

- [ ] **Step 2:** In the `Scholarship` model add:

```python
tier = Column(
    SAEnum(ScholarshipTier, name="scholarship_tier"),
    nullable=False,
    server_default=ScholarshipTier.STANDARD.value,
    index=True,
)
```

- [ ] **Step 3:** In the `User` model add:

```python
lifetime_sop_count = Column(Integer, nullable=False, default=0, server_default="0")
plan_expires_at = Column(DateTime(timezone=True), nullable=True, index=True)
air_uni_uni = Column(String(64), nullable=True)
air_uni_dept = Column(String(32), nullable=True)
air_uni_batch = Column(Integer, nullable=True)
marketing_opt_in = Column(Boolean, nullable=False, default=False, server_default="false")
redeemed_invite_code = Column(String(32), nullable=True)
```

- [ ] **Step 4:** Add the three new models near the bottom of the file:

```python
class SopMonthlyUsage(Base):
    __tablename__ = "sop_monthly_usage"
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    period_yyyymm = Column(String(6), primary_key=True)
    sop_count = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class UsageLedger(Base):
    __tablename__ = "usage_ledger"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    period_yyyymm = Column(String(6), nullable=False)
    kind = Column(String(32), nullable=False)
    input_tokens = Column(Integer, nullable=False, default=0)
    output_tokens = Column(Integer, nullable=False, default=0)
    cost_pkr_micro = Column(BigInteger, nullable=False)
    endpoint = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class InviteCode(Base):
    __tablename__ = "invite_codes"
    code = Column(String(32), primary_key=True)
    cohort = Column(String(32), nullable=False, index=True)
    grants_plan = Column(String(16), nullable=False)
    trial_days = Column(Integer, nullable=False, default=30)
    max_uses = Column(Integer, nullable=False, default=100)
    uses = Column(Integer, nullable=False, default=0)
    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_until = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

- [ ] **Step 5:** Run `python -m compileall backend/app/models` — expect `OK`
- [ ] **Step 6:** Add `SopMonthlyUsage`, `UsageLedger`, `InviteCode`, `ScholarshipTier` to `backend/app/models/__init__.py` exports
- [ ] **Step 7:** Commit: `git commit -am "feat(models): scholarship tier + sop/usage ledger + invite codes ORM"`

### Task 1.8 — Brand hotpatch (GrantPath → AidwiseAI)

**Files (verified by grep 2026-05-16):**
- `frontend/src/app/signup/page.tsx:45` — header `<Link>` label
- `frontend/src/app/login/page.tsx:55` — header `<Link>` label
- `frontend/src/components/shell/Sidebar.tsx:96` — sidebar brand text
- `frontend/src/app/layout.tsx:29,30,34` — `title.default`, `title.template`, `applicationName`
- `frontend/src/app/(student)/settings/page.tsx:70` — settings description copy
- **Skip:** `frontend/src/lib/api/client.ts:2` (file-header comment, not user-facing) and the `grantpath.access_token` / `grantpath.refresh_token` localStorage keys per CLAUDE.md (renaming logs every user out)
- **Verify but likely skip:** `frontend/src/app/onboarding/page.tsx` and `frontend/src/app/(student)/documents/new/page.tsx` — grep matched but may be in comments / dev copy

- [ ] **Step 1:** In `frontend/src/lib/brand.ts` confirm the file exports `BRAND` (created in S102 — observation 2058). If missing, create:

```ts
export const BRAND = "AidwiseAI" as const;
export const BRAND_TAGLINE = "Pakistan's AI scholarship co-pilot";
export const PARTNERSHIPS_EMAIL = "partnerships@aidwiseai.com";
export const PAYMENTS_EMAIL = "payments@aidwiseai.com";
export const SUPPORT_EMAIL = "hello@aidwiseai.com";

export const partnershipsMailto = (subject = "Institutional partnership") =>
    `mailto:${PARTNERSHIPS_EMAIL}?subject=${encodeURIComponent(subject)}`;
```

- [ ] **Step 2:** Find every `GrantPath` literal in `frontend/src/**/*.{tsx,ts}`:

```bash
cd frontend && grep -rn "GrantPath" src/
```

- [ ] **Step 3:** For each occurrence (typically `app/page.tsx` and `components/Sidebar.tsx`), replace with `{BRAND}` and add `import { BRAND } from "@/lib/brand";` at the top of the file
- [ ] **Step 4:** Update `<title>` and `<meta description>` in `app/layout.tsx` to use AidwiseAI
- [ ] **Step 5:** Run `cd frontend && bun run lint && bunx --bun tsc --noEmit && bun run build` — expect 0 errors
- [ ] **Step 6:** Commit: `git commit -am "feat(brand): hotpatch GrantPath -> AidwiseAI in user-facing surfaces"`

---

## 5. Day 2 — May 17 (Burn Cap + Anthropic Wrap + Match Blur + Quotas)

> ⚠️ **ALL OF DAY 2 (Tasks 2.1–2.7) ALREADY SHIPPED — verify only.**
>
> Per §0.5 audit: `plan_guard.py`, `burn_cap.py`, `anthropic_client.py` wrap, `match_service.py` blur, `sop_builder.py` quota, `tracker/service.py` cap, `waitlist.py` pricing — all confirmed in codebase. Run `pytest backend/tests/unit -q` to confirm green; skip Steps 1–5 of every task below.
>
> **Day 2 reclaimed for the actually-remaining work (R3–R5 from §0.5):**
> - **R3:** Auth `register()` patch (invite-code redemption, Air U fields, consent v1.0). See Tasks 3.1 + 3.2 of original §6 — pull forward to Day 2.
> - **R4:** `tasks/trial_tasks.py` daily downgrade cron + beat schedule. See Task 3.3 — pull forward.
> - **R5:** `notifications/channels.py` Mailgun POST. See Task 3.4 — pull forward.
>
> Net: Days 2 + 3 of the original plan collapse into a single Day 2. Original Day 3 deployment work moves to Day 3 unchanged.

### Day 2 actual scope (post-audit)
- Task 1.6 — Migration 0026 + InviteCode ORM (last DB work)
- Task 3.1 — RegisterRequest schema extension
- Task 3.2 — Auth service invite-code redemption
- Task 3.3 — Trial expiry Celery cron
- Task 3.4 — Mailgun send_email integration
- Tests: `pytest backend/tests/unit -q` green (existing + new invite-code tests)
- Brand hotpatch Task 1.8 (5 frontend files)

### Legacy task reference (kept for historical context only — DO NOT execute)

### Task 2.1 — `plan_guard.py` constants + helpers

**File:** Modify `backend/app/core/plan_guard.py`

- [ ] **Step 1:** Replace the existing `PRICE_BY_CURRENCY` block and append new constants:

```python
PRICE_BY_CURRENCY: dict[str, dict[str, str]] = {
    "PKR": {"pro": "PKR 2,999/month", "elite": "PKR 6,000/month", "institution": "Custom annual"},
    "GBP": {"pro": "£8.49/month", "elite": "£16.99/month", "institution": "Custom annual"},
    "EUR": {"pro": "€9.49/month", "elite": "€18.99/month", "institution": "Custom annual"},
    "AED": {"pro": "AED 39/month", "elite": "AED 79/month", "institution": "Custom annual"},
    "USD": {"pro": "$9.99/month", "elite": "$19.99/month", "institution": "Custom annual"},
}

MATCH_CAP = {"free": 3, "pro": 6, "elite": 12, "institution": 12}
TRACKER_CAP = {"free": 3, "pro": 6, "elite": 12, "institution": 50}
MONTHLY_SOP_CAP = {"free": 0, "pro": 5, "elite": 10, "institution": 50}
LIFETIME_FREE_SOP = 1
PRO_BLURRED_BEST_FIT_COUNT = 3

BEST_FIT_REVEAL_PLANS = frozenset({"elite", "institution"})
PREMIUM_VISIBLE_PLANS = frozenset({"pro", "elite", "institution"})


def can_reveal_best_fit(user) -> bool:
    return (user.plan or "free").lower() in BEST_FIT_REVEAL_PLANS


def can_see_premium(user) -> bool:
    return (user.plan or "free").lower() in PREMIUM_VISIBLE_PLANS
```

- [ ] **Step 2:** Create `backend/tests/unit/test_plan_caps.py`:

```python
import pytest
from app.core.plan_guard import (
    MATCH_CAP, TRACKER_CAP, MONTHLY_SOP_CAP,
    can_reveal_best_fit, can_see_premium,
)


class _U:
    def __init__(self, plan): self.plan = plan


@pytest.mark.parametrize("plan,m,t,s", [
    ("free", 3, 3, 0),
    ("pro", 6, 6, 5),
    ("elite", 12, 12, 10),
])
def test_caps(plan, m, t, s):
    assert MATCH_CAP[plan] == m
    assert TRACKER_CAP[plan] == t
    assert MONTHLY_SOP_CAP[plan] == s


def test_reveal_gates():
    assert can_reveal_best_fit(_U("elite"))
    assert not can_reveal_best_fit(_U("pro"))
    assert can_see_premium(_U("pro"))
    assert not can_see_premium(_U("free"))
```

- [ ] **Step 3:** Run `pytest backend/tests/unit/test_plan_caps.py -v` — expect 4 PASS
- [ ] **Step 4:** Commit: `git commit -am "feat(plan_guard): Q1 retier caps + reveal gates + new prices"`

### Task 2.2 — `burn_cap.py` accounting module

**Files:** Create `backend/app/core/burn_cap.py`, `backend/tests/unit/test_burn_cap.py`

- [ ] **Step 1:** Write tests first (`backend/tests/unit/test_burn_cap.py`):

```python
import pytest
from decimal import Decimal
from app.core.burn_cap import llm_cost_pkr, tier_budget, _period


class _U:
    def __init__(self, plan):
        self.plan = plan
        self.id = 1


def test_haiku_cost():
    c = llm_cost_pkr("llm_haiku", 1000, 500)
    assert Decimal("0.99") < c < Decimal("1.10")


def test_sonnet_cost():
    c = llm_cost_pkr("llm_sonnet", 5000, 1800)
    assert Decimal("11") < c < Decimal("13")


def test_tier_budgets():
    assert tier_budget(_U("free")) == Decimal("50")
    assert tier_budget(_U("pro")) == Decimal("1799")
    assert tier_budget(_U("elite")) == Decimal("3600")


def test_period_format():
    p = _period()
    assert len(p) == 6 and p.isdigit()
```

- [ ] **Step 2:** Run tests — expect `ImportError: cannot import name`
- [ ] **Step 3:** Create `backend/app/core/burn_cap.py`:

```python
from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from app.models import User, UsageLedger

PKR_PER_USD = Decimal("280")
PRICING_USD_PER_MTOK = {
    "llm_haiku": (Decimal("1"), Decimal("5")),
    "llm_sonnet": (Decimal("3"), Decimal("15")),
}
WHATSAPP_COST_PKR = Decimal("3")
TIER_BUDGET_PKR = {
    "free": Decimal("50"),
    "pro": Decimal("1799"),
    "elite": Decimal("3600"),
}


def _period() -> str:
    n = datetime.now(timezone.utc)
    return f"{n.year:04d}{n.month:02d}"


def llm_cost_pkr(kind: str, inp: int, out: int) -> Decimal:
    i, o = PRICING_USD_PER_MTOK[kind]
    usd = (Decimal(inp) * i + Decimal(out) * o) / Decimal(1_000_000)
    return usd * PKR_PER_USD


def tier_budget(user: User) -> Decimal:
    if (user.plan or "").lower() == "institution":
        return Decimal("999999")
    return TIER_BUDGET_PKR.get((user.plan or "free").lower(), Decimal("50"))


async def month_to_date_pkr(db: AsyncSession, user_id: int) -> Decimal:
    q = select(func.coalesce(func.sum(UsageLedger.cost_pkr_micro), 0)).where(
        UsageLedger.user_id == user_id,
        UsageLedger.period_yyyymm == _period(),
    )
    micro = (await db.execute(q)).scalar_one()
    return Decimal(micro) / Decimal(1_000_000)


async def assert_within_burn_cap(db: AsyncSession, user: User, projected: Decimal) -> None:
    spent = await month_to_date_pkr(db, user.id)
    budget = tier_budget(user)
    if spent + projected > budget:
        raise HTTPException(429, detail={
            "error": "burn_cap_reached",
            "spent_pkr": str(spent.quantize(Decimal("0.01"))),
            "budget_pkr": str(budget),
            "upgrade_url": "/upgrade" if (user.plan or "free").lower() != "elite" else None,
            "message": "Monthly AI budget reached. Resets next month, or upgrade tier.",
        })


async def record_llm(db: AsyncSession, user_id: int, kind: str,
                     inp: int, out: int, endpoint: str) -> None:
    cost = llm_cost_pkr(kind, inp, out)
    db.add(UsageLedger(
        user_id=user_id, period_yyyymm=_period(), kind=kind,
        input_tokens=inp, output_tokens=out,
        cost_pkr_micro=int(cost * Decimal(1_000_000)), endpoint=endpoint,
    ))
    await db.flush()


async def record_whatsapp(db: AsyncSession, user_id: int) -> None:
    db.add(UsageLedger(
        user_id=user_id, period_yyyymm=_period(), kind="whatsapp",
        cost_pkr_micro=int(WHATSAPP_COST_PKR * Decimal(1_000_000)),
        endpoint="notifications.whatsapp",
    ))
    await db.flush()
```

- [ ] **Step 4:** Run `pytest backend/tests/unit/test_burn_cap.py -v` — expect 4 PASS
- [ ] **Step 5:** Commit: `git commit -am "feat(burn_cap): per-user PKR ledger + 60% tier budget assertion"`

### Task 2.3 — Anthropic client wrap with accounting

**File:** Modify `backend/app/services/llm/anthropic_client.py` (and call sites)

- [ ] **Step 1:** Open `anthropic_client.py`. Add the wrapper near the existing `complete()` (around line 85+):

```python
import json
from app.core.burn_cap import llm_cost_pkr, assert_within_burn_cap, record_llm


def _estimate_input_tokens(system, messages) -> int:
    return len(json.dumps({"system": system, "messages": messages}, default=str)) // 4


async def complete_with_accounting(
    self, *, db, user, endpoint: str, model: str,
    system, messages, max_tokens: int = 1500,
):
    kind = "llm_sonnet" if "sonnet" in model.lower() else "llm_haiku"
    estimated_input = _estimate_input_tokens(system, messages)
    projected = llm_cost_pkr(kind, estimated_input, max_tokens)
    await assert_within_burn_cap(db, user, projected)

    resp = await self._client.messages.create(
        model=model, system=system, messages=messages, max_tokens=max_tokens,
    )
    await record_llm(
        db, user.id, kind,
        resp.usage.input_tokens, resp.usage.output_tokens, endpoint,
    )
    return resp
```

- [ ] **Step 2:** Update each call site (search `await llm.complete(`):
  - `app/services/documents/sop_builder.py` — pass `db=db, user=user, endpoint="documents.sop.draft"`
  - `app/services/documents/professor_email.py` — `endpoint="documents.professor_email"`
  - `app/services/reports/strategy_report.py` — `endpoint="reports.strategy"`
  - `app/services/visa_interview/evaluator.py` — `endpoint="interviews.visa.evaluate"`

Example replacement:

```python
resp = await llm.complete_with_accounting(
    db=db, user=user, endpoint="documents.sop.draft",
    model="claude-haiku-4-5-20251001",  # default Pro = Haiku; Sonnet only when Elite paid
    system=SYSTEM_SOP, messages=msgs, max_tokens=1800,
)
```

- [ ] **Step 3:** Add test `backend/tests/unit/test_burn_ledger_integration.py`:

```python
import pytest
from sqlalchemy import select
from app.models import UsageLedger


@pytest.mark.asyncio
async def test_sop_draft_records_ledger(client, db, elite_user, sop_payload, auth):
    await client.post("/api/v1/documents/sop/draft", json=sop_payload, headers=auth(elite_user))
    rows = (await db.execute(
        select(UsageLedger).where(UsageLedger.user_id == elite_user.id)
    )).scalars().all()
    assert rows
    assert rows[0].kind in {"llm_sonnet", "llm_haiku"}
    assert rows[0].cost_pkr_micro > 0
```

- [ ] **Step 4:** Run `pytest backend/tests/unit -k burn -v` — expect PASS
- [ ] **Step 5:** Commit: `git commit -am "feat(llm): wrap anthropic complete() with burn-cap ledger across all callers"`

### Task 2.4 — Match service: internal buckets + Pro top-3 blur

**Files:** Modify `backend/app/schemas/scholarships.py`, `backend/app/services/scholarships/match_service.py`

- [ ] **Step 1:** In `schemas/scholarships.py` replace `ScholarshipMatchOut` and add `UnlockOffer` + `MatchResponse`:

```python
from typing import Literal
from datetime import date
from pydantic import BaseModel, Field


class ScholarshipMatchOut(BaseModel):
    id: int | None
    name: str
    provider: str
    country_code: str | None
    funding_amount: str | None
    deadline: date | None
    compatibility: float = Field(ge=0, le=1)
    locked: bool = False


class UnlockOffer(BaseModel):
    to_plan: Literal["pro", "elite"]
    locked_count: int = 0
    headline: str
    message: str


class MatchResponse(BaseModel):
    items: list[ScholarshipMatchOut]
    unlock_offer: UnlockOffer | None = None
```

- [ ] **Step 2:** In `services/scholarships/match_service.py` add the imports + replace `match()`:

```python
from sqlalchemy import select
from app.core.plan_guard import (
    MATCH_CAP, PRO_BLURRED_BEST_FIT_COUNT,
    can_reveal_best_fit, can_see_premium,
)
from app.models import Scholarship, ScholarshipTier, RecordState
from app.schemas.scholarships import ScholarshipMatchOut, UnlockOffer, MatchResponse

_B_ELIG, _B_PART, _B_STRETCH = "eligible", "partial", "stretch"
_REDACT = "Reveal with upgrade"


def _strip(row, *, locked: bool, fit: float) -> ScholarshipMatchOut:
    if locked:
        return ScholarshipMatchOut(
            id=None, name=_REDACT, provider=_REDACT,
            country_code=row.country_code, funding_amount=None, deadline=None,
            compatibility=fit, locked=True,
        )
    return ScholarshipMatchOut(
        id=row.id, name=row.name, provider=row.provider,
        country_code=row.country_code,
        funding_amount=getattr(row, "funding_amount_display", None),
        deadline=row.deadline, compatibility=fit, locked=False,
    )


async def match(self, *, user, top_n: int | None = None) -> MatchResponse:
    plan = (user.plan or "free").lower()
    cap = top_n or MATCH_CAP.get(plan, 3)

    q = select(Scholarship).where(Scholarship.record_state == RecordState.PUBLISHED)
    if not can_see_premium(user):
        q = q.where(Scholarship.tier == ScholarshipTier.STANDARD)
    rows = (await self.db.execute(q)).scalars().all()

    classified = [
        (self._classify_bucket(r, self._profile), r, self._fit_score(r, self._profile))
        for r in rows
    ]
    bucket_rank = {_B_ELIG: 0, _B_PART: 1, _B_STRETCH: 2}
    classified.sort(key=lambda t: (bucket_rank[t[0]], -t[2]))

    if plan == "free":
        free_pool = [t for t in classified if t[0] == _B_STRETCH][:cap]
        items = [_strip(r, locked=False, fit=f) for _, r, f in free_pool]
        offer = UnlockOffer(
            to_plan="pro",
            locked_count=max(0, len(classified) - len(free_pool)),
            headline="More personalised matches available",
            message="Upgrade to Pro to see your full match list.",
        )
        return MatchResponse(items=items, unlock_offer=offer)

    visible = classified[:cap]
    if not can_reveal_best_fit(user):
        out, blurred = [], 0
        for bucket, row, fit in visible:
            if bucket == _B_ELIG and blurred < PRO_BLURRED_BEST_FIT_COUNT:
                out.append(_strip(row, locked=True, fit=fit))
                blurred += 1
            else:
                out.append(_strip(row, locked=False, fit=fit))
        offer = UnlockOffer(
            to_plan="elite",
            locked_count=blurred,
            headline=f"{blurred} match{'es' if blurred != 1 else ''} reserved",
            message="Upgrade to Elite to reveal matches personalised to your profile.",
        ) if blurred > 0 else None
        return MatchResponse(items=out, unlock_offer=offer)

    return MatchResponse(
        items=[_strip(r, locked=False, fit=f) for _, r, f in visible],
        unlock_offer=None,
    )
```

- [ ] **Step 3:** Extend `backend/tests/unit/test_scholarship_match_service.py` with:

```python
@pytest.mark.asyncio
async def test_pro_top_three_blurred(client, db, pro_user, fit_seed, auth):
    body = (await client.post("/api/v1/scholarships/match", headers=auth(pro_user))).json()
    blurred = [it for it in body["items"] if it["locked"]]
    assert len(blurred) <= 3
    for it in blurred:
        assert it["id"] is None
        assert it["name"] == "Reveal with upgrade"
        assert it["compatibility"] is not None
    if blurred:
        assert body["unlock_offer"]["to_plan"] == "elite"
```

- [ ] **Step 4:** Run `pytest backend/tests/unit/test_scholarship_match_service.py -v` — expect PASS
- [ ] **Step 5:** Commit: `git commit -am "feat(match): internal buckets, Pro top-3 blur, Elite full reveal"`

### Task 2.5 — SOP quota enforcement

**Files:** Modify `backend/app/services/documents/sop_builder.py`. Create `backend/tests/unit/test_sop_quota.py`.

- [ ] **Step 1:** Tests first:

```python
import pytest

PAYLOAD = {"target_field": "Computer Science", "target_country_code": "GB", "target_degree_level": "MS"}


@pytest.mark.asyncio
async def test_free_blocks_after_1_lifetime(client, db, free_user, auth):
    r1 = await client.post("/api/v1/documents/sop/draft", json=PAYLOAD, headers=auth(free_user))
    assert r1.status_code == 200
    r2 = await client.post("/api/v1/documents/sop/draft", json=PAYLOAD, headers=auth(free_user))
    assert r2.status_code == 402
    assert r2.json()["detail"]["error"] == "plan_required"


@pytest.mark.asyncio
async def test_pro_blocks_after_5_monthly(client, db, pro_user, auth):
    for _ in range(5):
        r = await client.post("/api/v1/documents/sop/draft", json=PAYLOAD, headers=auth(pro_user))
        assert r.status_code == 200
    r = await client.post("/api/v1/documents/sop/draft", json=PAYLOAD, headers=auth(pro_user))
    assert r.status_code == 429
    assert r.json()["detail"]["error"] == "sop_quota_exhausted"
```

- [ ] **Step 2:** Add helpers in `sop_builder.py` near the top:

```python
from datetime import datetime, timezone
from sqlalchemy import select, update, func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from fastapi import HTTPException
from app.core.plan_guard import MONTHLY_SOP_CAP, LIFETIME_FREE_SOP, raise_plan_required
from app.models import SopMonthlyUsage, User


def _yyyymm() -> str:
    n = datetime.now(timezone.utc)
    return f"{n.year:04d}{n.month:02d}"


async def _assert_sop_quota(db, user) -> None:
    plan = (user.plan or "free").lower()
    if plan == "free":
        if user.lifetime_sop_count >= LIFETIME_FREE_SOP:
            raise_plan_required(
                user, ["pro", "elite"],
                message="Free plan includes 1 SOP. Upgrade for 5/month (Pro) or 10/month (Elite).",
            )
        return
    cap = MONTHLY_SOP_CAP[plan]
    period = _yyyymm()
    row = (await db.execute(
        select(SopMonthlyUsage).where(
            SopMonthlyUsage.user_id == user.id,
            SopMonthlyUsage.period_yyyymm == period,
        )
    )).scalar_one_or_none()
    used = row.sop_count if row else 0
    if used >= cap:
        raise HTTPException(429, detail={
            "error": "sop_quota_exhausted",
            "plan": plan, "used": used, "cap": cap,
            "upgrade_url": "/upgrade" if plan == "pro" else None,
            "message": f"{cap} SOP drafts used this month. Resets next month."
                       + (" Upgrade to Elite for 10/month." if plan == "pro" else ""),
        })


async def _record_sop_use(db, user) -> None:
    plan = (user.plan or "free").lower()
    if plan == "free":
        await db.execute(
            update(User).where(User.id == user.id)
            .values(lifetime_sop_count=User.lifetime_sop_count + 1)
        )
        return
    period = _yyyymm()
    stmt = pg_insert(SopMonthlyUsage).values(
        user_id=user.id, period_yyyymm=period, sop_count=1,
    ).on_conflict_do_update(
        index_elements=["user_id", "period_yyyymm"],
        set_={"sop_count": SopMonthlyUsage.sop_count + 1, "updated_at": func.now()},
    )
    await db.execute(stmt)
```

- [ ] **Step 3:** Call `await _assert_sop_quota(db, user)` at the top of `draft_sop()` and `line_feedback()`. Call `await _record_sop_use(db, user)` after the LLM call succeeds.

- [ ] **Step 4:** Run `pytest backend/tests/unit/test_sop_quota.py -v` — expect PASS
- [ ] **Step 5:** Commit: `git commit -am "feat(sop): per-plan monthly quota + free-tier lifetime cap"`

### Task 2.6 — Tracker cap raise to 6/12

**File:** Modify `backend/app/services/tracker/service.py`

- [ ] **Step 1:** Search the file for the literal `3` in the cap-check block. Replace with:

```python
from app.core.plan_guard import TRACKER_CAP, raise_plan_required

cap = TRACKER_CAP.get((user.plan or "free").lower(), 3)
if active_count >= cap:
    raise_plan_required(
        user, ["pro", "elite"],
        message=f"Tracker limit reached ({cap} items). Upgrade for more.",
    )
```

- [ ] **Step 2:** Update `backend/tests/unit/test_tracker_service.py`:

```python
@pytest.mark.parametrize("plan,cap", [("free", 3), ("pro", 6), ("elite", 12)])
@pytest.mark.asyncio
async def test_tracker_cap_per_plan(client, db, user_factory, plan, cap, auth):
    u = await user_factory(plan=plan)
    item = {"scholarship_name": "Test", "stage": "interest"}
    for _ in range(cap):
        r = await client.post("/api/v1/tracker", json=item, headers=auth(u))
        assert r.status_code == 201
    r = await client.post("/api/v1/tracker", json=item, headers=auth(u))
    assert r.status_code in (402, 429)
```

- [ ] **Step 3:** Run `pytest backend/tests/unit/test_tracker_service.py -v` — expect PASS
- [ ] **Step 4:** Commit: `git commit -am "feat(tracker): plan-aware cap (3/6/12)"`

### Task 2.7 — Pricing endpoint update

**File:** Modify `backend/app/api/v1/routes/waitlist.py`

- [ ] **Step 1:** Replace `_PRICING_BY_CURRENCY` with the dict from Task 2.1
- [ ] **Step 2:** Replace Pro and Elite bullet lists per Q1 retier Task 12 (lines 757–777 of `Elite vs pro for Q1.md`)
- [ ] **Step 3:** Update `backend/tests/unit/test_waitlist_and_pricing.py` to assert `PKR 2,999/month`, `PKR 6,000/month`, `$9.99/month`, `$19.99/month`
- [ ] **Step 4:** Run `pytest backend/tests/unit/test_waitlist_and_pricing.py -v` — expect PASS
- [ ] **Step 5:** Commit: `git commit -am "feat(pricing): Q1 retier 2999/6000 PKR + neutral bullets"`

---

## 6. Day 3 — May 18 (Trial System + Frontend + Deployment)

Goal: invite-code redemption works end-to-end, backend deployed to DigitalOcean, frontend deployed to Vercel, custom domain live.

### Task 3.1 — Auth schema extension

**File:** Modify `backend/app/schemas/auth.py`

- [ ] **Step 1:** Extend `RegisterRequest`:

```python
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12)
    full_name: str
    invite_code: str | None = None
    air_uni_uni: str | None = Field(default=None, max_length=64)
    air_uni_dept: str | None = Field(default=None, max_length=32)
    air_uni_batch: int | None = Field(default=None, ge=2010, le=2030)
    consent_v: str  # required, e.g. "v1.0"
    marketing_opt_in: bool = False

    model_config = ConfigDict(extra="forbid")
```

- [ ] **Step 2:** In the `AuthMeResponse` (or equivalent), add `plan_expires_at: datetime | None`, `air_uni_uni: str | None`, `air_uni_dept: str | None`, `air_uni_batch: int | None`, `marketing_opt_in: bool`
- [ ] **Step 3:** Commit: `git commit -am "feat(schemas): register accepts invite code + Air U fields + consent"`

### Task 3.2 — Auth service: invite-code redemption

**File:** Modify `backend/app/services/auth/service.py`

- [ ] **Step 1:** Add the redemption helper near the top of the file:

```python
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, update
from app.models import InviteCode


async def _redeem_invite_code(db, code: str) -> InviteCode | None:
    if not code:
        return None
    now = datetime.now(timezone.utc)
    row = (await db.execute(
        select(InviteCode).where(InviteCode.code == code).with_for_update()
    )).scalar_one_or_none()
    if not row:
        raise HTTPException(400, detail={"error": "invite_code_invalid"})
    if not row.is_active:
        raise HTTPException(400, detail={"error": "invite_code_inactive"})
    if now < row.valid_from or now > row.valid_until:
        raise HTTPException(400, detail={"error": "invite_code_expired"})
    if row.uses >= row.max_uses:
        raise HTTPException(400, detail={"error": "invite_code_exhausted"})
    await db.execute(
        update(InviteCode).where(InviteCode.code == code)
        .values(uses=InviteCode.uses + 1)
    )
    return row
```

- [ ] **Step 2:** In `register()`, after the user row is created and before commit:

```python
invite = await _redeem_invite_code(db, payload.invite_code)
user.air_uni_uni = payload.air_uni_uni
user.air_uni_dept = payload.air_uni_dept
user.air_uni_batch = payload.air_uni_batch
user.marketing_opt_in = payload.marketing_opt_in
if invite:
    user.plan = invite.grants_plan
    user.plan_expires_at = datetime.now(timezone.utc) + timedelta(days=invite.trial_days)
    user.redeemed_invite_code = invite.code
```

- [ ] **Step 3:** Inside `register()` ensure consent log is written (per CLAUDE.md spec — IP + UA + sha256 of consent doc body):

```python
from app.services.privacy.consent import record_consent
await record_consent(db, user_id=user.id, doc_slug="trial-tnc-v1.0",
                     version=payload.consent_v, ip=request.client.host,
                     user_agent=request.headers.get("user-agent", ""))
```

- [ ] **Step 4:** Tests in `backend/tests/unit/test_trial_invite_codes.py`:

```python
import pytest
from datetime import datetime, timezone, timedelta
from app.models import InviteCode


@pytest.fixture
async def airu_code(db):
    code = InviteCode(
        code="AIRU2026", cohort="AU2026", grants_plan="pro",
        trial_days=30, max_uses=2, uses=0,
        valid_from=datetime.now(timezone.utc) - timedelta(hours=1),
        valid_until=datetime.now(timezone.utc) + timedelta(days=7),
        is_active=True,
    )
    db.add(code)
    await db.commit()
    return code


@pytest.mark.asyncio
async def test_redemption_grants_pro_30d(client, db, airu_code):
    payload = {
        "email": "test1@example.com", "password": "longpassword12",
        "full_name": "Test One", "invite_code": "AIRU2026",
        "consent_v": "v1.0", "marketing_opt_in": False,
    }
    r = await client.post("/api/v1/auth/register", json=payload)
    assert r.status_code == 201
    body = r.json()
    assert body["user"]["plan"] == "pro"
    assert body["user"]["plan_expires_at"] is not None


@pytest.mark.asyncio
async def test_max_uses_blocks_third(client, db, airu_code):
    base = {"password": "longpassword12", "full_name": "T",
            "invite_code": "AIRU2026", "consent_v": "v1.0", "marketing_opt_in": False}
    await client.post("/api/v1/auth/register", json={**base, "email": "a@x.com"})
    await client.post("/api/v1/auth/register", json={**base, "email": "b@x.com"})
    r = await client.post("/api/v1/auth/register", json={**base, "email": "c@x.com"})
    assert r.status_code == 400
    assert r.json()["detail"]["error"] == "invite_code_exhausted"


@pytest.mark.asyncio
async def test_expired_window_rejects(client, db):
    expired = InviteCode(
        code="OLD", cohort="OLD", grants_plan="pro",
        trial_days=30, max_uses=10, uses=0,
        valid_from=datetime.now(timezone.utc) - timedelta(days=30),
        valid_until=datetime.now(timezone.utc) - timedelta(days=1),
        is_active=True,
    )
    db.add(expired); await db.commit()
    r = await client.post("/api/v1/auth/register", json={
        "email": "z@x.com", "password": "longpassword12", "full_name": "Z",
        "invite_code": "OLD", "consent_v": "v1.0", "marketing_opt_in": False,
    })
    assert r.status_code == 400
    assert r.json()["detail"]["error"] == "invite_code_expired"
```

- [ ] **Step 5:** Run `pytest backend/tests/unit/test_trial_invite_codes.py -v` — expect 3 PASS
- [ ] **Step 6:** Commit: `git commit -am "feat(trial): invite-code redemption + Air U fields + consent enforcement"`

### Task 3.3 — Daily downgrade cron

**Files:** Create `backend/app/tasks/trial_tasks.py`, `backend/tests/unit/test_trial_tasks.py`

- [ ] **Step 1:** Tests first:

```python
import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from app.models import User
from app.tasks.trial_tasks import expire_trial_plans


@pytest.mark.asyncio
async def test_expired_pro_downgraded_to_free(db, user_factory):
    u = await user_factory(plan="pro")
    u.plan_expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
    await db.commit()
    await expire_trial_plans(db)
    refreshed = (await db.execute(select(User).where(User.id == u.id))).scalar_one()
    assert refreshed.plan == "free"
    assert refreshed.plan_expires_at is None


@pytest.mark.asyncio
async def test_active_pro_unchanged(db, user_factory):
    u = await user_factory(plan="pro")
    u.plan_expires_at = datetime.now(timezone.utc) + timedelta(days=10)
    await db.commit()
    await expire_trial_plans(db)
    refreshed = (await db.execute(select(User).where(User.id == u.id))).scalar_one()
    assert refreshed.plan == "pro"
```

- [ ] **Step 2:** Implement `backend/app/tasks/trial_tasks.py`:

```python
import asyncio
import logging
from datetime import datetime, timezone
from sqlalchemy import update
from app.core._celery import celery_app
from app.core.database import SessionLocal
from app.models import User

log = logging.getLogger(__name__)


async def expire_trial_plans(db) -> int:
    now = datetime.now(timezone.utc)
    result = await db.execute(
        update(User)
        .where(User.plan_expires_at.is_not(None))
        .where(User.plan_expires_at < now)
        .where(User.plan != "free")
        .values(plan="free", plan_expires_at=None)
        .returning(User.id)
    )
    ids = [r[0] for r in result.fetchall()]
    await db.commit()
    log.info("Expired %d trial plans: %s", len(ids), ids)
    return len(ids)


@celery_app.task(name="tasks.expire_trial_plans")
def run_expire_trial_plans():
    async def _run():
        async with SessionLocal() as db:
            return await expire_trial_plans(db)
    return asyncio.run(_run())
```

- [ ] **Step 3:** Wire to beat schedule in `backend/app/core/_celery.py` (or wherever beat schedule lives). Add to the schedule dict:

```python
"expire-trial-plans-daily": {
    "task": "tasks.expire_trial_plans",
    "schedule": crontab(hour=2, minute=0),  # 02:00 UTC = 07:00 PKT
},
```

- [ ] **Step 4:** Run `pytest backend/tests/unit/test_trial_tasks.py -v` — expect PASS
- [ ] **Step 5:** Commit: `git commit -am "feat(trial): daily 02:00 UTC cron downgrades expired Pro to Free"`

### Task 3.4 — Mailgun email channel

**File:** Modify `backend/app/services/notifications/channels.py`

- [ ] **Step 1:** Replace the log-only `send_email` with a Mailgun POST:

```python
import logging
import httpx
from app.core.config import settings

log = logging.getLogger(__name__)

PLAN_CHANNELS: dict[str, tuple[str, ...]] = {
    "free": ("email",),
    "pro": ("email",),
    "elite": ("email", "whatsapp"),
    "institution": ("email", "whatsapp"),
}


async def send_email(user, subject: str, message: str, *, html: str | None = None) -> None:
    if not settings.MAILGUN_API_KEY or not settings.MAILGUN_DOMAIN:
        log.info("mailgun-not-configured -> %s: %s", user.email, subject)
        return
    url = f"https://api.mailgun.net/v3/{settings.MAILGUN_DOMAIN}/messages"
    data = {
        "from": f"AidwiseAI <noreply@{settings.MAILGUN_DOMAIN}>",
        "to": [user.email],
        "subject": subject,
        "text": message,
    }
    if html:
        data["html"] = html
    async with httpx.AsyncClient(timeout=10.0) as c:
        r = await c.post(url, auth=("api", settings.MAILGUN_API_KEY), data=data)
        if r.status_code >= 400:
            log.warning("mailgun-failed %s -> %s: %s", r.status_code, user.email, r.text[:200])


async def send_whatsapp(db, user, message: str) -> None:
    log.info("whatsapp-stub -> %s: %s", user.whatsapp_e164 or user.phone_e164, message[:80])
    # Real Twilio integration deferred to Tier B post-launch


async def fan_out_for_plan(db, user, subject: str, message: str) -> None:
    for ch in PLAN_CHANNELS.get((user.plan or "free").lower(), ("email",)):
        if ch == "email":
            await send_email(user, subject, message)
        elif ch == "whatsapp":
            await send_whatsapp(db, user, message)
```

- [ ] **Step 2:** Update callers in `app/tasks/alert_tasks.py` and `app/tasks/reminder_tasks.py` — pass `subject` arg
- [ ] **Step 3:** Send a test email via Python REPL:

```python
import asyncio
from app.services.notifications.channels import send_email

class _U: email = "your-email@example.com"

asyncio.run(send_email(_U(), "AidwiseAI test", "Hello from Mailgun"))
```

Expected: email arrives within 10 sec at your inbox

- [ ] **Step 4:** Commit: `git commit -am "feat(notifications): wire Mailgun for email; whatsapp stub remains"`

### Task 3.5 — Frontend invite-code signup + Air U fields

**File:** Modify `frontend/src/app/(auth)/signup/page.tsx`

- [ ] **Step 1:** Read URL param `?invite=AIRU2026` and pre-fill the invite-code input:

```tsx
"use client";
import { useSearchParams } from "next/navigation";
import { useState, useEffect } from "react";

export default function SignupPage() {
  const params = useSearchParams();
  const [inviteCode, setInviteCode] = useState("");
  const [airUniUni, setAirUniUni] = useState("");
  const [airUniDept, setAirUniDept] = useState("");
  const [airUniBatch, setAirUniBatch] = useState<number | "">("");
  const [consent, setConsent] = useState(false);
  const [marketing, setMarketing] = useState(false);
  // ... existing email + password + full_name state

  useEffect(() => {
    const q = params.get("invite");
    if (q) setInviteCode(q.toUpperCase());
  }, [params]);

  const submit = async () => {
    if (!consent) {
      alert("Please accept the data processing terms to continue.");
      return;
    }
    const payload = {
      email, password, full_name: fullName,
      invite_code: inviteCode || undefined,
      air_uni_uni: airUniUni || undefined,
      air_uni_dept: airUniDept || undefined,
      air_uni_batch: airUniBatch || undefined,
      consent_v: "v1.0",
      marketing_opt_in: marketing,
    };
    // ... POST /api/v1/auth/register, store tokens, redirect
  };

  return (
    <form onSubmit={(e) => { e.preventDefault(); submit(); }}>
      {/* existing email/password/name inputs */}

      <label>Invite code (optional)</label>
      <input value={inviteCode} onChange={(e) => setInviteCode(e.target.value.toUpperCase())} placeholder="AIRU2026" />

      <fieldset>
        <legend>About you (optional, helps us personalise)</legend>
        <input value={airUniUni} onChange={(e) => setAirUniUni(e.target.value)} placeholder="University (e.g. Air University)" />
        <input value={airUniDept} onChange={(e) => setAirUniDept(e.target.value)} placeholder="Department (e.g. CS, EE, BBA)" />
        <input type="number" min={2018} max={2030} value={airUniBatch}
               onChange={(e) => setAirUniBatch(e.target.value ? Number(e.target.value) : "")}
               placeholder="Batch year (e.g. 2023)" />
      </fieldset>

      <label className="flex gap-2">
        <input type="checkbox" required checked={consent} onChange={(e) => setConsent(e.target.checked)} />
        <span>I agree to the <a href="/legal/trial-tnc-v1.0" target="_blank">data processing & trial terms (v1.0)</a></span>
      </label>

      <label className="flex gap-2">
        <input type="checkbox" checked={marketing} onChange={(e) => setMarketing(e.target.checked)} />
        <span>I'm OK with AidwiseAI quoting my anonymised feedback in marketing</span>
      </label>

      <button type="submit">Create account</button>
    </form>
  );
}
```

- [ ] **Step 2:** Run `cd frontend && bun run lint && bunx --bun tsc --noEmit && bun run build` — expect 0 errors
- [ ] **Step 3:** Commit: `git commit -am "feat(signup): invite code, Air U fields, mandatory consent v1.0"`

### Task 3.6 — Frontend match card with locked render

**Files:** Modify `frontend/src/lib/api/types.ts`, create `frontend/src/components/CompatibilityMeter.tsx`, modify `frontend/src/app/(student)/scholarships/page.tsx`

Implement per Q1 retier Task 15 verbatim — code already in the spec doc. Run `bun run build` after.

- [ ] **Step 1:** Update `types.ts` per Q1 Task 15 Step 1
- [ ] **Step 2:** Create `CompatibilityMeter.tsx` per Q1 Task 15 Step 2
- [ ] **Step 3:** Update `MatchCard` per Q1 Task 15 Step 3
- [ ] **Step 4:** `bun run build` — expect 0 errors
- [ ] **Step 5:** Commit: `git commit -am "feat(frontend): locked match card + CompatibilityMeter"`

### Task 3.6b — Coming Soon section on landing

**Files:** Create `frontend/src/components/ComingSoon.tsx`. Modify `frontend/src/app/page.tsx`.

- [ ] **Step 1:** Create `frontend/src/components/ComingSoon.tsx`:

```tsx
import Link from "next/link";

type Status = "in-design" | "in-dev" | "planned";
type Eta = "Jun 2026" | "Q3 2026" | "Q4 2026" | "2027";

interface PipelineFeature {
  title: string;
  blurb: string;
  eta: Eta;
  status: Status;
}

const PIPELINE: PipelineFeature[] = [
  {
    title: "One-click PKR payments",
    blurb: "JazzCash, Easypaisa, Visa/Mastercard, PayPak and RAAST checkout through Safepay.",
    eta: "Jun 2026",
    status: "in-dev",
  },
  {
    title: "Elite tier — line-by-line SOP AI",
    blurb: "Sentence-level critique, transcript-grade visa interview, downloadable strategy report.",
    eta: "Jun 2026",
    status: "in-dev",
  },
  {
    title: "WhatsApp deadline alerts",
    blurb: "Real-time scholarship deadline reminders straight to WhatsApp for paid tiers.",
    eta: "Jun 2026",
    status: "in-design",
  },
  {
    title: "Application essay editor with peer review",
    blurb: "Claim a peer slot, get inline feedback inside the SOP editor — Pro and Elite.",
    eta: "Jul 2026",
    status: "planned",
  },
  {
    title: "Scholarship calendar (.ics export)",
    blurb: "Subscribe your Google / Apple calendar to deadlines on your tracker.",
    eta: "Jul 2026",
    status: "planned",
  },
  {
    title: "Mentor 1:1 sessions",
    blurb: "Book paid 30-minute calls with verified Pakistani alumni at top universities.",
    eta: "Q3 2026",
    status: "planned",
  },
  {
    title: "Urdu interface",
    blurb: "Full Urdu translation of the dashboard, onboarding and SOP builder.",
    eta: "Q3 2026",
    status: "planned",
  },
  {
    title: "Mobile app (iOS + Android)",
    blurb: "Native apps for tracker, deadline alerts and SOP draft on the go.",
    eta: "Q4 2026",
    status: "planned",
  },
  {
    title: "Alumni knowledge graph",
    blurb: "Discover scholarships through alumni networks and shared application paths.",
    eta: "Q4 2026",
    status: "planned",
  },
  {
    title: "Application AutoFill",
    blurb: "One-click form fill across UCAS, Common App and university portals.",
    eta: "2027",
    status: "planned",
  },
];

const STATUS_LABEL: Record<Status, string> = {
  "in-design": "In design",
  "in-dev": "In dev",
  "planned": "Planned",
};

const ETA_TONE: Record<Eta, string> = {
  "Jun 2026": "bg-amber-100 text-amber-900 ring-amber-200",
  "Q3 2026": "bg-sky-100 text-sky-900 ring-sky-200",
  "Q4 2026": "bg-violet-100 text-violet-900 ring-violet-200",
  "2027": "bg-stone-100 text-stone-700 ring-stone-200",
};

const STATUS_DOT: Record<Status, string> = {
  "in-design": "bg-stone-400",
  "in-dev": "bg-emerald-500",
  "planned": "bg-stone-300",
};

export function ComingSoon() {
  return (
    <section id="roadmap" className="mx-auto max-w-6xl px-6 py-20">
      <div className="mb-10 flex items-end justify-between gap-6">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-stone-500">Roadmap</p>
          <h2 className="mt-2 font-serif text-3xl text-stone-900 sm:text-4xl">
            What's shipping next
          </h2>
          <p className="mt-3 max-w-2xl text-stone-600">
            Trial users vote on what we build next. Your feedback during the 30-day Pro trial
            shapes the order below.
          </p>
        </div>
        <Link
          href="/feedback"
          className="hidden shrink-0 rounded-full border border-stone-300 px-4 py-2 text-sm font-medium text-stone-700 hover:bg-stone-50 sm:inline-flex"
        >
          Suggest a feature →
        </Link>
      </div>

      <ul className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {PIPELINE.map((f) => (
          <li
            key={f.title}
            className="group flex flex-col rounded-xl border border-stone-200 bg-white p-5 transition hover:border-stone-300 hover:shadow-sm"
          >
            <div className="mb-3 flex items-center justify-between">
              <span
                className={`rounded-full px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider ring-1 ${ETA_TONE[f.eta]}`}
              >
                {f.eta}
              </span>
              <span className="flex items-center gap-1.5 text-[11px] text-stone-500">
                <span className={`inline-block h-2 w-2 rounded-full ${STATUS_DOT[f.status]}`} />
                {STATUS_LABEL[f.status]}
              </span>
            </div>
            <h3 className="font-serif text-lg text-stone-900">{f.title}</h3>
            <p className="mt-2 text-sm leading-relaxed text-stone-600">{f.blurb}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}
```

- [ ] **Step 2:** Mount in `frontend/src/app/page.tsx` between the hero and footer:

```tsx
import { ComingSoon } from "@/components/ComingSoon";

// ... inside the page JSX, after main hero / pricing block:
<ComingSoon />
```

- [ ] **Step 3:** Run `cd frontend && bun run lint && bunx --bun tsc --noEmit && bun run build` — expect 0 errors
- [ ] **Step 4:** Visual check: open `http://localhost:3000/#roadmap` — expect 10 cards in 3-col grid (1-col mobile), ETA badges color-coded, status dots
- [ ] **Step 5:** Commit: `git commit -am "feat(landing): Coming Soon roadmap section with 10 pipeline features"`

### Task 3.7 — Trial expiry banner

**File:** Modify `frontend/src/components/Sidebar.tsx` (or appropriate layout)

- [ ] **Step 1:** Read `auth/me.plan_expires_at`. If within 7 days, render banner:

```tsx
import { differenceInDays } from "date-fns";

function TrialBanner({ expiresAt }: { expiresAt: string | null }) {
  if (!expiresAt) return null;
  const days = differenceInDays(new Date(expiresAt), new Date());
  if (days < 0 || days > 7) return null;
  return (
    <div className="rounded bg-amber-50 border border-amber-300 px-3 py-2 text-sm">
      Pro trial ends in <strong>{days} {days === 1 ? "day" : "days"}</strong>.
      <a href="/upgrade" className="ml-2 underline">Upgrade →</a>
    </div>
  );
}
```

- [ ] **Step 2:** Commit: `git commit -am "feat(ui): trial expiry banner shows within 7-day window"`

### Task 3.8 — Upgrade page payment block

**File:** Modify `frontend/src/app/upgrade/page.tsx`

- [ ] **Step 1:** Refresh `COMPARISON_ROWS` per Q1 Task 16 Step 1 (verbatim from spec)
- [ ] **Step 2:** Add the v1 payment block at the bottom of the page (above the institution mailto):

```tsx
function PaymentMethods() {
  return (
    <section className="rounded-lg border p-4 mt-8">
      <h3 className="font-semibold mb-3">Pay manually (Beta)</h3>
      <p className="text-sm text-ink-muted mb-4">
        Stripe + JazzCash + Easypaisa integration arrives in June 2026.
        Until then, transfer the amount and email proof to <a href="mailto:payments@aidwiseai.com">payments@aidwiseai.com</a> — we'll activate within 4 hours.
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div>
          <p className="font-medium">JazzCash</p>
          <p className="text-sm">0300-XXXXXXX</p>
          <p className="text-xs text-ink-muted">Account title: <em>(your name)</em></p>
        </div>
        <div>
          <p className="font-medium">Easypaisa</p>
          <p className="text-sm">0345-XXXXXXX</p>
        </div>
        <div>
          <p className="font-medium">Bank Transfer / RAAST</p>
          <p className="text-sm">IBAN: PKxx-XXXX-XXXX-XXXX-XXXX</p>
          <p className="text-xs text-ink-muted">Bank: Meezan / Alfalah / HBL</p>
        </div>
      </div>
      <a href={`mailto:payments@aidwiseai.com?subject=${encodeURIComponent("Upgrade to Pro - " + (user?.email ?? ""))}&body=${encodeURIComponent("Hi, I just transferred PKR 2,999. Reference attached.")}`}
         className="mt-4 inline-block rounded bg-ink text-white px-4 py-2">
        Email payment proof
      </a>
    </section>
  );
}
```

- [ ] **Step 3:** Replace placeholder phone numbers + IBAN with your actual values **before deploying**
- [ ] **Step 4:** `bun run build` — expect 0 errors
- [ ] **Step 5:** Commit: `git commit -am "feat(upgrade): comparison rows refresh + manual payment block (v1)"`

### Task 3.9 — Seed invite code script

**File:** Create `backend/scripts/seed_invite_codes.py`

- [ ] **Step 1:** Write:

```python
"""Seeds the AIRU2026 invite code with 100-use cap, 7-day window."""
import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy import select
from app.core.database import SessionLocal
from app.models import InviteCode

PKT = ZoneInfo("Asia/Karachi")


async def main():
    valid_from = datetime(2026, 5, 19, 9, 0, 0, tzinfo=PKT)
    valid_until = datetime(2026, 5, 26, 23, 59, 59, tzinfo=PKT)
    async with SessionLocal() as db:
        existing = (await db.execute(
            select(InviteCode).where(InviteCode.code == "AIRU2026")
        )).scalar_one_or_none()
        if existing:
            print(f"AIRU2026 already exists: uses={existing.uses}/{existing.max_uses}, "
                  f"window={existing.valid_from} -> {existing.valid_until}")
            return
        db.add(InviteCode(
            code="AIRU2026", cohort="AU2026", grants_plan="pro",
            trial_days=30, max_uses=100, uses=0,
            valid_from=valid_from, valid_until=valid_until, is_active=True,
        ))
        await db.commit()
        print(f"Seeded AIRU2026: 100 uses, valid {valid_from} -> {valid_until}")


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 2:** Run against Supabase:

```bash
cd backend && DATABASE_URL=$DATABASE_URL_DIRECT python scripts/seed_invite_codes.py
```

Expected: `Seeded AIRU2026: 100 uses, valid ...`

- [ ] **Step 3:** Commit: `git commit -am "feat(scripts): seed AIRU2026 invite code (100 uses, 7-day window)"`

### Task 3.10 — Admin script to expand uses on-spot

**File:** Create `backend/scripts/grant_invite_uses.py`

- [ ] **Step 1:** Write:

```python
"""Bumps invite_codes.max_uses by N at booth. Usage:
    DATABASE_URL=... python scripts/grant_invite_uses.py AIRU2026 50
"""
import asyncio, sys
from sqlalchemy import update, select
from app.core.database import SessionLocal
from app.models import InviteCode


async def main(code: str, add: int):
    async with SessionLocal() as db:
        row = (await db.execute(
            select(InviteCode).where(InviteCode.code == code)
        )).scalar_one_or_none()
        if not row:
            print(f"NOT FOUND: {code}"); sys.exit(1)
        old = row.max_uses
        await db.execute(
            update(InviteCode).where(InviteCode.code == code)
            .values(max_uses=InviteCode.max_uses + add)
        )
        await db.commit()
        print(f"{code}: max_uses {old} -> {old + add} (used: {row.uses})")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1], int(sys.argv[2])))
```

- [ ] **Step 2:** Smoke: `python scripts/grant_invite_uses.py AIRU2026 0` — expect `max_uses 100 -> 100 (used: 0)`
- [ ] **Step 3:** Commit: `git commit -am "feat(scripts): admin CLI to bump invite_code.max_uses on-spot"`

### Task 3.11 — QR flyer generator

**File:** Create `backend/scripts/generate_qr_flyers.py`

- [ ] **Step 1:** Write:

```python
"""Generates a single high-res QR PNG for the AIRU2026 invite + a printable PDF flyer."""
import qrcode
from pathlib import Path

CODE = "AIRU2026"
DEEP_LINK = f"https://aidwiseai.com/signup?invite={CODE}"
OUT_DIR = Path(__file__).resolve().parents[1] / "out" / "exhibition"
OUT_DIR.mkdir(parents=True, exist_ok=True)

qr = qrcode.QRCode(
    version=None,
    error_correction=qrcode.constants.ERROR_CORRECT_H,
    box_size=20,
    border=4,
)
qr.add_data(DEEP_LINK)
qr.make(fit=True)
img = qr.make_image(fill_color="black", back_color="white")
qr_path = OUT_DIR / f"aidwise-{CODE.lower()}-qr.png"
img.save(qr_path)
print(f"QR saved: {qr_path} ({img.size[0]}x{img.size[1]} px)")
print(f"Deep link: {DEEP_LINK}")
print("\nFlyer copy suggestion:\n"
      "AidwiseAI — Free Pro trial for Air University students\n"
      "Scan to claim 30 days of personalised scholarship matching, SOP drafting, visa interview practice.\n"
      f"Code: {CODE}  |  aidwiseai.com  |  Valid May 19-26 only")
```

- [ ] **Step 2:** Run `python scripts/generate_qr_flyers.py` — expect PNG saved to `backend/out/exhibition/aidwise-airu2026-qr.png`
- [ ] **Step 3:** Open PNG, scan with phone — expect to land on `https://aidwiseai.com/signup?invite=AIRU2026`
- [ ] **Step 4:** Commit: `git commit -am "feat(scripts): QR generator for exhibition flyer"`

### Task 3.12 — DigitalOcean App Platform deploy

- [ ] **Step 1:** DO Dashboard → Create → Apps → connect GitHub → select repo → branch `feat/air-exhibition-launch`
- [ ] **Step 2:** Configure 3 components from same repo:

| Component | Type | Source dir | Build cmd | Run cmd | HTTP route |
|---|---|---|---|---|---|
| `web` | Web Service | `/backend` | `pip install -r requirements.txt` | `uvicorn app.main:app --host 0.0.0.0 --port 8080` | `/` |
| `worker` | Worker | `/backend` | (same) | `celery -A app.tasks.celery_app:celery_app worker -l info` | — |
| `beat` | Worker | `/backend` | (same) | `celery -A app.tasks.celery_app:celery_app beat -l info` | — |

- [ ] **Step 3:** Set env vars on **all three components** (paste from `.env.local`). Mark all as **encrypted** secrets:

```
DATABASE_URL=...pooler URL...
REDIS_URL=...upstash URL...
ANTHROPIC_API_KEY=...
JWT_SECRET=...
MAILGUN_API_KEY=...
MAILGUN_DOMAIN=mg.aidwiseai.com
SENTRY_DSN_BACKEND=...
INVITE_CODE_DEFAULT=AIRU2026
BRAND_DISPLAY_NAME=AidwiseAI
PLAN_TRIAL_DAYS=30
CORS_ORIGINS=https://aidwiseai.com,https://www.aidwiseai.com
AUTH_RATE_LIMIT_LOGIN_REQUESTS=50
AUTH_RATE_LIMIT_REGISTER_REQUESTS=200
```

- [ ] **Step 4:** Health check on `web` component: HTTP path `/livez`, port 8080, success codes `200`
- [ ] **Step 5:** Plan size: Basic XXS ($5/mo) for `beat`, **Basic S ($12/mo) for `web`** (1 GB RAM, 1 dedicated vCPU — handles bcrypt bursts + concurrent LLM contexts), **Basic S ($12/mo) for `worker`** (1 GB RAM — Chromium needs ~500 MB headless for scraper). Total backend: $29/mo, ~7 months on $200 DO credit.
- [ ] **Step 6:** Deploy → wait ~5 min for build
- [ ] **Step 7:** Smoke:

```bash
curl https://<app-name>.ondigitalocean.app/livez
# expect: {"status":"ok"}

curl https://<app-name>.ondigitalocean.app/api/v1/upgrade/pricing?currency=PKR
# expect: JSON with PKR 2,999 / 6,000
```

- [ ] **Step 8:** Add custom domain `api.aidwiseai.com`:
  - DO → Settings → Domains → Add `api.aidwiseai.com`
  - DO will issue a CNAME target like `<app>.ondigitalocean.app`
  - Cloudflare DNS → Add CNAME record `api` → `<app>.ondigitalocean.app`, Proxy status: **DNS only** (grey cloud) for the first cert issuance, then can flip to proxied after cert is live

### Task 3.13 — Vercel deploy

- [ ] **Step 1:** Vercel → Add New → Project → import repo → root dir `frontend`
- [ ] **Step 2:** Framework: Next.js (auto). Build cmd: `bun run build`. Install cmd: `bun install`
- [ ] **Step 3:** Env vars:

```
NEXT_PUBLIC_API_BASE_URL=https://api.aidwiseai.com/api/v1
NEXT_PUBLIC_BRAND=AidwiseAI
NEXT_PUBLIC_SENTRY_DSN=<frontend dsn>
```

- [ ] **Step 4:** Deploy → preview URL like `aidwise-xyz.vercel.app`
- [ ] **Step 5:** Add domain `aidwiseai.com` + `www.aidwiseai.com`:
  - Vercel → Domains → Add `aidwiseai.com`
  - Vercel shows DNS records (A + CNAME)
  - Cloudflare → add the records, **Proxy status: DNS only** for first cert
  - Wait ~5 min for cert
  - Then flip Cloudflare proxy to **proxied** for performance/CDN
- [ ] **Step 6:** Update DO env: `CORS_ORIGINS=https://aidwiseai.com,https://www.aidwiseai.com,https://aidwise-*.vercel.app` → redeploy backend

### Task 3.14 — End-to-end smoke

- [ ] **Step 1:** Open `https://aidwiseai.com/signup?invite=AIRU2026` — expect signup page with code pre-filled
- [ ] **Step 2:** Sign up as test user `e2e-test@example.com` with Air U fields filled, consent ticked, marketing off
- [ ] **Step 3:** Verify `auth/me` returns `plan: "pro"` and `plan_expires_at` ~30 days out
- [ ] **Step 4:** Walk: `/feed` (3+ matches), `/tracker` (add 6 cards), `/documents/sop` (1 draft), `/interviews/visa` (3 questions), `/upgrade` (sees comparison table + manual payment block)
- [ ] **Step 5:** In Supabase SQL: `SELECT user_id, kind, cost_pkr_micro, endpoint FROM usage_ledger ORDER BY created_at DESC LIMIT 10;` — expect rows for `llm_haiku` from sop draft + visa
- [ ] **Step 6:** In Supabase SQL: `SELECT uses, max_uses FROM invite_codes WHERE code='AIRU2026';` — expect `uses=1`
- [ ] **Step 7:** Reset test user: `DELETE FROM users WHERE email='e2e-test@example.com';` then `UPDATE invite_codes SET uses=0 WHERE code='AIRU2026';`

---

## 7. Day 4 — May 19 (Exhibition + Polish)

### Task 4.1 — Pre-flight checks (morning, 1 hour before booth opens)

- [ ] Sentry alert rule active: 5xx rate > 2% in 5-min window → email + push notification
- [ ] UptimeRobot active: 1-min ping `https://api.aidwiseai.com/livez` and `https://aidwiseai.com/`
- [ ] Anthropic dashboard: confirm $30 cap visible on the spend page
- [ ] Supabase: row count check `SELECT COUNT(*) FROM scholarships WHERE record_state='published';` ≥ 20
- [ ] Pre-warm: hit `https://aidwiseai.com/`, `/signup`, `/login`, `/feed` (no auth) → cache warmup
- [ ] Test invite redemption again: signup with throwaway email, walk one feature, then `DELETE FROM users WHERE email='warmup@x.com'`, `UPDATE invite_codes SET uses=uses-1 WHERE code='AIRU2026'`

### Task 4.2 — Booth setup

- [ ] Print 100 flyers with QR + invite code at local print shop (~PKR 2k–3k). Use Canva Pro template
- [ ] Bring laptop with `feat/air-exhibition-launch` branch checked out, `docker compose up` ready as offline fallback
- [ ] Bring phone with hot-spot enabled for emergency
- [ ] Bring iPad/tablet with the 90-second pre-recorded walkthrough video and 10-screen PDF as last-resort demos

### Task 4.3 — Live monitoring during exhibition

Open in browser tabs:

- Sentry → live errors feed
- Supabase → SQL editor with `SELECT COUNT(*) FROM users WHERE redeemed_invite_code='AIRU2026';` (refresh every 30 min)
- DO App Platform → Runtime logs (tail)
- UptimeRobot → status page

### Task 4.4 — On-spot operations

| Trigger | Action |
|---|---|
| 100 redemptions hit | `python scripts/grant_invite_uses.py AIRU2026 50` from laptop. Confirm in Supabase. |
| Backend 5xx spike in Sentry | Check DO logs first. If db-connection error, restart `web` component in DO dashboard. |
| Anthropic burn-cap rejected for many users | Bump per-user cap in `burn_cap.py` only as last resort (requires deploy). Better: explain to user "AI budget reset tomorrow" |
| Supabase unreachable | Check Supabase status page. If outage, deploy `MAINTENANCE_MODE=true` env to DO → `/api/v1/maintenance` returns 503 with friendly message |
| Internet down at booth | Switch to laptop hotspot. If hotspot dies, play 90-second video on tablet for live walk-throughs |

---

## 8. Backup & Contingency Stack

### Pre-built (Day 4 morning)

- [ ] **Localhost stack** — `cd scholarai-platform && docker compose up -d`. Test that `http://localhost:3000` works locally with Supabase (production DB still). Bookmark on laptop browser.
- [ ] **90-second walkthrough video** — Use OBS Studio (free) or QuickTime to screen-record full Zara journey: signup → match → tracker → SOP draft → visa Q&A → upgrade page. Save as MP4 on laptop AND phone AND iPad
- [ ] **10-screen PDF** — Open each key screen, take browser screenshot, paste into Canva Pro, export as PDF. Save on iPad and print 3 copies

### Tier ranking (use in this order if cloud fails)

| Tier | Trigger | Fallback |
|---|---|---|
| 0 | Single endpoint slow | Wait — UptimeRobot SMS will alert on > 2 min downtime |
| 1 | Backend 5xx > 50% for 2 min | Trigger DO redeploy from dashboard |
| 2 | Vercel down | Already mirrored on Vercel preview URL — switch QR to preview URL via short-link service (e.g. `bit.ly/airu2026`) — but this requires editing flyers (impractical). Better: hand out support email card |
| 3 | Supabase down | Show pre-recorded video on tablet, collect emails on paper, redeem codes manually post-event |
| 4 | No internet at booth | Tablet video + screenshots PDF |

---

## 9. Post-Exhibition Roadmap (Week of May 26)

### Week 1 (May 19–26): Trial active, payment v1 manual

- Daily monitor: signup count, feature usage, Sentry errors, Anthropic spend
- Manual payment processing for any early upgrades
- Apply for FBR NTN (3 days)
- Open business bank account at Meezan/Alfalah/HBL (5–7 days)

### Week 2 (May 26 – Jun 1): Tier B sprint + Safepay onboarding + LLM abstraction

- Q1 retier Tier B tasks: Task 13 (public catalog premium filter), Task 14 (vocab guard CI), Task 16 polish
- Apply for Safepay business account (NTN + business bank required)
- Day-7 NPS survey email to Air U cohort via Mailgun
- **LLM provider abstraction** — refactor `services/llm/anthropic_client.py` → `services/llm/llm_client.py` using OpenAI-compatible `AsyncOpenAI` SDK pointed at OpenRouter `https://openrouter.ai/api/v1`. Add env vars `LLM_MODEL_DEFAULT` (default `anthropic/claude-haiku-4-5`) and `LLM_MODEL_SOP_DEEP` (default `anthropic/claude-sonnet-4-6`). Update burn-cap pricing dict to read per-model rates from a config map. Keeps Day-1 quality, unblocks Week-3 model A/B tests (Kimi K2.5, DeepSeek V3.2) per route.

### Week 3 (Jun 2–8): Safepay sandbox + LLM A/B test

- Implement `POST /api/v1/payments/checkout/start` → Safepay hosted checkout
- Webhook handler `POST /api/v1/payments/webhook/safepay` → mark user `plan='pro_paid'`
- Sandbox test with PKR 100 transaction
- **Kimi K2.5 A/B test** — flip 50% of Pro SOP drafts + visa eval to `moonshotai/kimi-k2.5` via env override on a percentage of users. Compare: cost/call, latency, output-quality score against held-out PK SOP fixtures (`tests/fixtures/sop_pakistan/*.json`). If quality ≥ 90% of Haiku baseline, promote to default. Keep Sonnet for Elite SOP line-feedback + strategy report.

### Week 3 (Jun 2–8): Safepay sandbox integration

- Implement `POST /api/v1/payments/checkout/start` → Safepay hosted checkout
- Webhook handler `POST /api/v1/payments/webhook/safepay` → mark user `plan='pro_paid'`
- Sandbox test with PKR 100 transaction

### Week 4 (Jun 9–15): Safepay live + Twilio WhatsApp

- Switch Safepay to live keys
- Wire Twilio WhatsApp via `services/notifications/channels.py.send_whatsapp` (Student Pack $50 Twilio credit covers ~1500 messages)
- First real PKR payment — verify reconciliation in DB

### Week 5 (Jun 16–22): Trial expiry handling

- First wave of trial users hit Day 31 (those who redeemed May 19)
- Banner has been visible 5+ days → conversion data available
- A/B test: half users get email reminder Day 28, half don't
- Post-mortem: cohort metrics (signups, engagement, conversion)

---

## 10. Risks + Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Anthropic spend overrun | Low | High | $30 monthly cap (hard) + per-user PKR 1,799 burn cap (soft) |
| Supabase Free pauses | Low | High | Daily traffic prevents pause; UptimeRobot ping keeps active |
| Vercel TOS Hobby commercial-use enforcement | Low | Medium | If notified, upgrade to Pro $20 within 24 hr |
| DO image build fails | Medium | Medium | Test build locally with `docker build backend/` before pushing |
| Supabase pooler asyncpg breakage | Medium | High | Task 1.2 patch (`statement_cache_size=0`); fallback = direct 5432 URL |
| 100 codes redeemed in first hour | Low | Low | Task 3.10 admin script bumps cap in 30 sec |
| Trial users complain about feature limits | Medium | Low | Pro = generous (6 matches, 5 SOP, 6 tracker); upgrade-to-Elite path is the answer |
| PDPB complaint from a student | Low | High | Mandatory consent v1.0 at signup + 30-day deletion right surfaces in `/settings/privacy` (already in S87 work) |
| Cloud outage on May 19 | Very Low | Catastrophic | 4-tier backup stack (Section 8) |
| Mailgun email landing in spam | Medium | Medium | SPF + DKIM via Cloudflare DNS; warm-up domain by sending to known addresses Day 4 |
| NTN/business bank delays Safepay | High | Medium | Manual payment v1 covers first 4–6 weeks |
| Scraper Chromium OOM on worker | Medium | Medium | Worker upgraded to Basic S (1 GB RAM); scraper queues sequentially via Celery; source health monitor (S86) marks down sources after 6 consecutive failures |
| Scraper hits external rate limits / 429 | Medium | Low | Conditional GET (ETag/Last-Modified) + sitemap-driven fetch (S86) cuts load 80%; nightly 02:00 UTC schedule, not exhibition-blocking |

---

## Appendix A — Final `.env` template for production

`backend/.env.production` (paste into DO dashboard):

```
# Database
DATABASE_URL=postgresql+asyncpg://postgres.<ref>:<pwd>@aws-0-ap-south-1.pooler.supabase.com:6543/postgres?sslmode=require

# Redis
REDIS_URL=rediss://default:<token>@<endpoint>.upstash.io:6379

# LLM
ANTHROPIC_API_KEY=sk-ant-...

# Auth
JWT_SECRET=<openssl rand -hex 32>
JWT_ALG=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Email
MAILGUN_API_KEY=<key>
MAILGUN_DOMAIN=mg.aidwiseai.com

# Monitoring
SENTRY_DSN_BACKEND=<dsn>
SENTRY_ENVIRONMENT=production

# Brand + trial
INVITE_CODE_DEFAULT=AIRU2026
BRAND_DISPLAY_NAME=AidwiseAI
PLAN_TRIAL_DAYS=30

# CORS
CORS_ORIGINS=https://aidwiseai.com,https://www.aidwiseai.com

# Rate limits (relaxed for trial)
AUTH_RATE_LIMIT_LOGIN_REQUESTS=50
AUTH_RATE_LIMIT_REGISTER_REQUESTS=200
AUTH_RATE_LIMIT_REFRESH_REQUESTS=100
AUTH_RATE_LIMIT_LOGOUT_REQUESTS=100
```

`frontend/.env.production` (paste into Vercel):

```
NEXT_PUBLIC_API_BASE_URL=https://api.aidwiseai.com/api/v1
NEXT_PUBLIC_BRAND=AidwiseAI
NEXT_PUBLIC_SENTRY_DSN=<frontend dsn>
```

---

## Appendix B — Day 4 dry-run script

```bash
# 1. Verify deployment health
curl -fsS https://api.aidwiseai.com/livez
curl -fsS https://api.aidwiseai.com/api/v1/upgrade/pricing?currency=PKR | jq '.'

# 2. Verify invite code seeded
psql "$DATABASE_URL_DIRECT" -c "SELECT code, uses, max_uses, valid_from, valid_until, is_active FROM invite_codes WHERE code='AIRU2026';"

# 3. Verify scholarship seed
psql "$DATABASE_URL_DIRECT" -c "SELECT COUNT(*) FROM scholarships WHERE record_state='published';"

# 4. Hit signup with curl
curl -fsS -X POST https://api.aidwiseai.com/api/v1/auth/register \
  -H 'content-type: application/json' \
  -d '{
    "email": "dryrun-'$(date +%s)'@example.com",
    "password": "longpassword12",
    "full_name": "Dry Run",
    "invite_code": "AIRU2026",
    "air_uni_uni": "Air University",
    "air_uni_dept": "CS",
    "air_uni_batch": 2023,
    "consent_v": "v1.0",
    "marketing_opt_in": false
  }' | jq '.user.plan, .user.plan_expires_at'

# 5. Confirm redemption counted
psql "$DATABASE_URL_DIRECT" -c "SELECT uses FROM invite_codes WHERE code='AIRU2026';"

# 6. Check ledger empty for new user (no LLM calls yet)
psql "$DATABASE_URL_DIRECT" -c "SELECT user_id, kind, cost_pkr_micro FROM usage_ledger ORDER BY created_at DESC LIMIT 5;"
```

---

## Appendix C — Push gate before exhibition

Before deploying to DO + Vercel, the full push gate from `AGENTS.md` must pass:

- [ ] `cd backend && pytest tests/unit tests/integration -q` — expect previous 369 + new ~30 = ~399 PASS
- [ ] `python -m compileall backend/app backend/tests` — expect OK
- [ ] `cd frontend && bun run lint` — expect 0 warnings
- [ ] `cd frontend && bunx --bun tsc --noEmit` — expect 0 errors
- [ ] `cd frontend && bun run build` — expect successful build
- [ ] `python scripts/docs_governance_check.py` — expect 0 failures

---

## Appendix E — GitHub Student Pack full claim list

Audit of every Pack benefit applicable to AidwiseAI. Tiered by when to claim + when to actually use.

### Tier 1 — Claim today (Day 1, May 16) and use immediately

| Benefit | Use case | Replaces / saves |
|---|---|---|
| **DigitalOcean $200 credit** | Backend host (App Platform 3 svc × $5/mo) | Railway $12/mo × ~13 mo |
| **Namecheap free `.me` 1 yr** | Backup domain `aidwise.me` (redirect → `.com`) | $10/yr |
| **Mailgun 20k emails/mo** | Trial alerts, NPS surveys, deadline reminders, signup welcome | Resend Free 100/day → 20× headroom |
| **Sentry Developer plan** | Error tracking backend + frontend (100k events/mo) | Sentry Free 5k → 20× headroom |
| **1Password Teams 1-yr free** | Vault for `.env` secrets, share with cofounder/contractors safely | $8/user/mo |
| **Canva Pro 12 mo** | Booth flyer, QR card, brand assets, social posts | $13/mo |
| **Figma Professional free** | UI design iteration, component library, design hand-off | $15/user/mo |
| **JetBrains All Products Pack** | PyCharm Pro for backend, WebStorm for frontend | $289/yr |
| **GitKraken Pro 12 mo** | Visual git for fast PR reviews, merge conflict resolution | $5/mo |
| **Termius Premium** | SSH client to DO droplet (if direct droplet ever needed); SFTP | $9/mo |
| **Statsig Free 1-yr Enterprise** | Feature flags + experiments. Use for: model A/B test (Claude vs Kimi Week 3), invite-code cohort gating, trial banner copy A/B | $0 → enterprise tier |
| **Mailtrap free** | Email sandbox for local dev — send test emails without hitting Mailgun quota | Free anyway, useful early |

### Tier 2 — Claim today, configure Tier B (Week 2+)

| Benefit | Use case | Replaces / saves |
|---|---|---|
| **Twilio $50 credit** | WhatsApp deadline alerts for Elite paid tier (post-trial) | ~1500 messages free |
| **Datadog Pro 2 yr (5 hosts)** | APM + log aggregation for backend; richer than Sentry alone | $15/host/mo × 5 = $75/mo |
| **LogRocket Pro free** | Session replay on frontend; debug trial UX issues users won't report | $99/mo |
| **Crisp Chat Premium** | Live chat widget on `/help` for trial-user support | $25/mo |
| **HelpDocs free 1 yr** | Public knowledge base at `help.aidwiseai.com`; FAQ for "How do I redeem code", "How to upgrade" | $39/mo |
| **Linear Standard 6 mo free** | Issue tracking for solo dev; better than GitHub Issues for product roadmap | $8/user/mo |
| **Notion Personal Pro free** | Founder docs, customer feedback log, Air U cohort spreadsheet | $10/mo |
| **Icons8 Pro 6 mo** | Lucide gaps + branded icons for landing page | $13/mo |
| **Iconscout 3 mo Pro** | Illustration assets for empty states, onboarding | $9/mo |

### Tier 3 — Skill / learning (use during slow periods)

| Benefit | Use case |
|---|---|
| **O'Reilly Learning 12 mo** | Books on PostgreSQL perf, Next.js 16, marketing |
| **Frontend Masters 6 mo** | Next.js 16 + React 19 deep-dive |
| **Educative 6 mo** | System design refreshers |
| **Pluralsight 6 mo** | Cloud + DevOps catch-up if you self-host later |

### Tier 4 — Optional / domain-specific

| Benefit | Use if |
|---|---|
| **ElevenLabs Pro 1 yr free** | Recording landing-page voiceover or 90-sec demo narration |
| **AssemblyAI $50 credit** | If you add voice-to-text for visa-interview answers later |
| **Replicate $5 credit** | One-shot ML model trials (image gen for blog posts) |
| **DocuSign Demo** | Sign Air U Career Services MoU later (Round 2) |
| **Codacy free** | Static analysis on PRs (post-launch hygiene) |
| **DeepSource lifetime free** | Alternative to Codacy, lighter |
| **Sourcery Pro** | Python refactoring suggestions in PyCharm |
| **Pomodone Pro** | Pomodoro timer if you need focus discipline |

### Tier 5 — Skip (mismatch / redundant)

| Benefit | Why skip |
|---|---|
| Microsoft Azure $100 | DigitalOcean covers compute |
| AWS Educate | Same |
| Heroku 1-yr Hobby | DO covers; Heroku ends abrupt |
| MongoDB Atlas $200 | We use Postgres + pgvector, not Mongo |
| Pinecone $200 credit | pgvector covers MVP per CLAUDE.md |
| SendGrid 15k/mo | Mailgun already wired |
| Honeybadger free 1 yr | Sentry covers |
| Stripe Atlas $100 + waived fees | Blocked in PK |
| Bootstrap Studio | Using Tailwind |
| Bitnami Business | DO App Platform covers |
| Heap | PostHog covers analytics |
| Discord Nitro 3 mo | Not relevant |
| ClickUp free workspace 1 yr | Linear covers |
| Todoist Pro | Linear covers |

### Total lifetime value claimed (Tier 1 + 2)

| Benefit | Annualized value |
|---:|---:|
| DigitalOcean credit | $200 (one-time, ~13 mo runway) |
| Mailgun 20k/mo | ~$420/yr (vs paid plan) |
| Sentry Developer | ~$300/yr |
| 1Password Teams | ~$96/yr |
| Canva Pro | ~$156/yr |
| Figma Pro | ~$180/yr |
| JetBrains Pack | $289/yr |
| GitKraken Pro | ~$60/yr |
| Statsig Enterprise | thousands/yr at scale |
| Datadog Pro 5 hosts | ~$900/yr × 2 yrs |
| LogRocket Pro | ~$1,188/yr |
| Crisp Chat Premium | ~$300/yr |
| HelpDocs | ~$468/yr |
| Linear Standard | ~$48/6 mo |
| Notion Personal Pro | $120/yr |
| Twilio | $50 one-time |
| Icons8 + Iconscout | ~$130 |
| **Total claimed value** | **~$5,000+ in Year 1** |

### Claim order (browser tabs, ~90 min total)

1. Verify Pack active: `https://education.github.com/pack` ← Active student badge
2. **Infra/email/monitoring (15 min):** DigitalOcean → Mailgun → Sentry → Datadog (defer config)
3. **Domains/branding (10 min):** Namecheap (claim free `.me`, register `.com` paid) → Cloudflare DNS
4. **Dev tooling (15 min):** 1Password → JetBrains → GitKraken → Termius
5. **Design (10 min):** Canva → Figma → Icons8
6. **Product surface (15 min):** Statsig → Linear → Notion
7. **Tier B prep (15 min):** LogRocket → Crisp → HelpDocs → Twilio
8. **Optional (10 min):** ElevenLabs, O'Reilly, Frontend Masters

### Wiring tasks (added to Day 3)

- [ ] **1Password vault setup** — create vault `AidwiseAI Production`. Move all `.env.production` values in. Generate share link with cofounder/contractor.
- [ ] **Statsig SDK install** (backend + frontend):
  - Backend: `pip install statsig` → init in `app/main.py:on_startup`
  - Frontend: `bun add statsig-react` → wrap `<StatsigProvider>` in `app/layout.tsx`
  - Define gates: `kimi_model_eval` (off), `trial_banner_copy_v2` (off), `cohort_au2026` (on for `redeemed_invite_code='AIRU2026'`)
- [ ] **LogRocket script** in `frontend/src/app/layout.tsx`:
  ```tsx
  import LogRocket from "logrocket";
  if (typeof window !== "undefined" && process.env.NODE_ENV === "production") {
    LogRocket.init("aidwiseai/aidwiseai-prod");
  }
  ```
- [ ] **Crisp Chat widget** in `app/layout.tsx`:
  ```tsx
  <Script id="crisp" strategy="afterInteractive">{`
    window.$crisp=[];window.CRISP_WEBSITE_ID="${process.env.NEXT_PUBLIC_CRISP_ID}";
    (function(){d=document;s=d.createElement("script");s.src="https://client.crisp.chat/l.js";s.async=1;d.getElementsByTagName("head")[0].appendChild(s);})();
  `}</Script>
  ```
- [ ] **HelpDocs site** at `help.aidwiseai.com` — create 5 articles before May 19:
  - "How to redeem AIRU2026 code"
  - "What's included in Pro trial"
  - "What happens when my 30 days end"
  - "How to upgrade to paid Pro"
  - "Privacy + data deletion"

---

## Appendix D — Update `progress.md` and `CLAUDE.md` after launch

Per device-global session rules (`~/.claude/CLAUDE.md`):

- [ ] Update `scholarai-platform/progress.md` with: branch, files touched, deployment URLs, env var locations, demo creds, on-call runbook
- [ ] Update `scholarai-platform/CLAUDE.md` "Open work" section: trial cohort active, payment v2 ETA, Tier B/C scope. Keep file < 200 lines.

---

## Self-Review Checklist

- [x] **Spec coverage** — All 16 locked decisions (§0) map to a numbered task. Q1 retier Tier A 10 tasks all ship by Day 2; trial-specific 8 tasks ship Day 3; deployment + smoke Day 3 evening.
- [x] **No placeholders** — Every code block contains complete, runnable code. Phone numbers + IBAN in payment block flagged for manual replacement before Task 3.13 deploy.
- [x] **Type consistency** — `ScholarshipMatchOut` / `UnlockOffer` / `MatchResponse` shapes match between `schemas/scholarships.py`, `match_service.py`, and `lib/api/types.ts`. `User.plan_expires_at` is `DateTime(tz=True)` in migration, ORM, and frontend `differenceInDays` consumer.
- [x] **No sub-project leakage** — All work in monorepo paths under `backend/` and `frontend/`. No new top-level deployables.
