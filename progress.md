# progress.md — handoff

**Date:** 2026-05-29
**Branch:** `s94/frontend-design-pass` (off `s93/auth-tier-1`)
**Plan:** `~/.claude/plans/synthetic-popping-avalanche.md` (frontend design pass: patch P0/P1/P2 audit findings + 3 competitor features)

## Commits this session (branch `s94/frontend-design-pass`)
- `c602006` — Phase 1/2/3-core: competitor features + P1 fixes (29 files)
- `58d41e4` — Phase 4 motion polish (5 files)

## Gate status (this session)
- `bunx --bun tsc --noEmit` — clean
- `bun run build` — green (41 routes, clean build from wiped `.next`)
- `bun run lint` — green (exit 0, after final Phase 4 edits)
- `bun run audit:emoji` — clean (0 banned emoji, 133 files)
- `bun run audit:public` — could NOT run: harness Playwright launches system Chrome, which timed out at launch (60s) in this env. Not a copy failure — checks never executed. Manual em-dash + emoji sweeps done instead.
- Browser verification (bundled chromium via `frontend/scripts/capture_phase12.py`, `capture_phase3.py`, `crop_rail.py`): landing + login at 375/768/1440, pricing + password-meter states. 0 console errors. Screenshots in `frontend/audit-out/phase12/`.

## Completed this session

### Phase 1 (P0) — done prior session, verified this session
12 P0 fixes (mobile nav drawer, login split, em-dash sweep, onboarding "Other"+GPA preview, admin type-drift, devIndicators, GlobalAuthNav, etc.). Build/tsc green.

### Phase 2 (competitor features) — DONE + browser-verified
1. Outcome-framed CTAs: nav/hero "See my matches"; comparison + closing CTA "Show scholarships I qualify for".
2. Comparison table (Lahore consultant vs AidwiseAI: cost/turnaround/coverage/SOP authorship/transparency) before pricing — `src/app/page.tsx`.
3. Live scrollable scholarships rail — `src/components/marketing/ScholarshipsRail.tsx`. Real backend data (Edinburgh/Toronto/Melbourne/TU Delft…), horizontal scroll-snap, keyboard-focusable, edge-fade mask, **no autoplay**, skeleton while loading.
- Reviewer-flagged fix: `RoleChangeAudit` type drift synced to backend `AccessControlRoleChangeItem` (`previous_role`/`next_role`/`action`/`is_reversible`/`reverted_by_audit_id`); `(admin)/admin/audit/page.tsx` updated.
- `GlobalAuthNav` 44px tap targets.

### Phase 3 (P1) — core done (8 items) + 2 verified-already-satisfied
1. Sidebar "Matches" icon `Sparkles`→`Target` (Sparkles reserved for 14px AI-partition badge per CLAUDE.md).
2. `RotatingDegree`: `min-w-[5ch]`→`[10ch]` (no width jump on "bachelor's"), reduced-motion now fully static, blur-bridge cross-fade.
3. `Button` loading: spinner is absolute-overlay + label held via `invisible` wrapper — no label jolt / width shift.
4. `TopBar` alert-bell: persistent for admins (muted when 0, caution+count when >0) — no 60s-poll layout shift.
5. Password meter (`signup/page.tsx`): renders only after first keystroke, scaleX bar fill, inline per-criterion check pills. `passwordScore` extended with `checks[]`.
6. Role-mixing fix: new `primaryGroup(role)` in `RoleGuard.tsx`; Sidebar + MobileNav show ONLY the user's section group (admin/owner no longer see student+mentor+partner union).
7. Banner enter motion: new `slide-in-top`/`slide-in-bottom` utilities in `globals.css`; OfflineBanner (top), CookieBanner + ConsentBar (bottom).
8. Elite pricing-cell drench: `PricingTeaser` gains `drench` prop → ink-deep bg, paper-white text, gold-soft check pips, gold CTA. Breaks flat 3-cell grid.
- Em-dash sweep extended: signup editorial copy + landing aria-label.
- Verified already satisfied: ConnectedAccountsPanel tap targets (sm button carries `tap-target`=44×44); contrast tokens (globals already AA).

