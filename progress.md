# progress.md — 2026-05-18 (S89.2 landing rotator + IP currency)

**Date:** 2026-05-18
**Branch:** `feat/s89-premium-cultural`
**Head:** `7b85c46` (pushed to `origin/feat/s89-premium-cultural`)

## Completed this session

1. **Hero degree rotator** (`frontend/src/app/page.tsx:151` + new `frontend/src/components/marketing/RotatingDegree.tsx`)
   - h1 cycles `bachelor's → master's → PhD`
   - Opacity-only transition (320ms cross-fade, 2.2s hold)
   - `aria-live="polite"`, `aria-atomic="true"`
   - `prefers-reduced-motion`: no fade, instant swap
   - `min-w-[5ch]` reserves layout to prevent jump
   - Hero `max-w` bumped 14ch → 16ch to fit longest word

2. **Auto IP-based currency on /upgrade** (new `frontend/src/lib/geo/useGeoCurrency.ts` + edits to `frontend/src/app/upgrade/page.tsx`)
   - Hook fetches `https://ipwho.is/?fields=success,country_code,currency` once
   - 24h `localStorage` cache key `aidwise.geo_currency`
   - Maps `currency.code` to supported set (PKR/GBP/EUR/AED/USD); falls back via `defaultCurrencyForCountry(country_code)` then PKR
   - Aborts on unmount via `AbortController`
   - `CurrencySwitcher` 5-button radiogroup → `DetectedCurrency` chip (Globe2 icon + source label + currency code)
   - Precedence: `?currency=` query > `auth.user.plan_currency` > geo > PKR fallback
   - Error-state "Show in PKR" button preserved via internal `fallbackOverride` state

3. **Stripe consistency** (`frontend/src/app/(mentor)/mentor/documents/[id]/page.tsx:201`)
   - `ListEditor` danger tone swapped raw `border-l-2 border-l-danger pl-3` for the existing `danger-stripe` `@utility`
   - All three tones (validated / caution / danger) now share 3px stripe geometry from `globals.css`

4. **Page audit** (read-only)
   - `bun run audit:emoji` — 0 hits across 123 files
   - Grep scan: 0 `bg-clip-text` + gradient combos, 0 heavy `backdrop-blur-(xl|2xl|3xl)`, 0 heavy `shadow-(xl|2xl)` / `ring-(4|8)`
   - 1 raw side-stripe found → fixed (see #3)

5. **Doc upkeep**
   - Root `CLAUDE.md` — added S89.2 section, compressed S89/S89.1 (199 lines, under 200 budget)
   - `frontend/CLAUDE.md` — S89.2 row appended to sprint table; new "Geo / locale hooks" section; `marketing/RotatingDegree` listed under Shared feature components (185 lines)

## In progress

None. S89.2 closed.

## Open bugs / blockers

None new. Pre-existing deferreds carry over from S89/S89.1:
- Smoke selector re-point in `tests/e2e/playwright/*.py`
- Removal of `.github/workflows/ci.yml:198` `continue-on-error: true` on `browser-smoke`
- Both require 3 consecutive green local runs against `docker compose up`

## Files touched (this session, staged + committed)

Commit `02bc5bb` — `feat(landing+upgrade): rotating hero degree + IP-based currency`
- `frontend/src/app/page.tsx` (modified)
- `frontend/src/app/upgrade/page.tsx` (modified)
- `frontend/src/components/marketing/RotatingDegree.tsx` (new)
- `frontend/src/lib/geo/useGeoCurrency.ts` (new)

Commit `7b85c46` — `refactor(mentor): use danger-stripe utility in ListEditor`
- `frontend/src/app/(mentor)/mentor/documents/[id]/page.tsx` (modified)

Untracked / unstaged pre-existing files left in tree (NOT part of this session, kept via `git stash` round-trip during rebase):
- `.do/`, `Elite vs pro for Q1.md`, `Front-upgrade.html`, `Front-upgrade.legacy.md`, `STITCH_PROMPT_PACK.md`, `backend/app/core/account_lockout.py`, `frontend/.dockerignore`, `frontend/Dockerfile`
- Modified but unstaged: `.github/workflows/ci.yml`, `backend/.env.example`, `backend/app/core/config.py`, `backend/app/main.py`, `backend/app/schemas/auth.py`, `backend/app/services/auth/service.py`, `backend/app/services/notifications/channels.py`, `frontend/next.config.ts`, `frontend/src/app/signup/page.tsx`, `frontend/src/lib/api/endpoints/auth.ts`, `frontend/src/lib/auth/AuthProvider.tsx`

## Commands to resume

```bash
# Run
cd frontend && bun dev                  # http://localhost:3000
cd backend && python -m uvicorn app.main:app --reload   # :8000

# Verify
cd frontend && bun run lint              # 0 errors
cd frontend && bunx --bun tsc --noEmit   # clean
cd frontend && bun run build             # 40 routes, green
cd frontend && bun run audit:emoji       # 0 emoji

# Live visual audit (requires docker compose up + zara.khan seeded)
cd frontend && bun run audit             # writes audit-out/REPORT.md

# Test the rotator
open http://localhost:3000               # h1 cycles bachelor's → master's → PhD every ~2.5s

# Test geo currency
open http://localhost:3000/upgrade                       # detects via IP
open http://localhost:3000/upgrade?currency=GBP          # override path
# To retest detection from scratch:
# localStorage.removeItem("aidwise.geo_currency")
```

## Verification log

| Gate | Result |
|------|--------|
| `bun run lint` | exit 0 |
| `bunx --bun tsc --noEmit` | exit 0 |
| `bun run build` | 40 routes, "Compiled successfully" |
| `bun run audit:emoji` | 0 banned emoji / 123 files |
| Side-stripe grep | 0 raw hits after stripe-utility refactor |
| Gradient-text grep | 0 hits |
| Push | `02bc5bb..7b85c46` → `origin/feat/s89-premium-cultural` |
