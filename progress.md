# progress.md — 2026-05-18 (S89 + S89.1 cleanup pass)

**Date:** 2026-05-18
**Branch:** `feat/s89-premium-cultural`
**Alembic head:** `20260516_0026 (head)` — backend schema unchanged
**Commits this session:** S89.1 cleanup commit on top of `99cc4c7` (landing polish) and `cb9cfbb` (S89 base)

## Tasks completed this session (S89.1)

All open items from prior `progress.md` either shipped or documented with run-once recipe. Lint + tsc + build + emoji-grep across 121 files all green.

### P1 — Match-route alias

- `frontend/src/app/(student)/dashboard/scholarships/match/page.tsx` (new) — `export { default } from "@/app/(student)/scholarships/page"`. Unblocks sidebar (`Sidebar.tsx:57`), onboarding redirect (`onboarding/page.tsx:154`), `/feed` action tile + see-all link.

### P2 — StudentProfile type sync + /profile 6-card expansion

- `frontend/src/lib/api/types.ts` — `StudentProfile` grew from 10 to 28 fields, mirrors `backend/app/schemas/students.py:StudentProfileResponse` field-for-field. New string-literal aliases: `TargetDegreeLevel`, `HecDegreeLevel`, `CgpaScaleChoice`, `FundingRequirement`, `IntakeTarget`.
- `frontend/src/app/(student)/profile/page.tsx` — full rewrite, 6 cards per Front-upgrade §6.22:
  1. **Contact** — email (locked), citizenship select, city_of_origin
  2. **Academic record** — pakistani_university, hec_degree_level, cgpa_scale_choice, degree_subject, graduation_year, gpa + scale, target_degree_level
  3. **Test scores** — IELTS, TOEFL, GRE quant + verbal
  4. **Your goal** — target_countries multi-chip, target_fields multi-chip, intake_target, funding_requirement
  5. **Aspirations** — has_research_publications (Yes/No), conditional research_publication_count
  6. **Background** — can_afford_application_fees, needs_gre_waiver, family_has_funds_for_bank_statement (each Yes/No)
- `frontend/src/components/profile/MultiChip.tsx` (new) — multi-select chip group rendered as `<button role="checkbox" aria-checked>` with `<div role="group">` parent. Lapis-soft active fill, hairline neutral resting.
- `StickySaveFooter` retained from S89 (slides up when form dirty; PATCH on save; `recommendations` + `scholarships.match` queries invalidated after success).
- `toPayload` shapes single PATCH with both `target_country_code` (single) + `target_countries` (multi) so backend's reconcile model_validator stays happy.

### P3 — Admin repaint (8 routes)

Each route's `<header><h1 font-display text-3xl></h1></header>` swapped to `<PageHeader title= description= />` from `@/components/ui/section-header`. Original `<header>` retained with `sr-only` where it was wrapping form labels or paragraphs the screen-reader still needs. Touched:

- `frontend/src/app/(admin)/admin/page.tsx` (overview) — `data-testid="admin-overview"`, KPI numbers reshaped Fraunces 3xl → JBM 28/tabular-nums, `caution-stripe` utility on KPI alert card (replaces ad-hoc `border-l-4 border-l-caution`).
- `frontend/src/app/(admin)/admin/users/page.tsx`
- `frontend/src/app/(admin)/admin/audit/page.tsx`
- `frontend/src/app/(admin)/admin/rec-eval/page.tsx`
- `frontend/src/app/(admin)/admin/ingestion/page.tsx`
- `frontend/src/app/(admin)/admin/curation/page.tsx`
- `frontend/src/app/(admin)/admin/curation/[id]/page.tsx` — record-detail h1 now Fraunces 24 italic + JBM mono record-id eyebrow (matches `/documents/[id]` pattern).

### P4 — Mentor repaint (2 routes)

- `frontend/src/app/(mentor)/mentor/queue/page.tsx` — `PageHeader` + `data-testid="mentor-queue"`.
- `frontend/src/app/(mentor)/mentor/documents/[id]/page.tsx` — review h1 reshaped Fraunces 24 italic.

### P5 — Partners repaint (2 routes)

- `frontend/src/app/(partners)/partners/page.tsx` — `PageHeader` with `eyebrow="Institution"`, KPI numbers reshaped Fraunces 3xl → JBM 28/tabular-nums (3 stat cards), `data-testid="partners-overview"`.
- `frontend/src/app/(partners)/partners/universities/page.tsx` — `PageHeader`, `data-testid="partners-universities"`.

### P6 — Backend gap quick wins

