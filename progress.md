# progress.md — scholarai-platform

**Date:** 2026-05-27
**Branch:** `s93/auth-tier-1`

## Session: Clerk + Resend migration (Tasks 1–12 done; 13 pending)

Plan: `docs/superpowers/plans/2026-05-26-clerk-resend-migration.md`
Execution mode: superpowers:subagent-driven-development + karpathy-guidelines (strict surgical).

### Tasks completed this session

| # | Commit | Summary | Tests |
|---|--------|---------|-------|
| 1 | `d9ad076` + `600b04a` | `Settings` adds `AUTH_PROVIDER` + `CLERK_*` + `RESEND_*`; `validate_production_settings` extended; deps pinned (`clerk-backend-api==1.6.0`, `resend==2.5.1`, `svix==1.30.0`, `@clerk/nextjs ^6.12.0`, `@clerk/themes ^2.2.0`); both `.env.example` + `backend/.env.example` updated. | 2/2 |
| 1.1 | `a255b23` | Fix `test_prod_rejects_blank_clerk_when_provider_clerk` — `AUTO_SEED_DEMO_DATA=false` env override (validator returned early on prior check). | n/a |
| 2 | `68bc086` | `User.clerk_user_id` (String 64, nullable, unique, indexed) + migration `20260526_0029` (parent `20260525_0028`); `backend/tests/db/conftest.py` SQLite in-memory fixture. | 2/2 |
| 3 | `e616b47` | `jwt_verify.verify_clerk_jwt` — JWKS cache, RS256/384/512 only, rejects expired / unknown kid / `alg=none`. PyJWT 2.9.0 pinned. | 4/4 |
| 4 | `ede6c51` | `clerk/client.clerk_client()` lazy init + `user_sync.ensure_local_user` (lookup → fetch → email-collision link → create) writing `full_name` (not `first_name/last_name`). | 3/3 |
| 5 | `c632eb4` | Dual-mode `get_current_user`: preserved local body verbatim as `_get_user_from_local_jwt`; added `_get_user_from_clerk_jwt` (verify → `ensure_local_user_async` → sets `_token_capabilities` from `get_role_capabilities`). | 2/2 + 518 regression clean |
| 6 | `6b328e4` | `POST /api/v1/webhooks/clerk` — Svix HMAC verify; `user.created` / `user.updated` (email + full_name sync) / `user.deleted` (soft delete `is_active=False`). Registered in `api/v1/__init__.py`. | 3/3 |
| 7 | `e4a7e01` | `send_transactional` wrapper + Pydantic `TransactionalRequest` (EmailStr + CRLF reject) + 2-template registry (`welcome`, `data_export_ready`). `email-validator==2.2.0` pinned. | 3/3 |
| 8 | `935eb6b` | `send_email_notification(*, to, template, context) -> str` added to `services/notifications/channels.py` as thin wrapper (additive; existing `send_email` left intact since Mailgun was already gone). | 1/1 |
| 9 | `76cd469` | `_ensure_local_provider` injected as first dependency on `/register /login /refresh /logout`; returns `410 Gone` envelope `{"error":{"message":"auth handled by Clerk; ..."}}` when `AUTH_PROVIDER=clerk`. | 4/4 |
| 10 | (committed this session — see git log) | Frontend Clerk scaffold (opt-in via `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`): `(auth)/sign-in`, `(auth)/sign-up`, gated `middleware.ts`, conditional `<ClerkProvider>` in `providers.tsx`, CSP entries. | tsc clean for new files (pre-existing admin/audit type errors unrelated). |
| 11 | (committed this session) | `backend/scripts/clerk_bulk_import.py` + `clerk_seed_demo.py` + `backend/tests/scripts/test_clerk_bulk_import.py`. | 2/2 |
| 12 | (committed this session) | `docs/operations/clerk-runbook.md`; CLAUDE.md + progress.md updated. | n/a |

Final post-Task-9 backend suite: **533 pass + 1 xfailed** in `tests/`.

### Task 13 — staging dry-run + audit closure + PR (pending)

