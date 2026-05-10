# GrantPath frontend

Next.js 16 + React 19 + Tailwind 4 client for the ScholarAI/GrantPath backend.

User-centric. Frictionless. Non-AI-sluggish.

## Stack

- Next.js 16 (App Router)
- React 19
- Tailwind 4 (v4 `@theme` block in `src/app/globals.css`)
- shadcn-style primitives over Radix
- @tanstack/react-query for data
- sonner for toasts
- Lucide for icons (no emojis as UI)
- Sora (display) + IBM Plex Sans (body) + IBM Plex Mono (data)

## Run

```bash
bun install
cp .env.example .env.local        # point at your backend
bun dev                           # http://localhost:3000
```

Backend default: `http://localhost:8000/api/v1`. Override with `NEXT_PUBLIC_API_BASE_URL`.

Demo creds (from backend env example):
- `student@example.com` / `strongpass1`
- `admin@example.com` / `strongpass1`

## Structure

```
src/
  app/                          App Router routes
    layout.tsx                  fonts, providers
    page.tsx                    marketing landing
    login, signup, onboarding   public + onboarding wizard
    (student)/                  role-guarded student shell
    (mentor)/                   role-guarded mentor shell
    (admin)/                    role-guarded admin shell
  components/
    ui/                         primitives (Button, Input, Card, Badge, Skeleton)
    shell/                      AppShell, Sidebar, TopBar, PlaceholderRoute
  lib/
    api/                        REST client + per-router endpoints
    auth/                       AuthProvider, RoleGuard
    theme/tokens.ts             colour, spacing, font tokens
    utils.ts                    cn(), formatDeadline(), formatAmount()
```

## Design rules (enforced in code review)

1. No emojis as UI. Lucide SVG only.
2. Validated facts visually distinct from AI-generated content (`validated.500` border vs `generated.500` + Sparkles icon).
3. No streaming-text theatre. REST returns full payload, render once.
4. Optimistic mutations on save / kanban move / profile edit. Rollback toast on failure.
5. Skeletons appear once per route load. Re-fetches update in place.
6. All primary actions tap-target ≥ 44×44.
7. `/` focuses search anywhere. `Esc` closes drawers.
8. Errors say what to do next: "Couldn't load. [Retry]"
9. Numbers > prose. "12 match your profile" beats "We found several scholarships."
10. Latency budgets: LCP < 1.8s on `/feed`, INP < 200ms on save toggle and kanban drag.

## Sprint status

- **S1 Foundation** — DONE: tokens, fonts, providers, api client, auth, RoleGuard, AppShell, route stubs, marketing/landing, signup/login, onboarding wizard, feed page wired.
- **S2 Auth + Onboarding** — feed empty state, profile edit page.
- **S3 Discover + Saved** — filter bar, scholarship cards, kanban tracker.
- **S4 Recommendations** — full rec card with stage chips and factor lists.
- **S5 Documents** — upload + four-partition feedback view.
- **S6 Interviews** — adaptive Q/A loop + rubric radar.
- **S7 Mentor** — pending queue + split-pane review.
- **S8 Admin / Curation** — ingestion run management + curation state machine.
- **S9 Owner / Health** — RBAC mutations + audit log + KPI dashboard.
- **S10 Polish** — a11y pass, responsive matrix, Playwright E2E, RBAC matrix test.
