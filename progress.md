# progress.md — handoff

**Date:** 2026-05-30
**Branch:** `s95/frontend-design-pass-wave2` (NEW — off `s94/frontend-design-pass` tip, rebased onto `s93/auth-tier-1` head `ad14fef`)
**Plan:** `~/.claude/plans/synthetic-popping-avalanche.md` (wave 2)

## Commits this session
- `f92b1e1` — Wave 2: tasteful autoplay rail + skeleton crossfade + FAQ chips + footer chip + spinner reduced-motion (8 files)
- (about to add: docs commit for CLAUDE.md S95 row + this progress.md)

## S94 commits (carried via rebase onto s93/ad14fef; original local s94 still safe)
- `477c875` (was `ada6d4e`) — docs handoff
- `822b884` (was `58d41e4`) — Phase 4 motion polish
- `dbf65c2` (was `c602006`) — competitor features + P1 fixes

The original `s94/frontend-design-pass` branch still exists locally with the pre-rebase shas and was never pushed.

## Gate status
- `bunx --bun tsc --noEmit` — clean
- `bun run lint` — green
- `bun run build` — green (41 routes, clean build from wiped `.next`)
- `bun run audit:emoji` — 0 banned (133 files)
- Browser verification (bundled chromium, dev :3000, backend :8000 healthy via `docker restart scholarai-platform-backend-1`): rail 18 cards, autoplay 0→272, hover-pause 272→272, Next click 272→568, reduced-motion 0→0 static, 0 console errors in both default and reduced-motion contexts. See `frontend/scripts/capture_wave2.py`.

## Completed this session (wave 2)
- **Phase A — tasteful autoplay rail** (`components/marketing/ScholarshipsRail.tsx`): `setInterval(5000ms)` → `scrollBy({behavior:"smooth"})` with wrap-around; pauses on hover (`onMouseEnter/Leave` on outer), focus (`onFocusCapture/BlurCapture`), off-screen (`IntersectionObserver` threshold 0.5), and a 4s grace window after any user wheel/touchstart/keydown; reduced-motion hard-stop via `useSyncExternalStore` (no setState-in-effect — eslint-clean). Always-visible prev/next chevron buttons (44×44, aria-labels) are the keyboard affordance. `tabIndex={0}` moved off the `<ul>`; `aria-live="off"`. Edge-fade mask preserved. **Deliberate brand-ban exception** recorded as user-approved (CLAUDE.md "no auto-scroll carousel"); WCAG 2.2.2 satisfied via pause-on-everything + visible controls.
- **Phase B — skeleton→content crossfade**: new `content-fade-in` `@utility` + `@keyframes` in `globals.css` (opacity-only). Applied to rail items, `/discover` results `<ul>`, `/feed` recs grid `<ul>`, `/admin` stat grid wrapper. Reduced-motion-safe via the existing global cap.
- **Phase C — FAQ topic chips** (`app/page.tsx`): each `FAQS` item now carries a `topic` field; renders inside `<summary>` as a `Badge tone="neutral"` chip alongside the question.
- **Phase D — footer refresh-chip** (`app/page.tsx`): new `LAST_UPDATED_ISO`/`LAST_UPDATED_LABEL` module constants drive BOTH the hero editorial "Updated" line and the footer; the footer line is now a `rounded-full bg-paper-white/10 px-3 py-1` mono pill with `CalendarRange` icon and `aria-label`. Single source kills the 2026-05-17 vs 2026-05-18 drift.
- **Phase E1 — spinner reduced-motion** (`components/ui/button.tsx`): spinner overlay gated `motion-reduce:hidden`; label wrapper gated `motion-safe:invisible` so reduced-motion users see the label (not a frozen empty button) during `loading`. Button still goes `disabled` + `aria-busy`.

## Deferred / open
- **Phase E2 (audit P1, separable):** keep-mounted exit motion for `OfflineBanner`, `consent/CookieBanner`, `consent/ConsentBar` (currently animate on enter only, unmount instantly). Plan explicitly allowed deferring if it grew; pattern is identical across the 3 files. Estimated 30–45 min.
- **`/discover` + `ScholarshipCard` lean-list contract drift** — decision (user, 2026-05-29): **enrich backend `GET /scholarships` list response** to include `funding/field_tags/degree_levels/amount`. Backend ticket; FE rail uses its own typed `listPublic()` and is unaffected.
- **Authed-surface verification** still blocked by `AUTH_PROVIDER=clerk` (seeded accounts have null `clerk_user_id`; `.env` lockdown). Sidebar/TopBar/role-mixing verified by tsc + shape, not live render.
- **CORS** for dev: backend currently allows `:3000` origin; if `bun dev` ends up on `:3001` (port 3000 taken), the rail fetch is CORS-blocked. Fix is to free port 3000 before starting `bun dev`.

## Stash to restore later (on s93)
On `s93/auth-tier-1` there are 4 in-progress tracked-file edits I stashed before checking out s94 → branching s95: `CLAUDE.md`, `CLERK_AUDIT.md`, `progress.md`, `security-audit.md`. Restore with:
```
git checkout s93/auth-tier-1
git stash pop  # stash@{0}: "wave1->wave2 transition: in-progress s93 docs"
```

## Files touched (wave 2)
Modified: `frontend/src/app/(admin)/admin/page.tsx`, `frontend/src/app/(student)/discover/page.tsx`, `frontend/src/app/(student)/feed/page.tsx`, `frontend/src/app/globals.css`, `frontend/src/app/page.tsx`, `frontend/src/components/marketing/ScholarshipsRail.tsx`, `frontend/src/components/ui/button.tsx`.
New: `frontend/scripts/capture_wave2.py`.

## Commands to resume
```
cd frontend
# ensure port 3000 is free (CORS allow-list)
bun dev
bunx --bun tsc --noEmit
bun run lint
bun run build
python scripts/capture_wave2.py  # verifies autoplay + hover-pause + reduced-motion
```

## Push when ready
```
git push -u origin s95/frontend-design-pass-wave2
```
