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

## Required FRONTEND_BASE_URL

`backend/.env` must set `FRONTEND_BASE_URL=https://<public-frontend-origin>` for transactional email CTAs (welcome login button, deletion cancel link, reminder + alert dashboard buttons). Empty string is accepted — templates render the text fallback without a CTA.

## Resend template registry

All outbound transactional mail goes through `app.services.notifications.channels.send_templated_email_best_effort` → `send_email_notification` → `send_transactional`. The latter validates the template name against a `Literal[...]` so unknown templates fail at the schema layer.

Registry (`backend/app/integrations/resend/send.py:_TEMPLATES`):

| Template | Trigger | Context keys |
|----------|---------|--------------|
| `welcome` | Clerk `user.created` (brand-new only) | `name`, `login_url` |
| `data_export_ready` | `ExportService.fulfil_export` after `status=completed` | `name`, `download_url` |
| `account_deletion_scheduled` | `POST /api/v1/privacy/account-deletion` | `name`, `scheduled_deletion_at`, `cancel_url` |
| `account_deletion_cancelled` | `DELETE /api/v1/privacy/account-deletion` | `name` |
| `waitlist_confirmation` | `POST /api/v1/waitlist` | `plan`, `currency` |
| `deadline_reminder` | Daily Celery `tasks.run_deadline_reminders` | `name`, `upcoming: [{title, deadline_iso, days_left}]`, `dashboard_url` |
| `priority_alert` | Daily Celery `tasks.run_priority_scholarship_alerts` | `name`, `scholarships: [{title, deadline_iso, country}]`, `dashboard_url` |

### Add a new template

1. Create `backend/app/integrations/resend/templates/<name>.py` exporting `render(ctx: dict) -> tuple[str, str, str]` (subject, html, text). Use `ctx.get("k") or "default"` for every key so missing keys never throw.
2. Add the module import + `_TEMPLATES` entry + `Literal["...", ...]` member in `send.py`.
3. Add a render unit test in `tests/integrations/test_resend_send.py` asserting brand string + key context vars appear in output.
4. Call from the trigger site via `send_templated_email_best_effort(to=..., template="<name>", context={...}, source="<short_tag>")`.

### `fan_out_for_plan` contract (post-Phase-2)

```python
await fan_out_for_plan(
    db, user,
    email_template="<registered_template>",
    email_context={...},            # dict matching the template's render() expectations
    whatsapp_message="<short plaintext>",  # WhatsApp Business has no HTML
)
```

- Email branch is best-effort via `send_templated_email_best_effort` — Resend failures log + drop, never 5xx the task.
- WhatsApp branch records a `usage_ledger` row through `record_whatsapp` (burn-cap accounting).
- All free-text email through this path is gone; every send is schema-validated against the registry.

## Clerk lifecycle email branding (Phase 3a)

Clerk hosts the verification / magic-link / password-reset / invitation emails. Re-brand them per environment (dev / staging / prod) at **Clerk Dashboard → Customization → Emails**.

Required brand assets:
- `aidwiseai-logo-light-400.png` (400×400 transparent, ink-deep `#0E1A1F` mark)
- Sender domain `aidwiseai.com` already verified in Clerk → Customization → Email → "Sending domain"

Per template (Verification code / Magic link / Password reset / Invitation):
- From name: `AidwiseAI`
- Reply-to: `noreply@aidwiseai.com`
- Logo: `aidwiseai-logo-light-400.png`
- Footer: `AidwiseAI · aidwiseai.com`
- Keep all `{{...}}` placeholders unchanged (e.g. `{{verification_code}}`, `{{magic_link}}`).

Suggested subjects:

| Template | Subject |
|----------|---------|
| Verification code | `AidwiseAI: your verification code` |
| Magic link | `AidwiseAI: sign-in link` |
| Password reset | `AidwiseAI: reset your password` |
| Invitation | `You're invited to AidwiseAI` |

Acceptance: send a Clerk Dashboard test email for each template → confirm logo + sender + subject + reply-to in your inbox. Repeat per environment.

## Resend as Clerk's custom SMTP provider (Phase 3b, optional)

Run only when Clerk-originated email volume crosses ~500/day or you want one consolidated sender-reputation pool.

### DNS sub-domain split

Reason: keep our apex (`aidwiseai.com`) for product-transactional Resend traffic, isolate Clerk's lifecycle email on a sub-domain so deliverability metrics stay separate.

