# Clerk Integration Audit — Final Report

> Generated 2026-05-29 via 6-dimension adversarially-verified workflow (25 confirmed / 2 refuted of 27). Session also fixed 2 stale `test_clerk_user_sync.py` mocks (14/14 clerk backend tests green).

## 1. Verdict

**Clerk is wired correctly at the structural level (dispatcher, JWKS-keyed RS256 signature verification, svix-signed webhooks, 410-gating of legacy local auth, dual-mode `get_current_user`) and 14/14 Clerk backend tests are green this session — but it is NOT production-safe end-to-end: four HIGH defects (JWKS-error→500, missing iss/azp binding, a prod-only Resend `.id`/dict crash, and a CI directory typo that collects 0 of 42 auth tests) plus a sync-SDK `await` bug in the migration script mean the auth surface and its safety net are degraded in exactly the deployment that uses Clerk.**

## 2. Confirmed issues (severity-sorted)

| ID | Sev | File:line | Issue | Fix |
|----|-----|-----------|-------|-----|
| jwks-fetch-failure-becomes-500 | HIGH | `backend/app/integrations/clerk/jwt_verify.py:41-42,68` | httpx JWKS error → raw HTTP 500 across entire authed surface (not 401/503) | Catch `httpx.HTTPError` → `ClerkAuthError`/503 |
| clerk-jwt-no-iss-azp-check | HIGH | `backend/app/integrations/clerk/jwt_verify.py:72-90` | No `iss`/`azp` validation → cross-app token reuse auto-provisions a User | Pass `issuer=` to decode; reject unlisted `azp` |
| resend-response-id-attribute-access | HIGH | `backend/app/integrations/resend/send.py:61-68` | SDK 2.5.1 returns a dict; `response.id` raises `AttributeError` on every real send | `response["id"]` |
| ci-skips-all-clerk-resend-tests | HIGH | `.github/workflows/ci.yml:29` | CI runs `tests/integration` (singular); all 42 Clerk/Resend tests live in `tests/integrations` etc. → 0 collected | Add the plural + sibling dirs to pytest invocation |
| bulk-import-await-sync-sdk | HIGH | `backend/scripts/clerk_bulk_import.py:25` (also `clerk_seed_demo.py:20`) | `await api.users.create()` on sync SDK → `TypeError`, migration imports 0 users; AsyncMock masks it | Drop `await`; mock with `MagicMock` |
| resend-send-attribute-vs-dict | HIGH | `backend/app/integrations/resend/send.py:68` | Same dict-vs-attribute defect as above, framed as test-masking (`MagicMock(id=...)`) | `response["id"]`; mock a real dict |
| clerk-no-session-revocation-check | MED | `backend/app/core/dependencies.py:139-167` | Revoked/signed-out Clerk sessions honored until natural expiry; no backend kill switch except `user.deleted` webhook | Keep TTL short; optionally call Clerk sessions API on sensitive routes; document |
| clerk-jwks-blank-dev-silent-failure | MED | `backend/app/core/config.py:156-159` | `AUTH_PROVIDER=clerk` + blank `CLERK_JWKS_URL` boots silently in dev, 401s every request as misleading `AUTH_TOKEN_EXPIRED` | Warn on boot in dev; map blank-JWKS error to a misconfig code, not 401 |
| csp-missing-clerk-prod-fapi-domain | MED | `frontend/next.config.ts:25,30,37-38` | CSP only allows `*.clerk.accounts.dev`; prod custom-domain FAPI/clerk-js/captcha frame blocked → silent auth break in prod | Add prod FAPI host to connect/script/frame-src |
| csp-script-src-unsafe-inline-prod | MED | `frontend/next.config.ts:37` | `'unsafe-inline'` in prod `script-src` weakens CSP to an origin allowlist | Move to nonce-based script-src; separate from style-src justification |
| no-frontend-test-infra-clerk | MED | `frontend/package.json:6-11` | Zero unit/E2E tests; `proxy.ts` matcher, `getClerkToken()`, `clerkAdapter`, `sso-callback` untested | Add vitest + one Playwright sso-callback spec; wire into CI |
| no-primary-email-valueerror-500 | LOW | `backend/app/integrations/clerk/user_sync.py:89-90` | `ValueError` (no primary email) → HTTP 500 instead of 401/403 | Catch `ValueError` in dispatcher → `ScholarAIException` 401 |
| clerk-jwt-no-issuer-azp-verification | LOW | `backend/app/integrations/clerk/jwt_verify.py:73-78` | (Defense-in-depth dup of HIGH iss/azp finding) token-confusion if JWKS ever shared | Add `CLERK_ISSUER`/`CLERK_AUTHORIZED_PARTIES` validation |
| ensure-local-user-unique-race-500 | LOW | `backend/app/integrations/clerk/user_sync.py:105-113` | Concurrent first-login insert → `IntegrityError` → 503 | Catch `IntegrityError`, rollback, re-SELECT; or upsert ON CONFLICT |
| clerk-jwks-fetch-error-becomes-500 | LOW | `backend/app/integrations/clerk/jwt_verify.py:41-55` | (Dup of HIGH JWKS finding) + unused `lru_cache` import | Wrap fetch; remove dead `lru_cache` import |
| clerk-webhook-secret-not-prechecked | LOW | `backend/app/api/v1/routes/clerk_webhook.py:34-42` | Blank `CLERK_WEBHOOK_SECRET` relies on svix to fail closed; surfaces as 500 | Explicit `if not settings.CLERK_WEBHOOK_SECRET: raise 503` |
| resend-from-address-stale-nonempty-template | LOW | `backend/.env.example:63` | Ships `noreply@grantpath.app` (old brand, non-empty) vs blank convention | Blank it; comment expected AidwiseAI sender |
| login-next-param-unsanitized-redirect | LOW | `frontend/src/app/login/page.tsx:79,95,122` | `?next=` redirected without validation → open/protocol-relative redirect post-auth | `next.startsWith('/') && !next.startsWith('//') ? next : '/feed'` |
| csp-img-src-wildcard-https | LOW | `frontend/next.config.ts:26` | `img-src ... https:` allows any HTTPS origin (tracking-pixel beacon surface) | Tighten to known hosts or document tradeoff |
| no-ci-frontend-clerk-build-matrix | LOW | `.github/workflows/ci.yml:71-97` | CI never builds with `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` set (Clerk runtime-init uncovered) | Add a build leg with a dummy `pk_test_...` |
| untested-clerk-branches-backend | LOW | `backend/app/integrations/clerk/jwt_verify.py` (n/a) | JWKS-failure, `user.updated` sync, async email-collision link, dev fallthrough untested | Add the 3 targeted tests |
| double-commit-with-get-db-autocommit | INFO | `backend/app/integrations/clerk/user_sync.py:98,112-113` | Provisioning commits inside a session `get_db` also auto-commits | Prefer `flush()`+`refresh()`; let `get_db` own commit, or document |
| jwks-cache-non-atomic-refresh-race | INFO | `backend/app/integrations/clerk/jwt_verify.py:30-55` | Non-atomic cache refresh → thundering herd + 5s blocking `httpx.get` stalls event loop | `asyncio.Lock` single-flight + threadpool/`AsyncClient` |
| clerk-prod-validation-order | INFO | `backend/app/core/config.py:178-216` | Clerk prod-guard runs last; earlier misconfig masks it | Accumulate failures, raise once |
| env-example-auto-seed-enabled | INFO | `backend/.env.example:21` | Ships `AUTO_SEED_DEMO_DATA=true`; bypassed only if `ENVIRONMENT` is a non-matching string | Deny-by-default env-name check |

