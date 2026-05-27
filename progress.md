# progress.md — scholarai-platform

**Date:** 2026-05-28
**Branch:** `s93/auth-tier-1` (PR #102)
**Head:** `df37604` (+ `83eb589` for narrowing)
**Mergeable:** yes (5/5 CI green; required-review gate is the only block)

## Session focus

Clerk OAuth + magic-link + connected-accounts shipped end-to-end. Google sign-in live in dev container. Three other providers (Microsoft / Facebook / LinkedIn) intentionally narrowed out of UI but strategy maps + brand SVGs kept on disk for one-line re-enable.

## Tasks completed this session

| # | Commit | Summary |
|---|--------|---------|
| 1 | `334df4d` | Clerk OAuth + magic-link + connected-accounts shipped. `clerkAdapter` adds `useClerkSocialLogin`/`useClerkSocialSignup`/`useClerkMagicLink`. `SocialAuthButtons` 2×2 grid above email form. `/sso-callback` mounts `<AuthenticateWithRedirectCallback />`. `/login` mode toggle (password / magic-link / magic-sent, 30s resend cooldown). `/signup` social row + Clerk Smart-CAPTCHA `<div id="clerk-captcha"/>`. `/settings → Connected accounts` panel. `proxy.ts` public-route += `/sso-callback`. `next.config.ts` CSP += `worker-src 'self' blob:` + `*.clerk.accounts.dev` hosts on connect-src/script-src/frame-src. |
| 2 | `94fe605` | `<AuthenticateWithRedirectCallback signInFallbackRedirectUrl="/feed" signUpFallbackRedirectUrl="/onboarding"/>` (post-OAuth landed on `/` because Clerk fell back to dashboard default). |
| 3 | `6b3ab67` | CSP `worker-src 'self' blob:` (Clerk Web Workers were blocked, console-noise only — auth still functioned). |
| 4 | `df37604` | **Backend bug**: `clerk-backend-api 1.6.0` SDK is sync — `api.users.get(...)` returns `User` directly. Both `ensure_local_user` + `ensure_local_user_async` were `await`-ing → `TypeError: object User can't be used in 'await' expression` → 500 on every /me. Tests passed (AsyncMock). Fix: drop `await`. |
| 5 | `83eb589` | Narrow `SOCIAL_PROVIDERS` to `["google"]`. Microsoft/Facebook/LinkedIn strategy maps + brand SVGs kept; re-enable = one-line append. `ConnectedAccountsPanel.ALL_STRATEGIES` derived from same source — auto-narrows. |

## Env wire-up done this session (not commits — local state)

| Where | Change |
|---|---|
| `.env` (repo root, new file) | `ENV_FILE=backend/.env` — compose interpolates this so `env_file: ${ENV_FILE:-.env.example}` in `docker-compose.yml` resolves to the real Clerk-keyed file. |
| `backend/.env` | `AUTH_PROVIDER=clerk`; `CLERK_SECRET_KEY=sk_test_…`; `CLERK_PUBLISHABLE_KEY=pk_test_…`; `CLERK_JWKS_URL=https://open-kid-75.clerk.accounts.dev/.well-known/jwks.json`. **DB/Redis URLs** swapped from `@localhost` to docker service hostnames `@postgres:5432` / `redis://redis:6379`. |
| `frontend/.env.local` | `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_…`; `CLERK_SECRET_KEY=sk_test_…`. |
| Docker container | Recreate after env edits — `docker compose up -d --force-recreate --no-deps backend` (compose `restart` does NOT reload `env_file`). |
| Postgres | `docker compose exec backend alembic upgrade head` → `20260526_0029` applied, `users.clerk_user_id` column + index + unique constraint live. |
| Clerk dashboard | Google SSO configured for instance `open-kid-75.clerk.accounts.dev` with custom credentials (own Google Cloud OAuth client). Redirect URI pasted into Google Cloud Console authorised list. |

## Verified end-to-end

- `/login` → click Google → consent screen → `/sso-callback` (Fraunces "Signing you in…") → `/feed` renders user dashboard.
- Backend log: `ensure_local_user_async` creates new `users` row with `clerk_user_id=user_3EHV…` on first sign-in.
- `/me` returns 200 + populated `UserResponse` JSON.
- Reload `/feed` → still authenticated (Clerk `__session` cookie restores).
- `/sign-in` + `/sign-up` legacy Clerk-default routes → 404 (deleted).
- `/booth/air-university` → `redirect("/")` (Air U cohort retired).

## Open items

- **Microsoft / Facebook / LinkedIn**: dashboard + provider-side OAuth apps not yet configured. Code-ready. To enable each: add provider strategy to `SOCIAL_PROVIDERS` array in `frontend/src/lib/auth/clerkAdapter.ts`, configure provider in Clerk dashboard, paste credentials, paste Clerk redirect URI into provider OAuth whitelist.
- **`POST /api/v1/profile/onboarding-prefs`** backend route: PDPB consent + marketing flags collected in clerk-mode signup but not yet persisted (console.warn flags the gap). Track for follow-up PR.
- **Webhook**: `CLERK_WEBHOOK_SECRET` still empty in `backend/.env`. Wire only if/when we need user.deleted soft-delete from Clerk dashboard ops. Code path exists at `/api/v1/webhooks/clerk`.
- **Docker backend build** failed mid-session (`pip install torch` exit 2). Workaround used `docker compose cp` to patch `user_sync.py` live. Full rebuild deferred — image still has the bug baked in; recreate without `--build` keeps the patched-via-cp file in place until container is destroyed.

## Known production-vs-test divergences (unchanged)

- `resend.Emails.send(params)` in SDK 2.5.x returns `dict` (`{"id": ...}`). `send.py:send_transactional` reads `response.id` (attribute). Tests use `MagicMock(id=...)`. Verify on first staging send.
- `clerk-backend-api` SDK is sync (Task-17 bugfix above). Mocking with `AsyncMock` masks real-SDK behaviour — prefer `MagicMock` for new tests.

## Files touched (committed)

- frontend: `lib/auth/clerkAdapter.ts`, `components/auth/SocialAuthButtons.tsx`, `components/settings/ConnectedAccountsPanel.tsx`, `app/sso-callback/page.tsx`, `app/login/page.tsx`, `app/signup/page.tsx`, `app/(student)/settings/page.tsx`, `proxy.ts`, `next.config.ts`
- backend: `app/integrations/clerk/user_sync.py`
- docs: `CLAUDE.md`, `progress.md`

## Files touched (env / local-only, NOT in git)

- `.env` (repo root)
- `backend/.env`
- `frontend/.env.local`

## Commands to resume

```powershell
# Branch state
cd C:\Users\HP\scholarai-platform
git status
gh pr checks 102

# Container sanity (should show clerk + real JWKS)
docker compose exec backend printenv | Select-String "AUTH_PROVIDER|CLERK_"

# Migration head
docker compose exec backend alembic current   # 20260526_0029 (head)

# Backend logs while you hit /me from browser
docker compose logs -f backend

# Frontend dev (Docker frontend container has stale build; prefer bare bun)
docker compose stop frontend
cd frontend && bun dev

# Re-enable a social provider
# 1. frontend/src/lib/auth/clerkAdapter.ts: append "microsoft" (or other) to SOCIAL_PROVIDERS
# 2. Clerk dashboard → SSO Connections → enable + paste creds
# 3. Provider dashboard → paste Clerk's redirect URI
```

## Plan reference

`~/.claude/plans/parallel-percolating-sifakis.md` — full round 1/2/3/3b/3c history.