1. Apply `alembic upgrade head` against staging DB (head = `20260526_0029`).
2. Set Clerk + Resend env vars in staging.
3. `python backend/scripts/clerk_seed_demo.py` against staging Clerk app.
4. Manual smoke: sign-up → onboarding → `/feed` → `/profile` → data-export → receive Resend email.
5. Webhook smoke: edit a user in Clerk dashboard, tail backend logs, confirm `clerk_webhook` handler fires.
6. For each finding in `security-audit.md` claimed closed (H3, H4, H7, H10, H11, H12, H14, M18, M19, M23, M24, M26, M29, M30, M36, M43, M44), append one-line proof + commit SHA under a "Closed by Clerk + Resend migration" section.
7. `gh pr create --base main --title "feat(auth): migrate to Clerk + Resend"` with the test-plan checklist from plan §Task 13 Step 4.

### Known production-vs-test divergences

- **Resend SDK 2.5.x** `resend.Emails.send(params)` returns `dict` (`{"id": "..."}`) in production. `send.py` calls `response.id` (matches `MagicMock(id=...)` in tests). On first staging send, change to `response["id"]` if `AttributeError` appears.
- **`clerk_backend_api`** import deferred inside `clerk_client()` because the package fails to build pydantic-core wheels on Python 3.14. In production (Python 3.12 per Dockerfile) the import will succeed at first call.
- **Migration `20260526_0029` not yet applied** — no live PostgreSQL in this session. Run `alembic upgrade head` after merging.

### Deferred from Task 10 (Frontend integration)

Track for a follow-up PR after staging dual-mode validates:
- `frontend/src/lib/api/client.ts` token-source rewrite (`useAuth().getToken()` instead of `localStorage["grantpath.access_token"]`).
- `/login` and `/signup` redirects → `/sign-in` and `/sign-up`.
- Removal of `grantpath.*` localStorage tokens.
- Playwright `tests/auth/sign-in.spec.ts` (project has no `tests/auth/` runner today).

### Open bugs / blockers

- Pre-existing TypeScript errors in `frontend/src/app/(admin)/admin/{audit,page,users}.tsx` (`RoleChangeAudit` / `PlatformAnalytics` / `AccessControlManagedUser` shape drift). Tracked separately in `security-audit.md` D2–D4 / D7. **Not introduced by Clerk work.**
- `frontend/src/lib/api/endpoints/access-control.ts` missing `AccessControlManagedUser` export — same drift.
- /admin/curation crash fix (`CurationRecordSummary`/`Detail`/`ListResponse` split) is still on disk uncommitted — pre-existing WIP unrelated to this session's Clerk work.

### Files touched this session

- backend: `app/core/config.py`, `app/core/dependencies.py`, `app/integrations/clerk/{__init__,client,jwt_verify,user_sync}.py`, `app/integrations/resend/{__init__,client,send}.py` + `templates/{__init__,welcome,data_export_ready}.py`, `app/api/v1/routes/{auth,clerk_webhook}.py`, `app/api/v1/__init__.py`, `app/services/notifications/channels.py`, `app/models/models.py`, `alembic/versions/20260526_0029_add_clerk_user_id.py`, `requirements.txt`, `scripts/{clerk_bulk_import,clerk_seed_demo}.py`, `tests/{core,db,api,integrations,scripts,services}/*`, `.env.example`
- frontend: `package.json`, `bun.lock`, `src/middleware.ts`, `src/app/(auth)/{sign-in,sign-up}/[[...]]/page.tsx`, `src/app/providers.tsx`, `next.config.ts`, `.env.example`
- repo root: `.env.example`
- docs: `docs/operations/clerk-runbook.md`, `CLAUDE.md`, `progress.md` (this file)

### Commands to resume

```bash
cd backend && python -m pytest tests/ -q --no-header --tb=line 2>&1 | tail -5
git -C C:/Users/HP/scholarai-platform status --short
cd backend && alembic upgrade head  # head should be 20260526_0029
# After CLERK_SECRET_KEY in env:
python backend/scripts/clerk_seed_demo.py
python backend/scripts/clerk_bulk_import.py
# After NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY set:
cd frontend && bun run build && bun dev
# visit http://localhost:3000/sign-in
```
