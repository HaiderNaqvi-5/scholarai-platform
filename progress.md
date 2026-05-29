# progress.md — handoff

**Date:** 2026-05-30
**Branch:** `s93/auth-tier-1`

## Session: Clerk "why is it not working" audit + fixes

Asked to check why Clerk is not working and make sure it works / is not doing anything wrong. Ran an exhaustive 6-dimension adversarially-verified audit (workflow), then fixed the real defects. Full report in `CLERK_AUDIT.md`.

### Outcome
Clerk is structurally correct (proxy.ts valid Next-16 middleware, client.ts uses Clerk token, ClerkProvider env-gated, dispatcher routes on AUTH_PROVIDER). The real problems were prod-only / test-masked bugs hidden behind a CI blind spot. All fixed + verified — **561 backend pass + 1 xfail** under the new all-dirs command; `compileall` clean.

### Tasks completed (committed this session)
1. `.github/workflows/ci.yml:29` — added `tests/integrations` + `api|core|db|services|scripts`. CI ran `tests/integration` (singular) and collected **0 of 42** Clerk/Resend tests; this gap masked everything below.
2. `backend/tests/integrations/test_clerk_user_sync.py` — `AsyncMock`→`MagicMock` (sync SDK). 14/14 clerk tests green.
3. `backend/app/integrations/resend/send.py` — `response.id`→`response["id"]` (SDK 2.5.1 returns dict; was a prod silent total-email outage swallowed by the best-effort wrapper). Mocks flipped to real dict in `test_resend_send.py`. (Closes the divergence noted in the prior Task-17 handoff.)
4. `backend/scripts/clerk_bulk_import.py` + `clerk_seed_demo.py` — dropped `await` on sync `api.users.create()` (same class as df37604). Mock `AsyncMock`→`MagicMock` in `tests/scripts/test_clerk_bulk_import.py`.
5. `backend/app/integrations/clerk/jwt_verify.py` — JWKS httpx error → `ClerkAuthError` (was raw 500 across the authed surface); removed dead `lru_cache` import; added **env-gated** `iss`/`azp` validation.
6. `backend/app/core/config.py` — added `CLERK_ISSUER`, `CLERK_AUTHORIZED_PARTIES` (+ `clerk_authorized_parties` property). Empty default = OFF (back-compat).
7. `backend/app/core/dependencies.py` — `_get_user_from_clerk_jwt` maps `ValueError` (no primary email)→401 not 500.
8. `backend/tests/unit/test_auth_claim_enforcement.py` — autouse fixture pins `AUTH_PROVIDER=local` (ambient `backend/.env` is clerk; local-path tests were routing to the clerk path).

### In-progress / next step
None active.

### Open — need operator decision / value (NOT code bugs)
- **Prod CSP**: `frontend/next.config.ts` allows only `*.clerk.accounts.dev`. A production custom Clerk domain (e.g. `clerk.aidwiseai.com`) is blocked on connect/script/frame-src → silent auth break in prod. Add the deployed Clerk FAPI host. **Need the prod Clerk domain.**
- **Activate iss/azp**: set `CLERK_ISSUER` + `CLERK_AUTHORIZED_PARTIES` in prod env to enable the new binding (inert by default).

### Deferred (lower severity — full list in CLERK_AUDIT.md)
CSP `'unsafe-inline'`→nonce; no backend session-revocation (clerk sessions valid until natural expiry); zero frontend test infra (proxy.ts / client.ts clerk branch / sso-callback untested); `login/page.tsx` `?next=` open-redirect; IntegrityError first-login race; `clerk_webhook` blank-secret precheck; `.env.example` stale `RESEND_FROM_ADDRESS` + `AUTO_SEED_DEMO_DATA=true`.

### Files touched
- `.github/workflows/ci.yml`
- `backend/app/integrations/clerk/jwt_verify.py`
- `backend/app/integrations/resend/send.py`
- `backend/app/core/config.py`
- `backend/app/core/dependencies.py`
- `backend/scripts/clerk_bulk_import.py`, `backend/scripts/clerk_seed_demo.py`
- `backend/tests/integrations/test_clerk_user_sync.py`, `test_resend_send.py`
- `backend/tests/scripts/test_clerk_bulk_import.py`
- `backend/tests/unit/test_auth_claim_enforcement.py`
- `CLAUDE.md`, `CLERK_AUDIT.md` (new), `progress.md`

### Commands to resume / verify
```
cd backend && python -m pytest tests/unit tests/integration tests/integrations tests/api tests/core tests/db tests/services tests/scripts -q
python -m compileall backend/app backend/scripts -q
# frontend (untouched this session): cd frontend && bunx --bun tsc --noEmit && bun run lint && bun run build
```

### Note on local test env
`backend/.env` sets `AUTH_PROVIDER=clerk` (live wire-up from Task 17). CI has no such `.env` → default `local`. Tests asserting local-path behavior must pin `AUTH_PROVIDER=local` (done for `test_auth_claim_enforcement`).

---
_Prior session handoff (Task-17 Clerk OAuth, branch s93/auth-tier-1, head df37604/83eb589) preserved in git history; superseded by this audit + fix pass._
