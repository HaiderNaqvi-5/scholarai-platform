# progress.md — 2026-05-18 (S20 Security hardening pass)

**Date:** 2026-05-18 (S89 + S89.1 already in git)
**Branch:** `feat/s89-premium-cultural`
**Alembic head:** `20260516_0026 (head)` — backend schema unchanged
**Commits this session:** S20 security hardening commit on top of `41f3793` (S89.1) and `99cc4c7` (landing polish) and `cb9cfbb` (S89 base)

## Tasks completed this session (S20)

Closes P0 + P1 items from `SECURITY_AUDIT.md`. **396 unit + 63 integration backend tests pass.** Frontend lint + tsc + build + emoji-grep green across 123 files. Backend `create_app()` boots clean (112 routes) with Sentry stub.

### P0 (HIGH severity)

**S1 — Backend SecurityHeadersMiddleware + TrustedHost.** `app/main.py` mounts a new `SecurityHeadersMiddleware` after CORS so every response (including CORS preflights) carries:
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Cross-Origin-Opener-Policy: same-origin`
- `Cross-Origin-Resource-Policy: same-site`
- `Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=(), usb=()`
- `Content-Security-Policy: default-src 'none'; frame-ancestors 'none'; base-uri 'none'` (JSON API surface)

`TrustedHostMiddleware` mounted only when `ALLOWED_HOSTS` setting is non-empty (skips dev, enforced in prod).

**S2 — Frontend next.config.ts headers.** `next.config.ts:headers()` returns the same header set per response on every route. CSP allows `NEXT_PUBLIC_API_BASE_URL` host for `connect-src`; allows `'unsafe-inline'` for `style-src` because Tailwind 4 ships generated `<style>` blocks; production drops `'unsafe-eval'` from `script-src`.

**S3 — `AUTO_SEED_DEMO_DATA` default flipped to `False`.** Prod assertion in `validate_production_settings` already rejects `True`. Demo seed must now be explicitly opted-in even in dev. `.env.example` flag still reads `true` w/ explicit comment that prod assertion rejects it.

**S4 — Boot secret assertions strengthened.** New `OPENSEARCH_PASSWORD` setting + prod assertion that rejects the docker-compose default (`ScholarAI_Secure_123!`) and common weak values. `ALLOWED_HOSTS` becomes required-non-empty in prod via the same assertion; wildcards forbidden. Existing `SECRET_KEY` / Neo4j / DB / Redis / Celery checks unchanged.

**S5 — CORS prod hardening.** `validate_production_settings` rejects any `CORS_ORIGINS` entry containing `localhost` or `127.0.0.1` when `ENVIRONMENT in {production, staging}`.

### P1 (MED severity)

**S7 — `ProxyHeadersMiddleware`.** `uvicorn.middleware.proxy_headers.ProxyHeadersMiddleware` mounts when `TRUSTED_PROXY_HOPS > 0`. Rate-limiter Redis keys + Sentry breadcrumb + account-lockout email key now reflect real client IP behind nginx / Cloudflare / caddy.

**S8 — Account lockout.** New `backend/app/core/account_lockout.py` Redis sliding window per email. 5 failed logins inside 15 min → 15-min lockout. `AuthService.login`:
- checks `is_locked` first (constant-time response, no DB hit, no enumeration)
- records failure on every wrong-password attempt — including unknown email — so lock-trip behaviour can't be used as an existence oracle
- `clear()` wipes counter + lock on successful auth
- fail-open on Redis outage (logged warning; auth still works but no lockout)
5 unit tests in `backend/tests/unit/test_account_lockout.py` cover below-threshold / at-threshold / case-insensitive email / clear / Redis-outage fail-open.

**S10 — `UserLogin.password.min_length` dropped.** Was 8-char min; rejecting short passwords at login locks out legacy users + leaks policy via 422-vs-401 differential. Now only `max_length=128` DoS guardrail. `UserCreate.password` 12-char min unchanged.

**S11 — Frontend Dockerfile hardened.** Switched to `oven/bun:1-alpine` base + `bun install --frozen-lockfile` (lockfile must agree with package.json or install fails — refuses drift). Multi-stage build keeps build dependencies out of runtime. `tini` PID 1 for clean SIGTERM. Non-root `nextjs` user (uid 1001). `HEALTHCHECK wget /` every 30s. Telemetry disabled via `NEXT_TELEMETRY_DISABLED=1`.

**S12 — Sentry capture on 500.** `app/main.py:handle_unexpected_exception` calls `sentry_sdk.capture_exception(exc)` before building the error envelope. No-op when DSN unset (the import succeeds but the un-initialised hub silently drops the call). Defensive try/except so telemetry can never mask the actual 500.

**S13 — Mailgun header sanitize.** New `_sanitize_header()` in `services/notifications/channels.py` strips `\r` / `\n` / `\x00` and truncates to RFC 5322 998-char line limit. Applied to subject, recipient, and sender fields. Defence-in-depth — Mailgun's HTTP API normalises most input, but this blocks BCC-injection via a malicious display name.

**S14 — `pip-audit` in CI.** Added step to `.github/workflows/ci.yml` `backend-sanity` job. `pip-audit --strict --skip-editable -r backend/requirements.txt`. `continue-on-error: true` for the first run so the baseline isn't a hard block; flip to hard-fail after a clean run is on record.

**S15 — `/health` KPI leak fix.** Public probe now returns only `{ status, version, database, kpi_alerts: [] }`. KPI alert messages were leaking volume + pass-rate signals to unauthenticated callers. Admins read full KPI surface via auth-gated `/api/v1/analytics` (already wired into the admin shell). Test renamed `test_health_endpoint_does_not_leak_kpi_alerts` and asserts the empty list.

### Deferred to backlog

Recorded in `SECURITY_AUDIT.md` "Open backlog":
- **S6** — caddy/nginx reverse proxy + TLS termination in `docker-compose.yml`. Backend + frontend currently bind directly to host ports. ~1-2 hr; needs production deploy decision.
- **S9** — Refresh-token rotation + DB revocation table. Logout currently clears client only. ~2-3 hr.
- **S16** — Move tokens from `localStorage` → httpOnly + Secure + SameSite=Lax cookies. CSP in S1/S2 narrows the XSS surface in the meantime. ~1-2 days.
- **S17** — TOTP MFA for admin / owner roles. WebAuthn long-term. ~2-3 days.
- **S18** — Password hash pbkdf2_sha256 → Argon2id (OWASP 2025). Dual-read transition. ~1 day.
- **S19** — JWT HS256 → RS256 w/ private/public key separation. ~4 hr.

## Tasks in progress

None.

## Open bugs / blockers

- Same as prior session: smoke selector re-point + `ci.yml:198` flag flip pending 3 green local runs against `docker compose up`. Recipes preserved from S89.1 progress.md (run from this branch root).
- `pip-audit` first run will surface any current advisories; `continue-on-error: true` keeps CI green during the baseline pass. Flip to hard-fail in a follow-up PR.
- `python-jose` is at 3.3.0+ which has had CVEs in some 3.x versions — `pip-audit` will surface if our pin is exposed.
- Prod Supabase still needs `python scripts/seed_invite_codes.py` for `AIRU2026` before May-19 booth.

## Files touched this session

**Backend new (2):**
- `backend/app/core/account_lockout.py`
- `backend/tests/unit/test_account_lockout.py`

**Backend modified (5):**
- `backend/app/main.py` — `SecurityHeadersMiddleware` + `TrustedHostMiddleware` + `ProxyHeadersMiddleware` + Sentry `capture_exception` on 500 + `/health` KPI strip
- `backend/app/core/config.py` — `ALLOWED_HOSTS`, `TRUSTED_PROXY_HOPS`, `OPENSEARCH_PASSWORD`, account-lockout settings; `AUTO_SEED_DEMO_DATA` default flipped; prod assertions strengthened
- `backend/app/schemas/auth.py` — `UserLogin.password` min_length dropped
- `backend/app/services/auth/service.py` — account-lockout integration
- `backend/app/services/notifications/channels.py` — `_sanitize_header()` on subject/recipient/sender
- `backend/.env.example` — `AUTO_SEED_DEMO_DATA` comment
- `backend/tests/unit/test_health_kpi_alerts.py` — assert no KPI leak

**Frontend modified (2):**
- `frontend/next.config.ts` — `headers()` block w/ CSP + HSTS + etc.
- `frontend/Dockerfile` — bun + frozen-lockfile + multi-stage + tini + non-root + HEALTHCHECK

**CI (1):**
- `.github/workflows/ci.yml` — `pip-audit` step in `backend-sanity`

**Docs (4):**
- `SECURITY_AUDIT.md` (new) — 30 findings + plan + operator deploy checklist + sticky knowns
- `CLAUDE.md` — S20 section appended; older sections compressed to fit 200-line cap
- `frontend/CLAUDE.md` — S20 row in sprint table
- `progress.md` — this file (overwrite per device rule §2)

## Commands to resume

```bash
# Verify backend boots clean
cd backend && python -c "from app.main import create_app; app = create_app(); print('OK', len(app.routes))"
# Expected: OK 112