## Discovered pre-existing bug (NOT fixed — flagged, separate ticket)
`/discover` + `ScholarshipCard` read `s.id`/`s.provider`/`s.field_tags`, but `GET /scholarships` returns lean `ScholarshipListItem` (`scholarship_id`/`provider_name`/`deadline_at`/`record_state` only). `/discover` **crashes on live data** (`s.field_tags.length` on undefined). The rich card cannot be populated by the lean list endpoint. **DECISION (2026-05-29, user):** fix via **enriching the backend `GET /scholarships` list response** (add funding/field_tags/degree_levels/amount to `ScholarshipListItem`) — a BACKEND ticket, out of this FE pass. Do NOT rewrite `/discover` or `ScholarshipCard` here. Matches CLAUDE.md tracked "Outstanding drift" D-class. Marketing rail uses its own correctly-typed `scholarships.listPublic()` so it works regardless. New FE types: `ScholarshipListItem`, `ScholarshipListItemResponse` in `types.ts` (will need extending once backend enriches).

## Open bugs / blockers
- Live AUTHED surface re-capture still blocked: `AUTH_PROVIDER=clerk`, seeded accounts have null `clerk_user_id`, `.env` lockdown prevents toggling to local mode. Admin/mentor/student shells (Sidebar/TopBar/role-mixing) verified by tsc + shape, not live render.
- `audit:public` harness can't launch system Chrome in this env (60s timeout).

### Phase 4 (P2 motion polish) — DONE + verified
Scroll-driven progress bar on landing (progressive `@supports (animation-timeline: scroll())` + reduced-motion gate; verified scaleX(0.59) at 55% scroll, 0 console errors), CTA trailing-arrow nudge (`.arrow-nudge`, `@media (hover:hover)`), search `/`-hint `peer-focus:opacity-0`, sidebar shortcut-kbd now `opacity-0 group-hover:opacity-100` (no display-toggle layout shift). New CSS in `globals.css`.

## In progress / next steps
- **Remaining P2 nits (optional):** skeleton→content crossfade (`@starting-style`), FAQ answer-preview + topic chips, footer refresh-chip framing. Lower value; safe to defer.
- **Phase 5:** manual viewport matrix walk at 375/768/1024/1440 (public surfaces captured; authed surfaces blocked by clerk). CLAUDE.md S94 row + this file updated.
- (Plan's "2px lapis active rail" intentionally SKIPPED — conflicts with impeccable side-stripe ban; kept `bg-lapis-soft` active fill.)

## Environment notes
- Backend container `scholarai-platform-backend-1` was "Up (unhealthy)"/hung → `docker restart` revived it (livez 200 after 30s). Postgres/Redis healthy. Public `/scholarships` returns 18 published items.
- `bun run build` while `bun dev` runs corrupts `.next/dev/types` (TS1002 "Unterminated string literal") — stop dev + wipe `.next` before clean tsc/build.

## Files touched (frontend)
Modified: `next.config.ts`, `app/(admin)/admin/{page,users/page,audit/page}.tsx`, `app/globals.css`, `app/layout.tsx`, `app/login/page.tsx`, `app/onboarding/page.tsx`, `app/page.tsx`, `app/signup/page.tsx`, `components/consent/{ConsentBar,CookieBanner}.tsx`, `components/marketing/RotatingDegree.tsx`, `components/shell/{Sidebar,TopBar}.tsx`, `components/system/OfflineBanner.tsx`, `components/ui/button.tsx`, `lib/api/endpoints/{access-control,scholarships}.ts`, `lib/api/types.ts`, `lib/auth/RoleGuard.tsx`.
New: `components/marketing/ScholarshipsRail.tsx`, `components/shell/{GlobalAuthNav,MobileNav}.tsx`, `scripts/{capture_phase12,capture_phase3,crop_rail}.py`.

## Commands to resume
```
cd frontend
bun dev                     # http://localhost:3000 (stop before build)
bunx --bun tsc --noEmit
bun run lint
bun run build
python scripts/capture_phase12.py   # public-surface capture (server must run)
```
