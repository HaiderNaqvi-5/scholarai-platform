# frontend/CLAUDE.md

Guidance for Claude Code sessions working inside `frontend/`.

For backend / repo-wide context (architecture, RBAC matrix, recommendation pipeline, curation state machine, push gate, demo accounts), see `../CLAUDE.md`.

## Identity

User-facing brand: **AidwiseAI**. Internal/repo brand: ScholarAI.

This directory is the result of a greenfield rebuild on branch `feat/frontend-greenfield` (commit `f01bc08`). The previous frontend (single `lib/api.ts`, per-route `dashboard/document-feedback/interview/curation/admin/mentor/owner` pages, "GrantPath AI" metadata, npm + package-lock) was wiped. Only `lib/theme/tokens.ts` survived.

## Stack

- Next.js 16.2 (App Router, Turbopack)
- React 19.2
- TypeScript 5
- Tailwind 4 (CSS-first `@theme` block in `src/app/globals.css`)
- shadcn-style primitives over Radix
- @tanstack/react-query for server state
- sonner for toasts
- Lucide React for icons (no emojis as UI)
- **Fraunces** (display, variable, italic on h1) + **Inter** (body, ss01/cv11) + **JetBrains Mono** (data) via `next/font`. Pre-S88: Sora + IBM Plex.
- Bun as canonical package manager and runtime; npm fallback supported

## Run

```bash
bun install
cp .env.example .env.local        # NEXT_PUBLIC_API_BASE_URL
bun dev                           # http://localhost:3000
bun run build                     # production build (must stay green)
bun run lint                      # eslint (must stay clean)
bunx --bun tsc --noEmit           # typecheck (must stay clean)
```

Demo creds (seeded by backend):
- `student@example.com` / `strongpass1`
- `admin@example.com` / `strongpass1`

API base default: `http://localhost:8000/api/v1`.

## Layout

```
src/
  app/
    layout.tsx                    fonts, providers
    globals.css                   Tailwind 4 @theme tokens
    page.tsx                      marketing landing
    login/  signup/  onboarding/  public + onboarding wizard
    (student)/                    role-guarded student shell
      feed/                       POST /recommendations live
      discover/                   placeholder → S3
      scholarships/[id]/          placeholder → S3
      saved/                      placeholder → S3 (kanban)
      documents/, documents/new, documents/[id]
      interviews/, interviews/[id]
      profile/, settings/
    (mentor)/                     role-guarded mentor shell
      mentor/queue/, mentor/documents/[id]/
    (admin)/                      role-guarded admin shell
      admin/, admin/ingestion(/[id]), admin/curation(/[id])
      admin/users/, admin/audit/, admin/rec-eval/
  components/
    ui/                           Button, Input, Label, Card, Badge, Skeleton
    shell/                        AppShell, Sidebar, TopBar, PlaceholderRoute
  lib/
    api/
      client.ts                   bearer + silent refresh + 401 retry, typed ApiError
      types.ts                    hand-synced backend Pydantic shapes
      endpoints/                  one file per backend v1 router (11 modules)
      index.ts                    barrel: `endpoints.<domain>.<method>`
    auth/
      AuthProvider.tsx            login/signup/logout/refreshUser
      RoleGuard.tsx               hasRole, ROLE_GROUPS = {student,mentor,admin,owner}
    theme/tokens.ts               colour, spacing, radii, shadows, fonts
    utils.ts                      cn(), formatDeadline(), formatAmount()
```

## Design rules (PR-blocking, mirrored in `../CLAUDE.md`)

1. **Validated facts visually distinct from AI-generated content.** Validated → `validated.500` left border + "Verified" badge + source link. AI-generated → `generated.500` left border + Sparkles (Lucide) icon + 1-line provenance. Never mix in a single paragraph.
2. **No emojis as UI.** Lucide SVG icons only. Single sparkle is allowed only as the AI partition badge, at 14px.
3. **No streaming-text theatre on REST data.** Recommendations + scholarship payloads render once. No fake typewriter effect.
4. **Skeleton once per route load.** No spinner-on-every-card. List re-fetches update in place.
5. **Optimistic mutations** on save toggle, kanban status change, profile edit. Rollback toast on failure.
6. **Keyboard first.** `/` focuses search anywhere. `Esc` closes any drawer. `j/k` to scroll cards (S3+).
7. **Errors say what to do next.** "Couldn't load. [Retry]" — never bare "Network error".
8. **Latency budgets:** LCP < 1.8s on `/feed` (3G simulated); INP < 200ms on save toggle, kanban drag, filter change.
9. **Bundle budget:** initial JS ≤ 180KB gzipped per route. Tree-shake Radix; no full-barrel imports.
10. **44×44 minimum tap targets** on every primary action. `prefers-reduced-motion` respected globally.