- `backend/.env.example` — Mailgun keys (`MAILGUN_API_KEY` / `MAILGUN_DOMAIN` / `MAILGUN_BASE_URL` / `MAILGUN_TIMEOUT_SECONDS` / `BRAND_DISPLAY_NAME` / `EMAIL_FROM_LOCALPART`) + Sentry keys (`SENTRY_DSN` / `SENTRY_TRACES_SAMPLE_RATE` / `SENTRY_PROFILES_SAMPLE_RATE` / `SENTRY_ENVIRONMENT`) appended.
- `backend/app/core/config.py` — `SENTRY_DSN` / `SENTRY_TRACES_SAMPLE_RATE` / `SENTRY_PROFILES_SAMPLE_RATE` / `SENTRY_ENVIRONMENT` Settings fields added.
- `backend/app/main.py:_init_sentry()` — bundled `sentry-sdk[fastapi]==2.18.0` wired. Imports `sentry_sdk` + `FastApiIntegration` + `StarletteIntegration`. Reads DSN from settings; no-op when unset. `send_default_pii=False` per PDPB. Fail-soft on init error so an invalid DSN never blocks app boot. **Verified**: `python -c "from app.main import create_app; app = create_app(); print('OK', len(app.routes))"` returns `OK 112` with DSN unset.

### P7 — Deferred live-backend recipes documented

Two gates still require local docker compose stack + 3 green runs:

#### Audit recipe (full state-matrix against live backend)

```bash
# Terminal 1 — boot stack
docker compose up --build
# Wait for healthchecks (~2-3 min). OpenSearch needs DISABLE_SECURITY_PLUGIN=true
# (set in docker-compose.yml) or backend never reaches "alive".

# Terminal 2 — seed Pakistan demo (idempotent)
python backend/scripts/bootstrap_local.py
python backend/scripts/demo_seed_pakistan.py
# Confirm zara.khan@example.com exists, plan=elite, plan_expires_at=2099-12-31

# Terminal 3 — run audit
cd frontend
bun scripts/audit/emoji-grep.mjs              # sub-second, must be 0
bun run audit:public                          # no-auth subset first
bun run audit                                 # full matrix; writes audit-out/REPORT.md

# Inspect REPORT.md — every cell must be PASS (or WARN with explicit
# expected_phrases allowlist in scripts/audit/routes.mjs).
```

Acceptance: zero axe-serious / zero banned-phrase across all routes × viewports × states. Open `audit-out/REPORT.md` then `audit-out/<route>-<state>-<viewport>.png` for any FAIL.

#### Smoke gate flip recipe (`.github/workflows/ci.yml:198`)

```bash
# Stack must be running from the audit recipe above.

# Three consecutive green runs required:
python tests/e2e/playwright/run_smoke_suite.py
python tests/e2e/playwright/run_smoke_suite.py
python tests/e2e/playwright/run_smoke_suite.py

# After 3/3 green:
# 1. Update tests/e2e/playwright/*.py selectors to target the S89 testids
#    (saved-list / documents-list / discover-grid / interviews-list /
#     profile-form / settings-tabs / legal-doc / scholarships-list /
#     tracker-board / visa-setup-form / interview-session-shell /
#     admin-overview / mentor-queue / partners-overview).
# 2. Delete `continue-on-error: true` from .github/workflows/ci.yml:198 +
#    the TODO block at lines 192-197.
# 3. Keep `if: failure()` log-dump at lines 209-216.
# 4. Push as a separate one-line commit so revert is trivial if the gate
#    bites in the next 24h after merge.
```

Acceptance: `browser-smoke` CI step is a hard-fail gate; PRs touching auth / api / app-shell stop the merge button on failure.

### Earlier work this session (already in git)

S89 base (commit `cb9cfbb`, 2026-05-17): audit harness + 6 missing routes (404 / 500 / offline / denied / maintenance / legal[slug]) + /saved rewrite + /documents/new deletion + repaints across /documents, /documents/[id], /profile, /settings, /interviews, /scholarships/[id], /discover + 11 testids.

Landing polish (commit `99cc4c7`, 2026-05-18): hero 2-col + FAQ + closing CTA + lapis lift on 5 eyebrows.

## Tasks in progress

None.

## Open bugs / blockers

- Smoke selector re-point + CI flag removal (P7 above). Both gated by 3 green local runs against `docker compose up` — operator action.
- Prod Supabase has not yet been seeded with `AIRU2026` (`backend/scripts/seed_invite_codes.py` idempotent, awaits operator run before May-19 booth). Tracked in CLAUDE.md "Backend gap audit".
- `docs/scholarai/IMPLEMENTATION_STATUS_REPORT.md` predates Pakistan pivot + Q1 retier + S89. Long-form doc refresh deferred.