### HIGH — exact fixes

**`jwks-fetch-failure-becomes-500`** — `jwt_verify.py:41-42` does `resp = httpx.get(url, timeout=5.0)` / `resp.raise_for_status()`; `_get_jwks_keys()` at line 68 has no surrounding try/except, and the dispatcher (`dependencies.py:145-152`) only catches `ClerkAuthError`, so any httpx error escapes to the catch-all `Exception` handler (`main.py:211-231`) → 500. Wrap the fetch so external-dependency failures map to a sane status:
```python
try:
    resp = httpx.get(url, timeout=5.0)
    resp.raise_for_status()
except httpx.HTTPError as e:
    raise ClerkAuthError(f"JWKS fetch failed: {e}") from e   # -> 401, or map to 503 in the dependency
```
The 600s cache (`jwt_verify.py:30,36`) bounds the blast radius to cache-miss/expiry windows, but every cache-miss auth during a Clerk hiccup currently 500s. Consider serving stale cached keys on transient failure, and a retry on the 5s timeout.

**`clerk-jwt-no-iss-azp-check`** — `jwt_verify.py:73-78` calls `pyjwt.decode(token, pub, algorithms=[RS256/384/512], options={"require":["exp","sub"]})` with no `issuer=`/`audience=`; `iss`/`azp` are stored on `ClerkClaims` (lines 85-86) but never compared anywhere (dispatcher uses only `claims.sub`). Signature, alg-allowlist, kid, and exp are enforced, so this is missing audience-binding, not absent auth. Add settings and enforce:
```python
payload = pyjwt.decode(token, pub, algorithms=[...],
                       issuer=settings.CLERK_ISSUER,
                       options={"require": ["exp", "sub", "iss"]})
if settings.CLERK_AUTHORIZED_PARTIES and payload.get("azp") not in settings.CLERK_AUTHORIZED_PARTIES:
    raise ClerkAuthError("untrusted azp")
```
Define `CLERK_ISSUER` and `CLERK_AUTHORIZED_PARTIES` in `config.py` (currently only `CLERK_SECRET_KEY/PUBLISHABLE_KEY/JWKS_URL/WEBHOOK_SECRET` exist at 148-151).

