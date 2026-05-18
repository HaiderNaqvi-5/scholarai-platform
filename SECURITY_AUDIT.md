# SECURITY_AUDIT.md — 2026-05-18

Snapshot of the security posture after the P0 + P1 hardening pass on
`feat/s89-premium-cultural`. Backend + frontend covered. Threats
addressed are listed under "Closed"; "Open" items remain on the
backlog with explicit owner.

Last full audit: 2026-05-18. Run again before every production deploy.

---

## Closed in S20 (P0 + P1 hardening pass)

| # | Severity | Surface | Fix |
|---|----------|---------|-----|
| S1 | HIGH | Backend response headers | `SecurityHeadersMiddleware` (HSTS / X-Frame-Options DENY / X-Content-Type-Options / Referrer-Policy / Permissions-Policy / COOP / CORP / CSP). `TrustedHostMiddleware` gated by `ALLOWED_HOSTS` env. `backend/app/main.py`. |
| S2 | HIGH | Frontend response headers | `next.config.ts` `headers()` block mirrors backend headers. CSP allows `NEXT_PUBLIC_API_BASE_URL` for `connect-src`; production drops `'unsafe-eval'`. |
| S3 | HIGH | Demo accounts in prod | `AUTO_SEED_DEMO_DATA` default flipped to `False`. `validate_production_settings` already rejects `True` in prod/staging. |
| S4 | HIGH | Secret defaults at boot | `OPENSEARCH_PASSWORD` added to settings + prod assertion rejects default value. `ALLOWED_HOSTS` required in prod (empty list trips assertion). `SECRET_KEY` + Neo4j + DB checks already in place. |
| S5 | HIGH | CORS prod misconfig | `validate_production_settings` rejects `localhost` / `127.0.0.1` entries in `CORS_ORIGINS` when ENVIRONMENT is prod/staging. |
| S7 | MED | Reverse-proxy IP attribution | `uvicorn.middleware.proxy_headers.ProxyHeadersMiddleware` mounted when `TRUSTED_PROXY_HOPS > 0`. `request.client.host` now reflects the real client IP behind nginx / Cloudflare. Rate-limiter keys + Sentry breadcrumbs benefit immediately. |
| S8 | MED | Account-takeover via login brute-force | New `app/core/account_lockout.py` — Redis sliding window per email. 5 failures / 15min → 15-min lock. Fail-open on Redis outage. Wiped on successful auth. 5 unit tests in `tests/unit/test_account_lockout.py` (5/5 pass). |
| S10 | MED | Login schema info leak | `UserLogin.password` `min_length=8` dropped. Per-policy 422 no longer leaks (now constant 401). Registration policy unchanged on `UserCreate.password`. |
| S11 | MED | Frontend Dockerfile supply-chain + liveness | Switched to `oven/bun:1-alpine` + `bun install --frozen-lockfile`. Multi-stage build preserves non-root `nextjs` user. `tini` PID 1 for clean SIGTERM. `HEALTHCHECK CMD wget /` every 30s. |
| S12 | MED | Sentry context loss on 500 | Catch-all `handle_unexpected_exception` calls `sentry_sdk.capture_exception(exc)` before envelope. No-op when DSN unset. |
| S13 | MED | Mailgun header injection | `_sanitize_header()` strips CR / LF / NUL + truncates to RFC 5322 998-char limit. Subject + recipient + sender all sanitized. |
| S14 | MED | Dependency CVE drift | `pip-audit --strict` step added to `.github/workflows/ci.yml` `backend-sanity` job. `continue-on-error: true` for now so PRs stay unblocked; flip to hard-fail after baseline run. |
| S15 | INFO → fixed | `/health` KPI leak | Public probe returns DB status + version only. KPI alert messages removed. Admin reads `/api/v1/analytics`. Test in `test_health_kpi_alerts.py` updated to assert leak-free (3/3 pass). |

## Verification