## Anti-AI-sluggish enforcement

- No model names anywhere in UI. No "Powered by …".
- No floating chat bubble. No "Ask AI" button on every page.
- Chat-as-default reserved for interview practice (F4) only — that surface fits the task.
- No prompt boxes. Replace "describe what you want…" with structured forms.
- No purple gradient + sparkle decoration. Single 14px Sparkles icon on AI partitions only.
- No long disclaimers. One-line caveat per AI block.
- Specific labels, not generic. "Ranking 247 scholarships" not "Thinking…".
- No "AI" in nav copy. Sidebar reads "Recommendations", "Feedback", "Practice".

## Persistence

- localStorage tokens: `grantpath.access_token`, `grantpath.refresh_token`, `grantpath.access_expires_at`. Owned by `lib/api/client.ts`.
- Onboarding draft: `grantpath.onboarding_draft` (JSON; cleared on successful submit).
- Drafts in document editor: per-document key (lands in S5).
- Cross-tab logout via `subscribeTokens` listener.

## API contract

- `lib/api/types.ts` is the authoritative frontend mirror of backend Pydantic schemas. Update this file (and only this file) when backend response shapes change.
- Endpoint modules return parsed JSON typed against `types.ts`. Do not parse responses elsewhere.
- For multipart (document upload), use `api.upload(path, FormData)`; do **not** set `Content-Type` manually.

## Sprint status

