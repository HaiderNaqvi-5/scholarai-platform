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
- Sora (display) + IBM Plex Sans (body) + IBM Plex Mono (data) via `next/font`
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

## UI primitives

- `ui/button` (CVA, asChild Slot, `loading`, `tap-target`)
- `ui/input`, `ui/label` (Radix Label)
- `ui/card` (Card, CardHeader, CardTitle, CardDescription, CardBody, CardFooter)
- `ui/badge` (tones: validated, generated, caution, danger, neutral, ink)
- `ui/skeleton`
- `ui/dialog` (Radix Dialog wrapper — Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogClose). Used by admin/users + admin/audit modals.
- `ui/tabs` (Radix Tabs wrapper).
- `ui/select` (Radix Select wrapper). Forms still use native `<select>` where simpler — both are acceptable.

## Shared feature components

- `scholarship/ScholarshipCard` — generic list card (used by /discover).
- `scholarship/RecommendationCard` — feed card with stage chips, factor lists, expandable EligibilityMatrix.
- `scholarship/EligibilityMatrix` — 5-axis eligibility table comparing student profile vs scholarship rules.
- `interview/RubricRadar` — recharts radar over `InterviewRubricDimension[]`.

## Verification before marking work complete

- `bun run lint` — 0 errors
- `bun run build` — green; route count expected from current sprint
- `bunx --bun tsc --noEmit` — clean
- For UI work: visual check at 375 / 768 / 1024 / 1440 widths
- For mutations: confirm optimistic flow + rollback toast on simulated 4xx
- For new endpoints: confirm `lib/api/types.ts` matches backend response shape (curl against running backend)

@AGENTS.md