**`resend-response-id-attribute-access` / `resend-send-attribute-vs-dict`** (same root cause) — `send.py:68` does `return response.id` on the result of `resend.Emails.send(...)`. In resend 2.5.1, `Emails.send -> Email` where `Email` is a `TypedDict` (subclasses `dict`) and the value is `requests.Response.json()` (a plain dict; `typing.cast` is a runtime no-op), so `.id` raises `AttributeError` on every real send. `send_templated_email_best_effort` (`channels.py:149-165`) swallows it → **silent total email outage** across all 7 templates (welcome, data_export_ready, account_deletion_*, waitlist_confirmation, deadline_reminder, priority_alert). Tests pass because they mock `MagicMock(id=...)` (`test_resend_send.py:30,172`).
```python
return response["id"] if isinstance(response, dict) else response.id
```
Change the test mocks to a real dict (`{"id": "msg_123"}`) so the regression is caught.

**`ci-skips-all-clerk-resend-tests`** — `ci.yml:29` is `pytest backend/tests/unit backend/tests/integration -q` (singular). All 42 Clerk/Resend tests live in `tests/integrations` (plural) plus `tests/api`, `tests/core`, `tests/db`, `tests/services`, `tests/scripts`. Empirically: `pytest tests/unit tests/integration --co` → 514 tests, 0 clerk/resend; `pytest tests --co` → 562, exactly 42 clerk/resend. Every auth-critical guard (alg:none rejection, expired/unknown-kid, svix bad-signature, user.created/deleted, dual-mode dispatcher, 410-gating) currently merges green without ever running.
```yaml
run: pytest backend/tests/unit backend/tests/integration backend/tests/integrations backend/tests/api backend/tests/core backend/tests/db backend/tests/services backend/tests/scripts -q
```
Long-term, consolidate the singular/plural directory split. **Fixing this CI gap first will immediately surface the bulk-import and Resend bugs below** (they are real but test-masked).

