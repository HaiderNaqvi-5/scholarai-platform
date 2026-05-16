# progress.md — Air University Exhibition Backend Sprint

**Date:** 2026-05-16
**Branch:** `feat/pakistan-frontend-pass`
**Goal:** Land backend prerequisites for the May-19 Air University exhibition trial launch (Pro plan via shared invite code `AIRU2026`, 100 redemptions, 30-day per-user trial). Front-end work is queued separately in `Front-upgrade.md` §16.

## This session — backend bundle (post Q1 retier)

Q1 retier (Tasks 1–17) already shipped earlier today; see prior `progress.md` rev in git history for the SHA table. This session layers the trial-launch-specific work on top.

### Items completed

| # | Work | Files |
|---|---|---|
| R1 | Migration `0026` invite_codes + Air U cols + redeemed_invite_code (UUID FK style; reuses existing `User.marketing_consent` rather than duplicating it) | `backend/alembic/versions/20260516_0026_invite_codes_and_trial.py` |
| R2 | `InviteCode` ORM + 4 new `User` columns (`air_uni_uni`, `air_uni_dept`, `air_uni_batch`, `redeemed_invite_code`) + export | `backend/app/models/models.py`, `backend/app/models/__init__.py` |
| R3 | (verified — already in HEAD from prior session) `_redeem_invite_code` + Air U capture + Pro grant + `plan_expires_at = now + trial_days` in `AuthService.register`, plus `UserCreate` / `UserResponse` schema extensions | `backend/app/services/auth/service.py`, `backend/app/schemas/auth.py`, `backend/tests/unit/test_auth_service.py` (15 PASS) |
| R4 | Daily 02:00 UTC `expire_trial_plans` Celery beat task — UPDATE users SET plan='free', plan_expires_at=NULL WHERE plan_expires_at < now AND plan != 'free' | `backend/app/tasks/trial_tasks.py`, `backend/app/tasks/celery_app.py` (beat schedule + include), `backend/tests/unit/test_trial_tasks.py` (4 PASS) |
| R5 | Mailgun `send_email` with httpx POST; graceful log-only fallback when MAILGUN_API_KEY / MAILGUN_DOMAIN unset. Optional `subject` kwarg preserves the existing `(user, message)` caller signature | `backend/app/services/notifications/channels.py`, `backend/app/core/config.py` (MAILGUN_*, BRAND_DISPLAY_NAME, EMAIL_FROM_LOCALPART) |
| R9 | Dockerfile bakes Chromium for the scraper worker via `playwright install --with-deps chromium`, with `PLAYWRIGHT_BROWSERS_PATH=/opt/playwright-browsers` chowned to appuser | `backend/Dockerfile` |
| R10 | Three CLI scripts: seed `AIRU2026` (100 uses, May 19 09:00 → May 26 23:59 PKT), bump max_uses on-spot, and generate 900×900 QR PNG of `https://aidwiseai.com/signup?invite=AIRU2026` | `backend/scripts/seed_invite_codes.py`, `backend/scripts/grant_invite_uses.py`, `backend/scripts/generate_qr_flyers.py` |
| deps | Added `anthropic==0.39.0`, `qrcode[pil]==7.4.2`, `sentry-sdk[fastapi]==2.18.0` to `requirements.txt` | `backend/requirements.txt` |

### Push gate

- `python -m compileall app tests` — OK
- `pytest tests/unit tests/integration -q` — **454 passed, 1 xpassed, 8 warnings, 90 s**
- Migration `0026` applied locally; `alembic current` → `20260516_0026`
- Scripts: `seed_invite_codes.py` and `grant_invite_uses.py` both round-tripped against local DB; `generate_qr_flyers.py` produced 900×900 PNG

### Pending (sequenced)

| When | Owner | Work |
|---|---|---|
| May 17 | Ops | Apply 0026 + seed AIRU2026 + deploy DigitalOcean App Platform (3 services: web Basic S, worker Basic S with Chromium, beat Basic XXS), Cloudflare DNS for `api.aidwiseai.com`, Mailgun DKIM+SPF, Sentry backend init, Anthropic Tier-2 prepay ($40) |
| May 18 | Frontend | All of `Front-upgrade.md` §16 Tasks 16.1–16.11 (gold token, brand hotpatch ×5 files, ComingSoon, signup invite + consent, TrialBanner, PaymentMethods, Sentry/LogRocket/Statsig/Crisp wiring, pre-deploy gate, Vercel deploy with `aidwiseai.com`) |
| May 19 | Founder | Dry run, print 100 flyers (Canva Pro template), exhibition booth open 09:00 PKT |

### Files touched

```
backend/Dockerfile
backend/alembic/versions/20260516_0026_invite_codes_and_trial.py          (NEW)
backend/app/core/config.py
backend/app/models/__init__.py
backend/app/models/models.py
backend/app/services/notifications/channels.py
backend/app/tasks/celery_app.py
backend/app/tasks/trial_tasks.py                                          (NEW)
backend/requirements.txt
backend/scripts/generate_qr_flyers.py                                     (NEW)
backend/scripts/grant_invite_uses.py                                      (NEW)
backend/scripts/seed_invite_codes.py                                      (NEW)
backend/tests/unit/test_trial_tasks.py                                    (NEW)
```

### Commands to resume

```bash
# Local
cd backend && alembic current                          # expect 20260516_0026
python -m pytest tests/unit tests/integration -q       # expect 454+ PASS
python scripts/seed_invite_codes.py                    # idempotent
python scripts/generate_qr_flyers.py                   # outputs out/exhibition/

# Supabase production
DATABASE_URL='postgresql+asyncpg://postgres:<pw>@db.<ref>.supabase.co:5432/postgres?sslmode=require' \
    alembic upgrade head
DATABASE_URL='...' python scripts/seed_invite_codes.py

# Smoke deployed backend
curl https://api.aidwiseai.com/livez
curl https://api.aidwiseai.com/api/v1/upgrade/pricing?currency=PKR
```

### Notes / decisions

- `users.marketing_consent` (already shipped) covers the marketing-opt-in toggle. Migration 0026 was revised mid-flight to drop a duplicate `marketing_opt_in` column.
- Auth service `_redeem_invite_code` uses `with_for_update()` so two concurrent signups racing the last slot can't both succeed.
- Trial expiry cron writes via a single UPDATE — idempotent, safe to re-run within the same UTC day.
- Mailgun send_email returns True on log-only fallback so callers stay deterministic when MAILGUN_API_KEY / MAILGUN_DOMAIN are absent in dev / CI.
- Dockerfile keeps `--no-install-recommends apt` lean except for the Playwright `--with-deps` install which is necessary for headless Chromium. Final image ~1.2 GB; fits Basic S (1 GB RAM dedicated) on DO App Platform.