1. Add sub-domain `mail.aidwiseai.com` in your DNS provider.
2. Resend dashboard → Domains → Add `mail.aidwiseai.com` → copy the SPF + DKIM TXT records → add at registrar → wait for Resend to mark "Verified" (typically <15 min).
3. Resend → API keys → Create → "Sending access" → restrict to `mail.aidwiseai.com` only. Copy the `re_clerk_smtp_...` value.

### Wire SMTP into Clerk

Clerk Dashboard → Customization → Email & SMS → "Custom email provider" → SMTP:

| Field | Value |
|-------|-------|
| Host | `smtp.resend.com` |
| Port | `465` (SSL) |
| Username | `resend` |
| Password | `re_clerk_smtp_...` (from step above) |
| From address | `noreply@mail.aidwiseai.com` |
| From name | `AidwiseAI` |

Click "Send test email", confirm in inbox, save.

### Rotation

Rotate the Clerk SMTP key (`re_clerk_smtp_...`) independently of the apex `RESEND_API_KEY` used by the backend. The two keys are restricted to different domains so a leak of one does not require rotating the other.

---

## Social OAuth + magic-link + connected accounts (2026-05-27)

### Dashboard prerequisites (per Clerk environment)

Frontend renders 4 social buttons on `/login` + `/signup` unconditionally when `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` is set. A click on a disabled provider returns an error toast; the button stays visible.

**Enable in dashboard → Configure → User & Authentication → Social Connections:**

| Provider | Strategy | Clerk redirect URL pattern |
|----------|----------|----------------------------|
| Google | `oauth_google` | `https://<frontend>/sso-callback` |
| Microsoft | `oauth_microsoft` | same |
| Facebook | `oauth_facebook` | same |
| LinkedIn | `oauth_linkedin_oidc` | same |

For each provider, paste Clerk's generated "Redirect URL" into the provider's OAuth app config (Google Cloud Console / Microsoft Entra / Meta for Developers / LinkedIn Developers). Default scopes are sufficient — Clerk maps `email` + `name` claims automatically.

**Enable magic-link sign-in:**

Dashboard → Configure → User & Authentication → Email, Phone, Username → "Email verification link" toggle ON. Keep "Password" toggle ON (signup still requires it). Magic-link is sign-in only — `/signup` always uses the password + email-code 2-step flow.

### Frontend wire-up (already shipped — reference only)

- `frontend/src/components/auth/SocialAuthButtons.tsx` — 2x2 grid of branded buttons above the email form. Inline brand SVGs (Google 4-color G, Microsoft 4-square, Facebook f, LinkedIn in). No npm icon dep.
- `frontend/src/app/sso-callback/page.tsx` — mounts `<AuthenticateWithRedirectCallback />` with Fraunces "Signing you in…" shell. Absorbs OAuth + magic-link returns.
- `frontend/src/proxy.ts` — `/sso-callback` added to `isPublicRoute` matcher.
- `frontend/src/app/login/page.tsx` — `mode` state cycles `password → magic-link → magic-sent`. Magic-link mode hides the password field and switches the submit to "Send sign-in link" with a 30s resend cooldown after success.
- `frontend/src/app/signup/page.tsx` — social row shown only on create step (hidden during email-code verification).
- `frontend/src/components/settings/ConnectedAccountsPanel.tsx` — lists `user.externalAccounts`; Disconnect per row; "Connect" for unlinked providers. Refuses to disconnect the last identification method.
- `frontend/src/app/(student)/settings/page.tsx` — new "Connected accounts" tab between Privacy and Notifications (clerk-mode only).

### Smoke per provider

1. `/login` → click Google → redirect to accounts.google.com → choose account → return to `/sso-callback` → `/feed`. Cookie `__session` present afterwards.
2. `/login` → "Or email me a sign-in link" → enter email → Send → inbox shows AidwiseAI-branded link → click → `/feed`.
3. `/signup` → click LinkedIn → Clerk-hosted consent screen → `/sso-callback` → `/onboarding`.
4. `/settings` → Connected accounts tab → confirm linked providers list + emails. Click Disconnect on one (must leave at least one method) → row disappears.
5. `/settings` → Connect a new account → click an unlinked provider → OAuth roundtrip → row reappears.

### Known caveats

- Clerk SDK 6.39.4 exports `<SignedIn>` / `<SignedOut>` (not `<Show>` — that lands in a future major). Layout header uses the former pair.
- LinkedIn strategy is `oauth_linkedin_oidc` (current) not legacy `oauth_linkedin`.
- Apple Sign-In requires a $99/yr Apple Developer Account — deferred until the iOS app.