**`bulk-import-await-sync-sdk`** — `clerk_bulk_import.py:25` is `created = await api.users.create({...})` where `api` is the real sync `Clerk(...)` client. clerk-backend-api 1.6.0 is synchronous (same class as the already-fixed df37604 on `api.users.get`), so this `TypeError`s on the first user and imports zero. `test_clerk_bulk_import.py:47` masks it with `AsyncMock`. The identical bug is at `clerk_seed_demo.py:20`.
```python
created = api.users.create({...})   # drop await, in both scripts
```
Update the test mock to `MagicMock(return_value=MagicMock(id=...))`.

## 3. Cleared (checked, not issues)

- **`clerk-me-before-window-clerk-hydrates-no-retry`** — Refuted. `useAuth().isSignedIn` and `window.Clerk.session` derive from the **same** clerk-js singleton (`ClerkContextProvider` snapshot; `deriveFromClientSideState`), so `isSignedIn===true` requires a real `window.Clerk.session`; the claimed cold-start token-less `/me` window cannot occur, and `userId` is in the effect dep array so `/me` re-fires on resolution. Not a defect.
- **`clerk-token-via-window-global-instead-of-hook`** — Refuted. Reading the bearer from `window.Clerk` is not "independent of React auth state" — both share the same clerk-js client; `/me` is only called when `isLoaded && isSignedIn`. At most an idiomatic-API code-style preference, not a correctness bug.
- **Items confirmed correct by design (do NOT flag):** the sync-SDK no-await on `api.users.get` (df37604 fix), `src/proxy.ts` as valid Next-16 middleware, and the already-repaired `test_clerk_user_sync.py` AsyncMock→MagicMock (14/14 green).

## 4. Recommended fix order (smallest-diff-first)

1. **`ci.yml:29`** — add the plural + sibling test dirs (one-line). Restores the safety net and makes the next two fixes test-verifiable on PRs.
2. **`send.py:68`** — `response["id"]` (one line) + flip Resend test mocks to a real dict. Unblocks the entire transactional-email surface.
3. **`clerk_bulk_import.py:25` and `clerk_seed_demo.py:20`** — drop `await` (two lines) + `MagicMock` in `test_clerk_bulk_import.py`. Restores migration tooling.
4. **`jwt_verify.py:41-42,68`** — wrap `httpx.get`/`raise_for_status` in `except httpx.HTTPError -> ClerkAuthError` (or 503). Converts JWKS hiccups from 500 to 401/503. Remove the dead `lru_cache` import (line 5) in the same edit.
5. **`jwt_verify.py:73-78` + `config.py:148-151`** — add `CLERK_ISSUER`/`CLERK_AUTHORIZED_PARTIES`, pass `issuer=`, require `iss`, reject unlisted `azp`. Closes cross-app token reuse.
6. **`next.config.ts:25,30,37-38`** — add the production Clerk FAPI host to connect/script/frame-src (env-derived) so prod auth does not silently break. Same file: scope `script-src` to a nonce (drop `'unsafe-inline'`) and optionally tighten `img-src`.
7. **`config.py:156-159`** — emit a dev startup `log.warning` when `AUTH_PROVIDER=='clerk'` and `CLERK_JWKS_URL` is blank, and map that error away from `AUTH_TOKEN_EXPIRED`.
8. **`dependencies.py:139-167` / `user_sync.py:89-90,105-113`** — translate `ValueError`→401 and catch `IntegrityError`→rollback+re-SELECT (or upsert ON CONFLICT) on the provisioning path.
9. **`clerk_webhook.py:34-42`** — explicit blank-`CLERK_WEBHOOK_SECRET`→503 guard (fail closed independently of svix).
10. **`login/page.tsx`** — one-line `next` sanitizer; **`.env.example:63`** — blank the stale `RESEND_FROM_ADDRESS`.
11. **Test/CI hardening (deferred, non-blocking):** add the 3 untested backend Clerk tests; stand up frontend vitest + one Playwright sso-callback spec; add a Clerk-key CI build leg; document the no-backend-revocation gap and the `get_db` double-commit; consider `asyncio.Lock` single-flight on the JWKS cache.