```bash
# Backend
cd backend && python -c "from app.main import create_app; app = create_app(); print('OK', len(app.routes))"
# Expected: OK 112

cd backend && pytest tests/unit -q
# Expected: 396 passed, 1 xfailed

cd backend && pytest tests/integration -q
# (integration suite)

# Frontend
cd frontend && bun run lint           # 0 errors
cd frontend && bunx --bun tsc --noEmit # clean
cd frontend && bun run build          # green
cd frontend && bun scripts/audit/emoji-grep.mjs # 0 hits / 123 files

# Sentry stub on/off boot test
SENTRY_DSN= python -c "from app.main import create_app; create_app()"
```

## Operator deploy checklist (must run before prod / staging)

1. `SECRET_KEY` — 32+ random chars. Distinct from any other env.
2. `ENVIRONMENT=production` (or `staging`) — flips `_STRICT_RATE_LIMIT` + activates `validate_production_settings`.
3. `ALLOWED_HOSTS=["aidwiseai.com","www.aidwiseai.com","api.aidwiseai.com"]` — no wildcards, no localhost.
4. `CORS_ORIGINS=["https://aidwiseai.com","https://www.aidwiseai.com"]` — HTTPS only, no localhost.
5. `AUTO_SEED_DEMO_DATA=false` (or unset). Production assertion rejects True.
6. `DB_PASSWORD`, `NEO4J_PASSWORD`, `OPENSEARCH_PASSWORD` — all overridden from defaults.
7. `REDIS_URL`, `CELERY_BROKER_URL` — point at managed Redis, never localhost.
8. `SENTRY_DSN` — set to project DSN. `SENTRY_ENVIRONMENT=production`. `send_default_pii=False` already hard-coded.
9. `TRUSTED_PROXY_HOPS=1` (or 2 for Cloudflare → caddy → backend). Activates ProxyHeadersMiddleware so rate-limit keys + Sentry capture see the real client IP.
10. `MAILGUN_API_KEY` + `MAILGUN_DOMAIN` — without these `send_email` falls back to log-only.
11. Terminate TLS at the edge (Cloudflare / caddy / nginx). Backend HTTPS is opportunistic; HSTS + COOP need TLS.
12. Bind backend + frontend containers to internal docker network only. Expose `:443`/`:80` on the edge proxy.

## Open backlog (defer)

| # | Sev | Area | Notes |
|---|-----|------|-------|
| S6 | HIGH | Reverse proxy + TLS at edge | No nginx / caddy / traefik in `docker-compose.yml`. Backend + frontend bind directly to host. Add caddy service or document Cloudflare-in-front as the stance + drop host port bindings. ~1-2 hr. |
| S9 | MED | Refresh-token rotation + DB revocation | Refresh token in localStorage stays valid 7 days. Logout clears client side only. Add `revoked_token` table + `jti` claim. ~2-3 hr. |
| S16 | HIGH | Tokens in localStorage (XSS-readable) | Migrate to httpOnly + Secure + SameSite=Lax cookies. CSP S2 narrows XSS surface in the meantime. ~1-2 days. |
| S17 | MED | No MFA | TOTP for admin / owner roles at minimum. WebAuthn long-term. ~2-3 days. |
| S18 | MED | Password hash pbkdf2_sha256 | Migrate to Argon2id (OWASP 2025 recommendation). Dual-read transition. ~1 day. |
| S19 | LOW | JWT HS256 (shared secret) | Migrate to RS256 with private/public key separation when scaling out. ~4 hr. |
| OPS | INFO | Demo persona in prod | Decision pending: should prod ship a `zara.khan@example.com` showcase account? Privacy + tier consequences. |
| OPS | INFO | IMPLEMENTATION_STATUS_REPORT.md | Predates Pakistan pivot + Q1 retier + Air-Uni cohort + S89 + S89.1 + S20. Refresh before next external review. |

## Sticky knowns (do not re-investigate)

- `users.id` is `UUID(as_uuid=True)`. Every new model + migration must use `postgresql.UUID(as_uuid=True)` for FK columns.
- `Scholarship` ORM uses `title` + `provider_name` (NOT `name` / `provider`). Backfills + regex must match.
- Mailgun `send_email` returns `True` on log-only fallback so callers stay deterministic offline.
- `account_lockout` fails open on Redis outage (logged). Auth still works; just no lockout protection during the outage.
- `pip-audit` step is `continue-on-error: true` until a clean baseline run. Flip to hard-fail in a separate one-line PR.