# Backend test suite
cd backend && pytest tests/unit -q                 # 396 passed, 1 xfailed
cd backend && pytest tests/integration -q          # 63 passed

# Frontend
cd frontend && bun run lint                        # 0 errors
cd frontend && bunx --bun tsc --noEmit             # clean
cd frontend && bun run build                       # 36 routes
cd frontend && bun scripts/audit/emoji-grep.mjs    # 0 hits / 123 files

# Production-assertion smoke (set ENVIRONMENT=production to trigger)
cd backend && ENVIRONMENT=production python -c "from app.core.config import settings; settings.validate_production_settings()"
# Expected: raises RuntimeError until ALLOWED_HOSTS + non-default secrets are set.

# Live-backend audit + smoke (operator action — recipe from prior session in git history)
docker compose up --build
python backend/scripts/demo_seed_pakistan.py
bun run audit                                      # full state matrix
python tests/e2e/playwright/run_smoke_suite.py     # × 3 green before flipping ci.yml:198
```

## Next session

1. Run pip-audit baseline locally; document any CVEs in `SECURITY_AUDIT.md` "Open backlog"; flip the CI step to hard-fail in a one-line PR if clean.
2. Tackle the audit + smoke recipes from prior session: 3 green smoke runs → drop `continue-on-error: true` from `ci.yml:198`.
3. Pick one S20-deferred item to ship next. Recommended order: S9 refresh-token rotation (highest cost/benefit ratio at the moment).
4. Refresh `docs/scholarai/IMPLEMENTATION_STATUS_REPORT.md` to reflect S87 + S89 + S89.1 + S20.

## Verdict

S20 security hardening **SHIPPED** to `feat/s89-premium-cultural`. 11 P0+P1 audit items closed in code + 1 new unit-test module + new ops doc (`SECURITY_AUDIT.md`). Backend tests 396 + 63 green; frontend gates green; create_app() boots clean. Remaining 6 deferred items have explicit cost estimates in `SECURITY_AUDIT.md` — pick the next one based on the deploy timeline.