| Sprint | Scope | State |
|--------|-------|-------|
| S1 | Foundation: tokens, REST, AuthProvider, RoleGuard, AppShell, marketing/login/signup/onboarding/feed | **Done** (`f01bc08`) |
| S2 | Profile edit (optimistic, PUT /profile), Settings (sign out + account info) | **Done** |
| S3 | Discover (sticky filter bar + URL state), ScholarshipCard, Scholarship detail, Saved kanban (HTML5 drag, optimistic status) | **Done** |
| S4 | RecommendationCard with stage chips, supporting/limiting factors, expandable EligibilityMatrix (5 axes: citizenship/degree/GPA/field/language) | **Done** |
| S5 | Documents list, /documents/new (paste-or-upload + grounding selector + 5s autosave), /documents/[id] four-partition FeedbackPartition with auto-poll | **Done** |
| S6 | Interviews list (modes + analytics), session adaptive Q/A loop + RubricRadar (recharts) + trend chips + recommended focus | **Done** |
| S7 | Mentor queue, split-pane review form (summary/strengths/revision_priorities/caution_notes ListEditor) | **Done** |
| S8 | Admin ingestion (start/filter/bulk-retry/select), run detail (diagnostics + snapshot viewer/clear), curation list, curation detail (raw→validated→published with audit notes) | **Done** |
| S9 | Admin overview (KPI alerts polled 60s + stats grid), Users (role mutation Dialog w/ reason), Audit (revert Dialog), Rec-eval (benchmarks + per-case + aggregate) | **Done** |
| S10 | Polish: data-testid added (login-form, app-shell, name attrs); auth smoke re-pointed to /feed. **Remaining**: axe-core gate, responsive matrix at 375/768/1024/1440, full smoke selector re-point for documents/recs/curation/interview/curation, RBAC matrix Playwright spec | Partial |
| S88 | **Premium Cultural rebuild** (2026-05-17): tokens swap (ivory/ink-deep/lapis/gold-leaf/sindoor); fonts swap (Fraunces/Inter/JBM); UI primitives repainted (Button + lapis/gold/sindoor variants, Card + asPanel, Badge + Chip atoms, IconButton, EmptyState/ErrorState, SectionHeader/PageHeader, StatChip, Skeleton with opacity-pulse). 9 routes rebuilt: `/`, `/booth/air-university` (NEW), `/upgrade`, `/signup` (+invite chip + Air U fields), `/login` (CapsLock + rate-limit countdown), `/onboarding`, `/feed`. CookieBanner + CookiePreferences modal wired in `providers.tsx`. AidwiseAI metadata. Sidebar + TopBar repainted: lapis active nav, gold trial banner, ink-deep avatar pip, `/` keyboard shortcut. Visual audit script at `scripts/visual-audit.mjs` (Playwright headless, 375/1024/1440 viewports, console-error capture); screenshots to `audit-out/`. | **Done** |
| S20 | **Security hardening pass** (2026-05-18, branch `feat/s89-premium-cultural`, full audit in `SECURITY_AUDIT.md`): `next.config.ts:headers()` ships HSTS/X-Frame-Options DENY/X-Content-Type-Options/Referrer-Policy/Permissions-Policy/COOP/CSP per response. CSP `connect-src` honors `NEXT_PUBLIC_API_BASE_URL`; production drops `'unsafe-eval'` from `script-src`. Frontend `Dockerfile` migrated to `oven/bun:1-alpine` + `bun install --frozen-lockfile` for supply-chain hygiene; multi-stage; `tini` PID 1; non-root `nextjs` user (uid 1001); HEALTHCHECK via `wget /` every 30s. Backend side closes 11 P0+P1 items: SecurityHeadersMiddleware, TrustedHostMiddleware, account-lockout, sanitized Mailgun headers, /health KPI strip, etc. — see `SECURITY_AUDIT.md` for full table. | **Done** |
| S89.1 | **S89 cleanup pass** (2026-05-18, branch `feat/s89-premium-cultural`): match-route alias at `/dashboard/scholarships/match` re-exports `/scholarships` (unblocks sidebar 404 + onboarding redirect + feed links). `StudentProfile` type sync 10→28 fields mirroring backend `students.py`. `/profile` expanded 3→6 cards per §6.22: Contact / Academic record / Test scores / Your goal (multi-select chips for `target_countries` + `target_fields` via new `components/profile/MultiChip.tsx`) / Aspirations (research pubs) / Background (3 boolean financial-context flags). Admin (8 routes) + mentor (2 routes) + partners (2 routes) headers swapped to `PageHeader` primitive; KPI numbers in admin/overview reshaped from Fraunces 3xl → JBM mono 28/tabular-nums; `caution-stripe` utility on KPI alert card; testids added (`admin-overview`, `mentor-queue`, `partners-overview`, `partners-universities`). Backend gap quick wins: Mailgun + Sentry keys appended to `backend/.env.example` and `app/core/config.py`; `app/main.py:_init_sentry()` gated by `SENTRY_DSN` (no-op when unset, fail-soft on init error). | **Done** |
| S89 | **Premium Cultural pass + audit harness + missing routes** (2026-05-17 → 2026-05-18, branch `feat/s89-premium-cultural`): state-matrix runner under `scripts/audit/` (`@axe-core/playwright` a11y, copy-grep banned-phrase ledger, emoji-grep over `src/`, `page.route()` 402/500/empty/loading mocks, REPORT.md per route × viewport × state). 6 missing routes added: `/not-found`, `/error` + `/global-error`, `/offline`, `/denied`, `/maintenance`, `/legal/[slug]` (server-rendered against `GET /privacy/legal/{slug}` with print stylesheet + version chip + ToC). `OfflineBanner` + `ConsentBar` mounted globally. /saved rewritten Kanban→list + sort dropdown + inline Promote-to-tracker (mutation pattern preserved). `/documents/new` deleted (not in IA §3.1). /documents repaint (Add dropdown, URL-stateful filter chips, table at lg+, status labels Draft/Final). /profile + /settings repaint (PageHeader, StickySaveFooter, 6-tab settings with TypedConfirm DELETE MY ACCOUNT pattern + privacy + data export + 30-day cancel deletion wiring). /interviews list TrendStrip + RubricSparkline. /scholarships/[id] sticky AsideAtAGlance ("Estimated Scholarship Fit Score" verbatim). /discover Pagination component. 11 data-testids backfilled. **Landing polish (2026-05-18):** hero 2-col at lg+ with right editorial preview card, 6-Q FAQ via native `<details>`, closing CTA before footer, lapis-lifted eyebrows. New primitives: `components/ui/pagination.tsx`, `consent/ConsentBar.tsx`, `legal/LegalViewer.tsx`, `interview/TrendStrip.tsx` + `RubricSparkline.tsx`, `scholarship/AsideAtAGlance.tsx`, `profile/StickySaveFooter.tsx`, `settings/TypedConfirm.tsx`, `system/OfflineBanner.tsx` + `SystemErrorLayout.tsx`, `saved/SavedRow.tsx` + `SortDropdown.tsx`. New endpoint module `lib/api/endpoints/legal.ts` (consent state + grant + data-export + account-deletion). Smoke selector re-point + `.github/workflows/ci.yml:198` `continue-on-error` removal deferred until 3 green local runs (plan mitigation #3). | **Done** |

## UI primitives (post-S88)

- `ui/button` (CVA, asChild Slot, `loading`, sizes sm/md/lg/icon, variants: `primary` / `lapis` / `secondary` / `ghost` / `danger` / `gold` / `validated` / `link`).
- `ui/icon-button` (square 44×44, tones `ghost` / `solid` / `danger`, required `aria-label`).
- `ui/input` + `ui/textarea` (10 radius, lapis focus ring, tap-target).
- `ui/card` (`Card`, `CardHeader`, `CardTitle`, `CardEyebrow`, `CardDescription`, `CardBody`, `CardFooter`; `hoverable` lifts shadow; `asPanel` upgrades to 22 radius + 24 padding).
- `ui/badge` + `ui/chip` (tones: neutral, validated, generated, caution, sindoor, lapis, gold, ink, live, outline).
- `ui/skeleton` (`Skeleton` opacity-pulse shapes block/text/circle; `SkeletonText`; `SkeletonCard`).
- `ui/states` (`EmptyState`, `ErrorState` — no illustration ever).
- `ui/section-header` (`PageHeader` for route h1; `SectionHeader` for in-page h2).
- `ui/stat-chip` (mono numeral + ink-muted label, used on marketing surfaces).
- `ui/dialog` (Radix Dialog wrapper — Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogClose). Used by admin/users + admin/audit modals.
- `ui/tabs` (Radix Tabs wrapper).
- `ui/select` (Radix Select wrapper). Forms still use native `<select>` where simpler — both acceptable.
- `consent/CookieBanner` (bottom sheet + CookiePreferences modal, persists `aidwise.cookie_consent` localStorage).
- `consent/ConsentBar` (post-S89, sticky bottom — polls `/privacy/consent` every 5min, surfaces on terms/privacy version mismatch, POSTs `/privacy/consent` on agree, persists agreed versions to `aidwise.consent_versions`).
- `system/OfflineBanner` (post-S89, fixed top — `useSyncExternalStore` over `navigator.onLine`; sindoor-soft offline / validated-soft "back online"; hidden on `/offline`).
- `ui/pagination` (post-S89, prev/numbered/next with ellipsis ≥5 pages, URL-stateful when wired with `router.replace`).

## Shared feature components

- `scholarship/ScholarshipCard` — generic list card (used by /discover).
- `scholarship/RecommendationCard` — feed card with stage chips, factor lists, expandable EligibilityMatrix.
- `scholarship/EligibilityMatrix` — 5-axis eligibility table comparing student profile vs scholarship rules.
- `interview/RubricRadar` — recharts radar over `InterviewRubricDimension[]`.
- `interview/TrendStrip` + `interview/RubricSparkline` — post-S89, /interviews list trend strip (5 rubric chips + mono sparkline).
- `scholarship/AsideAtAGlance` — post-S89, sticky right aside on /scholarships/[id] (deadline / funding / Estimated Scholarship Fit Score / source).
- `legal/LegalViewer` + `legal/markdown` — post-S89, server-rendered legal doc with version chip + ToC + minimal markdown→block parser (no runtime dep).
- `profile/StickySaveFooter` — post-S89, reusable dirty-state footer for /profile + /settings.
- `settings/TypedConfirm` — post-S89, typed-confirm dialog ("DELETE MY ACCOUNT" verbatim).
- `saved/SavedRow` + `saved/SortDropdown` — post-S89, list-row + kebab menu replaces /saved Kanban.

## Verification before marking work complete

- `bun run lint` — 0 errors
- `bun run build` — green; route count expected from current sprint
- `bunx --bun tsc --noEmit` — clean
- For UI work: visual check at 375 / 768 / 1024 / 1440 widths
- For mutations: confirm optimistic flow + rollback toast on simulated 4xx
- For new endpoints: confirm `lib/api/types.ts` matches backend response shape (curl against running backend)
- For audit harness: `bun run audit:emoji` (sub-second, source-only) + `bun run audit:public` (no auth) + `bun run audit` (full matrix, requires backend + zara persona)

@AGENTS.md