Carry-over from S89 base:
- `frontend/src/app/(student)/profile/page.tsx` field set still relies on backend reconciling single ↔ multi country + field. Backend tested green; frontend manual UAT recommended once docker compose is back up.
- `/dashboard/scholarships/match` resolves now via alias; if spec ever wants a distinct UI variant, the alias becomes a real page.

## Files touched this session (S89.1)

**Frontend new (2):**
- `frontend/src/app/(student)/dashboard/scholarships/match/page.tsx` — alias re-export
- `frontend/src/components/profile/MultiChip.tsx`

**Frontend modified (16):**
- `frontend/src/lib/api/types.ts` — StudentProfile expansion + 5 string-literal aliases
- `frontend/src/app/(student)/profile/page.tsx` — full rewrite to 6 cards
- `frontend/src/app/(admin)/admin/page.tsx` — PageHeader + KPI mono + caution-stripe + testid
- `frontend/src/app/(admin)/admin/users/page.tsx` — PageHeader
- `frontend/src/app/(admin)/admin/audit/page.tsx` — PageHeader
- `frontend/src/app/(admin)/admin/rec-eval/page.tsx` — PageHeader
- `frontend/src/app/(admin)/admin/ingestion/page.tsx` — PageHeader
- `frontend/src/app/(admin)/admin/curation/page.tsx` — PageHeader
- `frontend/src/app/(admin)/admin/curation/[id]/page.tsx` — Fraunces 24 italic detail h1
- `frontend/src/app/(mentor)/mentor/queue/page.tsx` — PageHeader + testid
- `frontend/src/app/(mentor)/mentor/documents/[id]/page.tsx` — Fraunces 24 italic detail h1
- `frontend/src/app/(partners)/partners/page.tsx` — PageHeader + KPI mono + testid
- `frontend/src/app/(partners)/partners/universities/page.tsx` — PageHeader + testid

**Backend modified (3):**
- `backend/.env.example` — Mailgun + Sentry keys
- `backend/app/core/config.py` — Sentry settings fields
- `backend/app/main.py` — `_init_sentry()` gated by SENTRY_DSN

**Docs (3):**
- `CLAUDE.md` — S89.1 section appended before S89
- `frontend/CLAUDE.md` — S89.1 row in sprint table (above S89)
- `progress.md` — this file (overwrite per device rule §2)

## Commands to resume

```bash
# Dev server
cd frontend && bun dev                                 # http://localhost:3000

# Frontend gates (all green)
bun run lint
bunx --bun tsc --noEmit
bun run build                                          # 36 routes (S89 35 + S89.1 alias 1)
bun run audit:emoji                                    # sub-second, 0 hits

# Backend smoke import (verifies Sentry stub boots clean)
cd backend && python -c "from app.main import create_app; app = create_app(); print('OK', len(app.routes))"

# Backend gates (when ready to push)
pytest tests/unit tests/integration -q
python scripts/docs_governance_check.py

# Audit + smoke gates (require docker compose — see P7 recipes above)
docker compose up --build
python backend/scripts/demo_seed_pakistan.py
bun run audit                                          # full state matrix
python tests/e2e/playwright/run_smoke_suite.py         # × 3
```

## Next session

Priority order:

1. **Run the audit + smoke recipes from P7** against `docker compose up`. Open `audit-out/REPORT.md` and fix any FAIL. After 3 green smoke runs, delete `continue-on-error: true` from `.github/workflows/ci.yml:198` as a one-line commit.
2. **Prod Supabase seed**: `DATABASE_URL=...supabase... python backend/scripts/seed_invite_codes.py` before the May-19 booth.
3. **`docs/scholarai/IMPLEMENTATION_STATUS_REPORT.md` refresh**: reflect alembic head `20260516_0026` + Pakistan-pivot endpoints + Q1 retier + Air-Uni cohort flow + S89 + S89.1.
4. **Trial-lifecycle integration test** — backend pytest covering signup → invite-redeem → plan flip → 30-day expire end-to-end.
5. **Burn-cap pruning task** — Celery beat `tasks.run_usage_ledger_prune` first of month, drop rows older than 13 months.

## Verdict

S89.1 cleanup pass **SHIPPED**. Every open item from prior `progress.md` either landed in code (P1–P6) or documented with a verbatim run-once recipe (P7). Frontend lint + tsc + build + emoji-grep all green. Backend `create_app()` boots clean with Sentry stub (112 routes, DSN unset). The two remaining gates (audit-matrix + smoke flag flip) are operator actions: they need the docker compose stack up, which this session intentionally did not start. Recipes are in P7 above — paste, run, then flip the flag.
