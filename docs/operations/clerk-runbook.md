# Clerk + Resend Runbook

## Keys / dashboards
- Clerk: https://dashboard.clerk.com → app `grantpath-{env}`
- Resend: https://resend.com → API keys

## Backend env vars (all set per environment)
- `AUTH_PROVIDER=local|clerk` — `local` keeps the legacy FastAPI auth path; `clerk` flips routing.
- `CLERK_SECRET_KEY` (sk_…), `CLERK_PUBLISHABLE_KEY` (pk_…), `CLERK_JWKS_URL`, `CLERK_WEBHOOK_SECRET` (whsec_…)
- `RESEND_API_KEY` (re_…), `RESEND_FROM_ADDRESS`

## Frontend env vars (build-time)
- `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` — blank disables the Clerk surface; provider + middleware fall through to local auth.
- `NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in`, `NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up`
- `NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL=/feed`, `NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL=/onboarding`

## Cutover sequence
1. Set the Clerk + Resend keys in staging secret store.
2. Run `python backend/scripts/clerk_seed_demo.py` to seed admin/mentor/student demo accounts in Clerk.
3. Run `python backend/scripts/clerk_bulk_import.py` to migrate existing users (idempotent on `User.clerk_user_id`).
4. Flip `AUTH_PROVIDER=clerk` on the backend service; redeploy.
5. Set `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` on the frontend; redeploy.
6. Smoke: `/sign-up` → onboarding → `/feed` → `/profile` → data-export → Resend email arrives.
7. After 1 release on Clerk, schedule cleanup PR (delete `backend/app/services/auth/service.py`, `password_resets` table, `account_lockout.py`).

## Rotate Clerk secret
1. Dashboard → API keys → "Roll secret".
2. Update `CLERK_SECRET_KEY` in secret store.
3. Redeploy backend.
4. Validate `/api/v1/auth/me` with a fresh sign-in.

## Rotate Resend key
Same pattern. `RESEND_API_KEY` only.

## Webhook re-delivery
Clerk dashboard → Webhooks → endpoint → "Send test" or "Resend" per event. Endpoint URL: `https://{api-host}/api/v1/webhooks/clerk`.

## Force user deletion (GDPR)
1. Backend: mark `User.is_active=False`, anonymise audit refs.
2. `clerk_client().users.delete(user_id=...)`.
3. Verify `user.deleted` webhook fires and the local row stays deactivated.

## MAU monitoring
Free tier 10k MAU. Dashboard → Usage → set 80% Slack alert.

## Rollback
1. Set `AUTH_PROVIDER=local` on backend, redeploy.
2. Set `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=""` on frontend, redeploy.
3. Existing users imported into Clerk also still have local `password_hash` rows — they can use the legacy login path.

## Known production-vs-test divergences
- `resend.Emails.send(params)` in SDK 2.5.x returns a `dict` (`{"id": "..."}`). `backend/app/integrations/resend/send.py:send_transactional` calls `response.id`; if the SDK returns raw dict in prod, change to `response["id"]`. Verify on first staging send.
