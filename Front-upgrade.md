# Front-upgrade — AidwiseAI Frontend Design Specification

> Purpose-built design spec. Every screen designed from intent, every state declared, every word audited.
> Audience: a frontend engineer building AidwiseAI from cold, with no prior context.
> Brand (public): **AidwiseAI**. Repo/internal: ScholarAI.
> Date of authorship: 2026-05-17. Version: v4 (purpose-built rewrite).

---

## §0 Document Purpose & How to Read

This document is the single source of frontend truth. It supersedes all prior frontend planning notes. It does **not** describe what currently exists in the codebase — it describes what the product **must be**. Where the spec and the code disagree, the code is wrong.

**Reading order.**
1. §1 (voice) and §2 (foundations) are mandatory pre-reading. Every other section assumes them.
2. §3 (IA) gives the route map. Pick a route, jump to its §6 entry.
3. §4 (components) is the parts list — read on-demand.
4. §5 (flows) ties screens together. Read before building any cross-screen feature.
5. §6 is the bulk. Each screen entry uses the same template (Purpose → Users → Backend → Anatomy → States → Interactions → Motion → Anti-slop → Copy → A11y → Responsive → Telemetry).
6. §7–§11 are quality gates: copy register, motion spec, a11y, perf, delivery checklist.

**Conventions.**
- Code identifiers are `inline`. Token names are `--like-this`. Routes are `/like/this`. Components are `PascalCase`.
- Measurements without units are pixels.
- "Locked" = freemium-paywalled. "Verified" = backend-validated structured data. "Generated" = AI-drafted prose.
- All copy quoted in this doc is verbatim production copy unless prefixed `e.g.`.

---

## §1 Brand Voice & Anti-Slop Charter

### 1.1 Voice

AidwiseAI speaks like a senior scholarship advisor in a university common room: **plain, grounded, specific, calm**. Never breathless. Never anthropomorphic about the model. Never apologetic. Names actions, not technologies.

**Four voice principles.**

1. **Specific over generic.** Replace adjectives with numbers and proper nouns. "47 fully-funded master's programs in the UK" beats "many scholarships". "Drafting your SOP — 4 paragraphs left" beats "AI is working its magic".
2. **Name the action, not the technology.** "Generate matches" not "AI-powered match". "Draft your SOP" not "AI essay assistant". The user does not care which model runs.
3. **No theatre.** No fake progress, no "thinking…", no shimmer-while-empty, no anthropomorphism ("I'm working on it"). Real progress or real silence.
4. **Pakistan-grounded.** Use NUST, LUMS, FAST-NUCES, IBA, HEC, Chevening, Fulbright, DAAD, Commonwealth as default examples. Never Stanford / MIT / Harvard as filler.

### 1.2 Tense, person, register

- Second person (you / your) for user-facing copy. First-person plural (we) only in legal / explicitly editorial contexts.
- Present tense for state ("Your trial ends in 4 days"). Imperative for actions ("Add a scholarship").
- Sentence case for everything except brand names. Never Title Case For UI Strings.
- Numbers as digits from 1 onward (1, 2, 7, 42, 1,500). Spell out "one" only when used as a pronoun ("only one left").

### 1.3 Global ban ledger (every screen inherits)

**Banned phrases.** `Unlock`, `Unleash`, `Magic`, `Magical`, `AI is thinking`, `AI is generating`, `Powered by AI`, `Revolutionary`, `Game-changing`, `Seamlessly`, `Leverage`, `Synergize`, `Next-generation`, `World-class`, `Cutting-edge`, `Reimagined`, `Reinvented`, `Smart` (as adjective for software), `Effortless`, `Just a moment`, `Hang tight`.

**Banned visual.** Gradient mesh background, neon glow, animated gradient text, blob shapes, sparkle particles, hand-drawn arrows, sparkle iconography, "as seen on" logo wall without source link, 3D-render hero images, glassmorphism on the page background, blur over a busy background.

**Banned motion.** Bounce on hover, scale-up on hover that shifts layout, parallax on scroll, marquee logo strips, auto-play carousels, fake typewriter on static text, particle backgrounds.

**Banned components.** Emoji-as-icon (🚀 ✨ 🎉 🔥 ⚡), spinner-per-card, infinite-scroll without pagination fallback, modal-stacking more than 1 deep, full-page loaders on route change after first paint, toast-stacks more than 3 deep.

**Banned copy patterns.** Passive voice on CTAs ("Your matches will be loaded" → use "Show my matches"). Apology-as-microcopy ("Sorry we couldn't…"). Anthropomorphism ("Our AI thinks…"). Generic empty states ("No data" → name what's missing).

### 1.4 Allowed exemplars

| Bad (banned)                                  | Good (replace with)                                                    |
|-----------------------------------------------|------------------------------------------------------------------------|
| "Unlock premium scholarships"                 | "See all 47 matches with Pro"                                          |
| "AI is generating your SOP…"                  | "Drafting paragraph 2 of 5"                                            |
| "Hang tight while we work our magic ✨"        | "Searching 30 universities. ~15 seconds."                              |
| "Powered by AI"                               | (delete; the user does not care)                                       |
| "Effortlessly track your applications"        | "Track 6 applications across 6 stages"                                 |
| "Seamlessly integrate with…"                  | (delete; describe the integration instead)                             |
| "No data"                                     | "No applications yet. Add your first."                                 |

### 1.5 Per-screen ban-list discipline

Every §6 entry adds **3–5 surface-specific bans** beyond the global ledger. The SOP builder bans `AI is writing`, `Generating brilliance`, spinner-per-paragraph. The Visa simulator bans `Interview Coach AI`, applause-emoji on scores, country-flag emoji. The Tracker bans `Smart pipeline`, animated trophy on accepted column.

---

## §2 Design Foundations

### 2.1 Color System (Premium Cultural)

The system reads as a heritage scholarship publication — ivory paper, ink-deep print, lapis serif accents, gold leaf for premium, sindoor for urgency. One accent per screen. Color carries semantic weight (validated, generated, caution, danger); it is never decoration.

**Token table.**

| Token              | Hex / value                            | Role                                                    |
|--------------------|----------------------------------------|---------------------------------------------------------|
| `--ivory`          | `#FBF7EE`                              | Page background                                         |
| `--paper-warm`     | `#F3ECDC`                              | Section fills, hover surfaces                           |
| `--paper-edge`     | `#E5DAC2`                              | Dividers, skeleton base                                 |
| `--paper-white`    | `#FFFDF9`                              | Card + input surface                                    |
| `--ink-deep`       | `#0E1A1F`                              | Primary heading, primary button background              |
| `--ink`            | `#1B2630`                              | Body heading                                            |
| `--ink-muted`      | `#4A5663`                              | Body text                                               |
| `--ink-subtle`    | `#6E7984`                              | Captions, placeholder, helper                           |
| `--lapis`          | `#1B3A6B`                              | Primary action accent, link, AI-generated content       |
| `--lapis-soft`     | `#DCE3EE`                              | Lapis tint background                                   |
| `--gold-leaf`      | `#B08A3E`                              | Premium / Elite tier, trial countdown                   |
| `--gold-soft`      | `#F1E6CA`                              | Gold tint background                                    |
| `--sindoor`        | `#B94A48`                              | Destructive, deadline <14 days, errors                  |
| `--sindoor-soft`   | `#F2D9D5`                              | Sindoor tint background                                 |
| `--validated`      | `#426B5A`                              | Verified eligibility, success, validated data stripe    |
| `--validated-soft` | `#DDE9E2`                              | Validated tint background                               |
| `--generated`      | `#2E5B9A`                              | AI-drafted content stripe                               |
| `--generated-soft` | `#DCE6F4`                              | Generated tint background                               |
| `--caution`        | `#B7791F`                              | Warnings, partial eligibility                           |
| `--caution-soft`   | `#F4E7CF`                              | Caution tint background                                 |
| `--border-hair`    | `rgba(14,26,31,0.10)`                  | Card / input / divider borders                          |
| `--border-quiet`   | `rgba(14,26,31,0.06)`                  | Subtle dividers within cards                            |
| `--focus-ring`     | `rgba(27,58,107,0.32)`                 | Focus outline                                           |
| `--scrim`          | `rgba(14,26,31,0.48)`                  | Modal scrim                                             |

**Semantic stripes.** Validated content carries a 3px left border in `--validated`. Generated content carries a 3px left border in `--generated`. Caution carries `--caution`. Danger carries `--sindoor`. Never combine two stripes on the same card.

**Color contrast.** All body text vs background ≥ 4.5:1. All UI text on accent tints ≥ 4.5:1. Verified pairs: `--ink` on `--ivory` 13.9:1, `--ink-muted` on `--ivory` 7.2:1, `--ink-subtle` on `--paper-warm` 4.6:1, `--paper-white` on `--ink-deep` 17.2:1, `--paper-white` on `--lapis` 8.1:1, `--paper-white` on `--gold-leaf` 4.6:1 (use only on chips, never body text).

**Dark mode.** Out of scope for v1. Foundation reserved: `--ink-deep` becomes background, `--paper-white` becomes text. Do not ship dark mode without rerunning contrast pass on every token.

### 2.2 Typography

**Families.**
- **Display:** Fraunces (variable: opsz 9..144, wght 300..700, SOFT 0..100). Italic enabled by default on display h1. Variant settings: `opsz auto` via CSS `font-optical-sizing: auto`, `SOFT 30`.
- **Body:** Inter (variable: wght 100..900). Stylistic sets `ss01` (single-storey a) and `cv11` (tabular dotted zero in data) enabled globally on body.
- **Data / mono:** JetBrains Mono (wght 400 / 500). Used for codes, deadlines, currencies, IDs, keyboard shortcuts, file paths in admin.

**Scale.**

| Token         | Size px | Line height | Use                                                     |
|---------------|---------|-------------|---------------------------------------------------------|
| `text-3xs`    | 11      | 1.4         | Microlabels, table headers (uppercase + 0.06em tracking) |
| `text-2xs`    | 12      | 1.45        | Captions                                                |
| `text-xs`     | 13      | 1.5         | Helper, badge text                                      |
| `text-sm`     | 14      | 1.55        | Card descriptions, dense UI                             |
| `text-base`   | 15      | 1.65        | Body                                                    |
| `text-md`     | 17      | 1.55        | Card title, sub-heads                                   |
| `text-lg`     | 20      | 1.4         | Section heads                                           |
| `text-xl`     | 24      | 1.3         | Pricing tier titles                                     |
| `text-2xl`    | 32      | 1.2         | Page h1 (interior pages)                                |
| `text-3xl`    | 44      | 1.1         | Marketing h1                                            |
| `text-4xl`    | 56      | 1.05        | Marketing hero only                                     |

**Tracking.** Display sizes (24+) tracking `-0.02em`. Body `-0.005em`. Microlabels `+0.06em`. Mono `0`.

**Pairings.**
- Marketing h1: Fraunces 56 italic 400 + Inter 17 400 lede.
- Interior h1: Fraunces 32 roman 500 + Inter 15 400.
- Card title: Inter 17 600 (Fraunces reserved for editorial moments only; do not use as card title default).
- Data / numerals: JetBrains Mono 14, tabular figures on (`font-variant-numeric: tabular-nums`).

**Italics policy.** Fraunces italic carries editorial weight. Use it for hero h1, blockquotes from policy docs, scholarship-name headers on detail page. Never use italic for inline emphasis (use weight 600 instead).

### 2.3 Spacing, Radius, Shadow, Border

**Spacing scale.** 4 / 8 / 12 / 16 / 20 / 24 / 32 / 48 / 64 / 96. Page gutters: 20 mobile, 24 tablet, 32 desktop. Card padding: 20. Panel padding: 24–32. Section vertical rhythm: 48 mobile, 64 tablet, 96 desktop.

**Radius.**
- Input / chip / pill: 10
- Button: 12
- Card: 18
- Panel: 22
- Hero card / Marketing surface: 28
- Modal: 22

Never mix radii on adjacent surfaces. A button inside a card is 12 inside 18 — that is the only nesting rule.

**Shadow.**
- `--shadow-hairline`: `inset 0 0 0 1px var(--border-hair)`. Default on all surfaces.
- `--shadow-lift`: `0 1px 2px rgba(14,26,31,0.04), 0 8px 24px -12px rgba(14,26,31,0.10)`. On hover for cards.
- `--shadow-raised`: `0 12px 32px -16px rgba(14,26,31,0.18)`. On popovers, modal, command-K palette.

**No glow.** No coloured shadow. No `box-shadow: 0 0 40px var(--accent)`. Shadow only adds vertical depth in neutral.

**Border.**
- Default border on cards / inputs: 1px solid `--border-hair`.
- Divider within a card: 1px solid `--border-quiet`.
- Validated stripe: 3px solid `--validated` on left edge only.
- Generated stripe: 3px solid `--generated` on left edge only.
- Focus: 2px solid `--focus-ring`, offset 2px, never coloured by component.

### 2.4 Motion Principles

Motion exists to clarify state, not to entertain. Three durations, two easings, one principle.

**Durations.**
- `--motion-micro` 90ms — hover color/opacity only.
- `--motion-enter` 180ms — element enters viewport, modal opens, popover appears.
- `--motion-exit` 140ms — element leaves, modal closes.
- `--motion-layout` 220ms — list reorder, Kanban move, accordion expand.

**Easings.**
- `--ease-out`: `cubic-bezier(0.22, 1, 0.36, 1)`. Default for enter, layout.
- `--ease-in`: `cubic-bezier(0.32, 0, 0.67, 0)`. Default for exit.

**Principle.** Animate `transform` and `opacity`. Never animate `width`, `height`, `top`, `left`, `margin`. Layout shifts during animation are banned.

**Reduced motion.** `@media (prefers-reduced-motion: reduce)` collapses every duration > 120ms to opacity-only crossfade at 100ms. Layout reordering becomes instant. No exceptions.

### 2.5 Iconography & Imagery

**Icons.** Lucide-react only, stroke 1.5, sizes 16 / 20 / 24. Never filled glyphs. Never icon fonts. Never emoji as a UI element. Brand logos (NUST, LUMS, HEC, university crests) are SVG, color-tokenized to `--ink-muted` at rest and `--ink-deep` on hover.

**Imagery.** Editorial photography only. Specifically: Pakistani campus exteriors, students at desks with books, hands writing in margins, university interiors (libraries, lecture halls), passport/visa documents (sanitized — no real names). Forbidden: 3D-rendered hero, gradient blob, mesh background, sparkle particle layer, AI-generated illustration, stock-image people pointing at laptops.

**Image treatment.** All images grayscale-then-warmth-tinted (CSS filter `grayscale(0.15) sepia(0.05)`) to match paper warmth. Never full-color saturated photography.

**Charts.** Recharts. Default palette: `--lapis`, `--gold-leaf`, `--validated`, `--sindoor`, `--ink-muted`. Never rainbow. Always include accessible tabular fallback.

### 2.6 Density & Responsive Breakpoints

**Breakpoints.**
- `xs` 0–374 (small phones — keep functional but not pixel-perfect).
- `sm` 375–767 (default mobile).
- `md` 768–1023 (tablet portrait, sidebar drawer).
- `lg` 1024–1279 (laptop, sidebar always visible).
- `xl` 1280–1535 (desktop).
- `2xl` 1536+ (max content width 1440, no wider).

**Container widths.** Marketing: max 1200 with 64 side padding at xl+. Interior app: max 1280 with 32 side padding at xl+. Reading-heavy surfaces (legal viewer, SOP preview): max 720.

**Density.** Default density is comfortable (44px row min). A user-toggleable compact mode (36px row) lives in `/settings` and applies to tracker tables and admin tables only — never to student core flows.

### 2.7 Accessibility Floor (WCAG 2.2 AA, PDPB)

Non-negotiable.
- All interactive elements have a min hit area of 44×44.
- All text contrasts ≥ 4.5:1 (3:1 for text ≥ 24px).
- Focus is always visible and 2px wide.
- Tab order matches DOM order matches visual order.
- All form inputs have a `<label for>` (never placeholder-as-label).
- Icon-only buttons carry `aria-label`.
- Async status changes announce via `role="status"` live regions.
- All images have `alt`; decorative images use `alt=""`.
- Color is never the only signal — every color change pairs with text or icon.
- PDPB: explicit consent before collecting marketing, behavioral analytics, or B2B sharing.

---

## §3 Information Architecture

### 3.1 Route map (preserved)

```
Public
  /                                  Landing
  /booth/air-university              Booth-specific landing
  /upgrade                           Pricing
  /legal/[slug]                      Terms / Privacy / DPA / Cookie / Refund

Auth
  /signup                            Registration (invite-code variant via ?invite=)
  /login                             Sign-in

Onboarding
  /onboarding                        5-step Pakistan profile

Student core
  /feed                              Dashboard home
  /discover                          Browse all scholarships
  /scholarships/[id]                 Scholarship detail
  /saved                             Saved opportunities
  /dashboard/scholarships/match      Match results (eligible/partial/stretch)
  /tracker                           Kanban application tracker
  /documents                         Documents list (SOPs, emails, reports)
  /documents/[id]                    Document detail
  /documents/sop                     SOP builder
  /documents/professor-email         Professor inquiry email
  /interviews                        Interviews list
  /interviews/[id]                   Generic adaptive interview
  /interviews/visa                   Visa interview simulator
  /profile                           Profile editor (6 cards)
  /settings                          Account, privacy, density, notifications

Admin
  /admin                             KPI overview
  /admin/ingestion                   Source list
  /admin/ingestion/[id]              Run detail
  /admin/curation                    Record list
  /admin/curation/[id]               Record edit
  /admin/users                       Role + plan management
  /admin/audit                       Audit trail
  /admin/rec-eval                    Recommendation benchmarks

Mentor
  /mentor/queue                      Pending feedback queue
  /mentor/documents/[id]             Mentor review form

Partners
  /partners                          Institution overview
  /partners/universities             University list

System
  404, 500, /offline, /denied, /maintenance
```

### 3.2 Nav topology

**Public pages.** `LandingNav` — horizontal: logo left, links (How it works / Scholarships / Pricing / Sign in) center-right, primary CTA (Get started) far right. Sticky after 80px scroll, then becomes 56-tall with hairline bottom border.

**App shell (student / mentor / admin / partner).** `AppShell` = persistent left `Sidebar` (240 wide on lg+, drawer on md and below) + `TopBar` (60 tall, page title left, search center on lg+, avatar menu right).

**Student sidebar (top → bottom).** Dashboard, Matches, Tracker, Documents, Interviews, Discover, Saved, Profile, Settings. Footer cluster: TrialBanner (if applicable), DemoBanner (if demo session), Upgrade button.

**Mobile (sm).** Sidebar becomes drawer behind hamburger. Bottom tab bar replaces sidebar for primary nav: Dashboard / Matches / Tracker / Documents / More. Bottom bar is 64 tall, icons 24, labels 11.

### 3.3 Role-based surfaces

| Role        | Sidebar                                                       | TopBar specifics              |
|-------------|---------------------------------------------------------------|-------------------------------|
| student     | Dashboard, Matches, Tracker, Documents, Interviews, Discover, Saved, Profile, Settings | Plan chip (Explorer/Pro/Elite/Demo) |
| mentor      | Queue, Profile, Settings                                       | Queue count badge             |
| admin       | Overview, Users, Ingestion, Curation, Audit, Rec-Eval, Settings | KPI status dot                |
| partner     | Partners, Universities, Settings                              | Institution name              |

Cross-role nav is forbidden. A student never sees admin links, even if cookied as multi-role. Role mismatch returns to `/feed` with a toast.

---

## §4 Shared Component Inventory

### 4.1 Atomic

- **Button** — variants `primary` (ink-deep bg, paper-white text), `secondary` (paper-white bg, ink-deep text, 1px border), `ghost` (transparent, ink-muted text, hover paper-warm bg), `danger` (sindoor bg). Sizes `sm 36` / `md 44` / `lg 52`. Loading state replaces label with 18px spinner; button disabled. Min hit 44×44.
- **IconButton** — square, 44×44, transparent → paper-warm hover. Carries `aria-label`.
- **Input** — h44, 1px border, 12px radius, 15px text, placeholder `--ink-subtle`. Focus: ring 2px `--focus-ring`, no border color change.
- **Textarea** — same as Input, auto-grows 4–16 rows, monospace optional for code/data.
- **Select** — Radix Select; chevron 16, options list radius 18, max 320 wide, hairline shadow.
- **Checkbox / Radio** — 20×20, 6px radius, validated check.
- **Switch** — 36×20 track, 16 thumb. Off=paper-edge, on=lapis.
- **Chip** — h28, 10 radius, 12px text, sm 12 / 12 padding. Variants `neutral`, `validated`, `generated`, `caution`, `gold`, `sindoor`.
- **Badge** — h20, 999 radius, 11px text uppercase tracking 0.06em.
- **Avatar** — circle, sizes 24 / 32 / 40 / 56. Initials when no image. Background `--paper-warm`, text `--ink-deep`.
- **Tag** — like chip but rectangular; for taxonomy.
- **Spinner** — 18px line-circle, lapis stroke 2, never coloured by container.
- **Skeleton** — paper-edge fill, no shimmer animation (banned theatre); subtle 1.2s opacity pulse 0.6→1 only.

### 4.2 Molecular

- **Card / CardHeader / CardTitle / CardBody / CardFooter** — 18 radius, 1px border, 20 pad. Hover: lift shadow + border-hair → ink-muted (only on clickable cards).
- **Dialog / Modal** — 22 radius, max-w 560 default, 720 wide variant. Scrim 48% ink-deep. Close button top-right 44×44. Esc closes. Focus trap.
- **Tabs** — underline variant default, 2px lapis indicator, 16 padding y, 220ms layout transition on indicator.
- **Accordion** — 1px divider between rows, chevron right, expand collapse 220ms.
- **Tooltip** — 8 radius, paper-white bg, hairline border, 12px text, 8 pad. Delay 400ms.
- **Popover** — like tooltip but interactive, raised shadow, 16 pad, max-w 320.
- **Toast (Sonner)** — bottom-right desktop, top mobile. Stack max 3. Auto-dismiss 5s, hover pauses. Variants `info`, `validated`, `caution`, `sindoor`. Each has icon + title + optional action button.
- **Toolbar** — horizontal cluster, 1px border, 12 radius, 8 pad, used in editors (SOP).
- **Pagination** — prev / pages / next, 36×36 squares, 1px border. Current page bg `--ink-deep`, text paper-white.
- **EmptyState** — icon 32, title 17/600, description 14/400 ink-muted, primary CTA. Never use illustration.
- **ErrorState** — sindoor icon 32, title 17/600 ink-deep, description 14/400 ink-muted, primary retry CTA. Inline within card or full-screen.
- **SkeletonRow / SkeletonCard / SkeletonText** — for list, card grid, paragraph respectively.

### 4.3 Organism

- **AppShell** — sidebar + topbar + main. Main scrolls; sidebar and topbar do not.
- **Sidebar** — collapsible to 64 wide (icons only) on lg between 1024–1199.
- **TopBar** — sticky, paper-white, hairline bottom border. Page title left, search center, avatar menu right.
- **MobileBottomTabBar** — fixed bottom, 64 tall, paper-white, hairline top border, 5 slots, current tab has 2px ink-deep top indicator.
- **LandingNav** — public-page header.
- **MatchCard** — scholarship match tile: provider logo 32 + title 17/600 + bucket chip + deadline mono + funding mono + footer (CTA + save).
- **CompactScholarshipCard** — dashboard recent-matches mini variant (h96, title 15/600, deadline only).
- **ScholarshipDetailHeader** — provider logo 56, scholarship name in Fraunces 32 italic, validated stripe, deadline + funding chips, primary CTA.
- **CompatibilityMeter** — 5-segment horizontal bar, segments fill lapis from left, 1px gap between segments, percent label right.
- **EligibilityMatrix** — table of requirement vs. user-state with check/cross/dash. ARIA labelled.
- **TrackerCard** — kanban tile: 20 pad, 18 radius, scholarship title + deadline chip + checklist progress + grab handle (4-dot lucide GripVertical).
- **TrackerBoard** — 6 columns, horizontal scroll on tablet down, native HTML5 DnD.
- **ChecklistPanel** — collapsible 14-item list with checkbox + label + optional info icon (hover tooltip).
- **AddApplicationDialog** — modal with scholarship picker (autocomplete from match results) + stage select + deadline date.
- **PricingCard** — tier name (Fraunces 24 italic on Pro+, roman on Explorer), price mono 32 + period, feature list 8 max, CTA.
- **CurrencySwitcher** — select with 5 ISO codes; persists to localStorage `aidwise.currency`.
- **WaitlistForm** — accordion within pricing card: email + selected plan → POST.
- **PaymentMethods** — block listing JazzCash, Easypaisa, IBAN, mailto. Each method = label + value + copy-to-clipboard button.
- **UpgradeWall** — overlay or inline; consumes 402 `detail.message` verbatim. Two variants: `full` (blocks the surface) and `inline` (replaces an item slot with locked placeholder).
- **CookieBanner** — bottom sheet on first visit, 3 buttons (Accept all / Reject non-essential / Customize). Persists choice.
- **ConsentBar** — sticky bottom on `/legal/[slug]` when version mismatch; "I agree, version 1.0" button.
- **TrialBanner** — sidebar footer card, gold-soft bg, gold-leaf text, mono countdown.
- **TrialExpiredBanner** — full-width sticky banner inside AppShell main, gold-leaf bg, ink-deep text, primary "See pricing" CTA.
- **DemoBanner** — sidebar footer when `session.demo === true`, ink-deep bg, paper-white text, mono "DEMO" tag.
- **ComingSoon** — pill badge: amber=Q2, sky=Q3, violet=Q4, stone=TBD (use validated/lapis/caution/ink-muted soft tints in this palette).
- **QuestionCard** — visa interview Q&A: question text 17, mic + text input toggle, submit + skip footer.
- **FeedbackPanel** — rubric scores (5 categories), each row = label + 5-segment bar + numeric score 0–10 mono.
- **SummaryRadar** — Recharts radar with 5 axes, single series, ink color, no fill (1px outline only).
- **SessionSummary** — interview close-out: transcript preview + download CTA + share CTA (Elite only).
- **SetupScreen** — country tile grid (4 across desktop, 2 mobile), tile = flag-free, country name 17, university count mono 13, hover paper-warm.
- **RoleGuard** — server-side gate; on mismatch redirects to `/feed` (student) or `/denied`.

### 4.4 Behavior contracts (cross-component rules)

- Lists never spinner-per-item. One skeleton on first load, optimistic updates after.
- Mutations are optimistic where reversible (toggle save, change tracker stage, check checklist item). On error, rollback + toast.
- Modals never stack >1 deep. Confirmation inside a modal uses inline state, not a second modal.
- Toasts never replace inline error. Inline error is primary; toast is supplemental.
- 402 plan-required is the only error that renders as a feature-blocking overlay. All other errors render inline.

---

## §5 User Flows

### 5.1 Booth walk-by → first match (≤3 minutes)

Goal: a student scans the QR at the Air University booth and lands on `/signup?invite=AIRU2026`, gets to one validated match in ≤3 minutes.

```
QR scan → /booth/air-university (10s glance)
  → "Get my matches" CTA
  → /signup?invite=AIRU2026 (60s)
    pre-filled invite code chip, PDPB consent checkbox required
  → /onboarding (90s, 5 steps, defaults filled aggressively)
  → /dashboard/scholarships/match (1s)
    skeleton 600ms → 1 eligible + 1 partial + 1 stretch
```

**Friction audit.**
- Step 1: invite chip visible above email field — no extra typing.
- Step 2: GPA scale auto-detects (4.0 / 5.0 / first-class / percentage) from a single number.
- Step 3: target country defaults to the most-requested in the cohort (UK).
- Step 4: degree subject is a free-text with autocomplete from a 200-term list, not a select with 2,000 options.
- Step 5: financial context is one slider (0–PKR 5M/year budget), not a form.
- Result page renders eligible match first, partial second. No tabs on first paint — they appear after first scroll.

### 5.2 Returning student → tracker → SOP draft

Goal: a user with an existing match adds a scholarship to tracker and drafts an SOP in one session.

```
/feed → recent matches block → click match card
  → /scholarships/[id] (detail)
  → "Add to tracker" → AddApplicationDialog
    auto-fills scholarship, prompts stage (default Wishlist), deadline pre-filled
  → /tracker (tile appears in Wishlist column, optimistic)
  → click tile → drawer opens with checklist
  → "Draft SOP" link in checklist → /documents/sop?scholarship=[id]
  → SOP builder pre-fills program + provider + deadline
  → draft generates in 3–8s (progress: "Drafting paragraph N of 5")
  → preview opens right panel
  → save → /documents (toast: "SOP saved as draft")
```

**Friction audit.** No copy-paste between screens. Deep links carry scholarship context. Drawer-based checklist means no full-page navigation interruption.

### 5.3 Freemium gate → upgrade decision

Goal: a free user hits a 402 plan-required at match #4 and either upgrades or chooses to wait.

```
/dashboard/scholarships/match (showing 3 unlocked + N locked placeholders)
  → click locked item → UpgradeWall (inline) renders 402 `detail.message`
    "See all 47 matches with Pro (PKR 2,999/mo)"
  → "See pricing" → /upgrade
    4 tiers, comparison table, currency switcher
  → "Start Pro trial" (no payment yet)
    → POST /waitlist with plan=pro → confirmation toast
    → return path: /dashboard/scholarships/match
```

**Friction audit.** UpgradeWall copy is backend-driven and specific. No interstitial. Pricing currency persists. Waitlist is a single email — no payment in v1.

### 5.4 Privacy + consent

Goal: a user reviews policy, grants consent, opts in/out of marketing.

```
First visit → CookieBanner bottom sheet
  → "Customize" → CookiePreferences modal (4 toggles: essential always on)
  → save → banner dismisses

/signup → PDPB consent checkbox (v1.0 doc hash logged)
/legal/privacy → ConsentBar appears if version mismatch
  → "I agree, version 1.0" → POST /privacy/consent → bar dismisses

/settings → Privacy panel
  → Marketing emails toggle
  → B2B share consent toggle (Pro+)
  → "Export my data" → POST /privacy/data-export → status card
  → "Delete account" → typed-confirm dialog → POST /privacy/account-deletion
```

### 5.5 Trial countdown → expiry → recovery

```
Signup with AIRU2026 → plan=pro + plan_expires_at=now+30d
  → TrialBanner in sidebar footer: "Pro trial — 30 days left"
  → daily countdown, color-shift at <7 days (gold-leaf bg)
  → at day 0: trial expires (Celery beat flips to free)
  → on next login: TrialExpiredBanner sticky in AppShell
    "Your Pro trial ended. See pricing to keep Pro features."
  → "See pricing" → /upgrade
  → "Keep using free" → banner dismisses for 7 days, returns
```

### 5.6 Visa interview practice → summary → share

```
/interviews/visa → SetupScreen (country tile grid)
  → pick UK → POST /interviews/visa/start (session created)
  → QuestionCard renders Q1; user answers (text or mic)
  → submit → POST /interviews/visa/{id}/answer
  → FeedbackPanel slides in right (study mode) OR
    next question loads immediately (exam mode)
  → after Q3 free / Q15 elite: SessionSummary
    SummaryRadar + transcript download + share (Elite)
  → "Practice again" returns to SetupScreen with last country pre-selected
```

---

## §6 Screen Specifications

### 6.1 `/` — Landing

**Purpose.** Convert a Pakistani student visiting AidwiseAI for the first time into a signup within 90 seconds.

**Users + Entry.** First-time visitor (organic, referral, paid). Entry: external link, search, friend referral. Next: `/signup` (primary) or `/booth/air-university` if QR-routed.

**Backend contract.** No auth. `GET /api/v1/scholarships?tier=standard&limit=6` for featured scholarships block. Public.

**Anatomy.**
```
+-------------------------------------------------------+
| LandingNav (sticky after 80px)                        |
+-------------------------------------------------------+
| Hero: Fraunces h1 italic 56 / Inter lede 17 / 2 CTAs  |
|       3 stat chips below CTAs (mono)                  |
+-------------------------------------------------------+
| Problem section: 3-card grid (Visa / Funding / SOP)   |
+-------------------------------------------------------+
| How it works: 4 numbered steps, horizontal            |
+-------------------------------------------------------+
| Featured scholarships: 6 CompactScholarshipCards      |
+-------------------------------------------------------+
| Visa interview callout: split, image left, copy right |
+-------------------------------------------------------+
| Pricing teaser: 3 PricingCards (Explorer/Pro/Elite)   |
+-------------------------------------------------------+
| Footer: 4 columns + legal links + brand mark          |
+-------------------------------------------------------+
```

**States.**
- Empty: never (page is static + 6 scholarships always available; if API fails, show fallback editorial copy).
- Loading: SSR — no client-side loading. Featured scholarships block uses skeleton on hydration if revalidated.
- Loaded: golden path.
- Processing: not applicable.
- Error: if `/scholarships` 5xx, featured block renders 6 editorial placeholders with provider names (Chevening / Fulbright / DAAD / Commonwealth / HEC Overseas / Erasmus Mundus) and "Browse all" CTA to `/discover` (post-signup).
- Success: not applicable.
- Locked: not applicable.

**Interactions.** Nav links smooth-scroll to in-page anchors on `/`. Primary CTA "Get started" → `/signup`. Secondary "See scholarships" → `/discover` (gated; redirects to signup with `?next=/discover`).

**Motion.** Hero h1 fades in 220ms on load (no slide). Stat chips count up from 0 once (180ms ease-out, single play). Featured cards fade in stagger 60ms apart on viewport intersection. No parallax.

**Anti-slop check.**
- Banned: hero gradient blob bg; "Revolutionary scholarship platform"; sparkle icon next to "AI-powered"; auto-scroll carousel of testimonials.
- Allowed: "Find your funded master's in 7 minutes."; "47 universities. 20 active scholarships. 70 visa questions."; named provider logos with source links.

**Copy strings.**
- H1: "Funded master's degrees, found for you."
- Lede: "AidwiseAI matches Pakistani students with fully-funded scholarships in the UK, US, Canada, Germany, and Australia."
- Primary CTA: "Get started — free"
- Secondary CTA: "See how it works"
- Stat chips: "47 universities", "20 scholarships live", "70 visa questions"
- Problem h2: "Three things between you and a funded place."
- How-it-works h2: "How AidwiseAI works."
- Featured h2: "Live scholarships."
- Pricing teaser h2: "Start free. Upgrade when you're ready."
- Footer brand line: "AidwiseAI — built for Pakistani applicants."

**Accessibility.** Hero h1 is the single `<h1>`. Section headings `<h2>`. Stat chips are decorative — same data appears as text inside the problem section. CTAs have descriptive labels (not "click here"). Featured card list uses `<ul role="list">` with `<li>` per scholarship.

**Responsive.**
- 375: hero h1 32, single column, stat chips wrap to 3 rows.
- 768: hero h1 44, two-column problem section.
- 1024: hero h1 56, full grid layout.
- 1440: container caps at 1200.

**Telemetry.** `landing.view`, `landing.cta_primary_click`, `landing.cta_secondary_click`, `landing.featured_card_click {scholarship_id}`, `landing.scroll_depth {25|50|75|100}`.

---

### 6.2 `/booth/air-university` — Booth Landing

**Purpose.** Convert a QR-scanning student standing at the AidwiseAI booth into a signup with invite code pre-applied, in under 90 seconds.

**Users + Entry.** Student physically present at Air University. Entry: QR scan of `https://aidwiseai.com/signup?invite=AIRU2026` (or direct link). Often distracted, on mobile, in a hurry.

**Backend contract.** No auth. `GET /api/v1/upgrade/pricing?currency=PKR` for trial value statement.

**Anatomy.**
```
+----------------------------------------------+
| Brand mark + "Air University" co-mark        |
+----------------------------------------------+
| H1: "30 days of Pro, free for Air U."        |
| Sub: invite chip "AIRU2026" + counter        |
+----------------------------------------------+
| 3 value bullets (mono numerals)              |
+----------------------------------------------+
| Single CTA: "Start now — 60 seconds"         |
+----------------------------------------------+
| Trust footer: PDPB, deadline of trial window |
+----------------------------------------------+
```

**States.**
- Empty: not applicable.
- Loading: SSR.
- Loaded: golden path.
- Processing: not applicable.
- Error: if `/upgrade/pricing` fails, render static value bullets (no live counter).
- Success: not applicable on this page (success state is on the next page).
- Locked: trial-window-expired — if current time > AIRU2026 `valid_until` (May 26 23:59 PKT), page replaces value statement with "Air University trial window has ended. You can still sign up for Explorer (free forever)." CTA changes to "Sign up free".

**Interactions.** Single CTA. No nav. Tappable invite chip copies code to clipboard (toast: "AIRU2026 copied"). Back button warns "You'll lose the invite link — sure?" only on mobile browsers.

**Motion.** None on entry. Counter chip updates once per second client-side once below 24 hours remaining; otherwise static.

**Anti-slop check.**
- Banned: animated "Limited time!" badge; countdown timer with milliseconds; balloon emoji; gradient on h1.
- Allowed: "Trial closes May 26, 23:59 PKT — 3 days left."; single-color invite chip; named partner co-mark.

**Copy strings.**
- H1: "30 days of Pro, free for Air U."
- Sub: "Use code AIRU2026 at signup. Closes May 26."
- Bullets: "Match against 20 fully-funded scholarships.", "Build a Pakistan-context SOP in 5 minutes.", "Practice 70 visa questions for UK / US / CA / DE."
- CTA: "Start now — 60 seconds"
- Trust footer: "We follow PDPB. We never share your data without consent."

**Accessibility.** Invite chip has `aria-label="Invite code AIRU2026, tap to copy"`. CTA destination announced in `aria-describedby`. Counter has `aria-live="polite"` only when <60 minutes remaining.

**Responsive.**
- 375: full-bleed single column, CTA full-width sticky bottom.
- 768+: max-w 560 centered, CTA inline.

**Telemetry.** `booth.view {invite_code}`, `booth.cta_click`, `booth.invite_copied`, `booth.expired_view`.

---

### 6.3 `/upgrade` — Pricing

**Purpose.** Help a free or trial user choose between Explorer, Pro, Elite, or Institution and either start a waitlist or contact sales.

**Users + Entry.** Free user, trial user, or curious visitor. Entry: sidebar Upgrade button, UpgradeWall CTA, landing pricing-teaser CTA, trial-expired banner. Next: waitlist form submission or `/feed`.

**Backend contract.** `GET /api/v1/upgrade/pricing?currency={PKR|GBP|EUR|AED|USD}`. `POST /api/v1/waitlist` with `{plan, email}`. Institution → mailto.

**Anatomy.**
```
+--------------------------------------------------------+
| Page header: H1 "Pricing" + CurrencySwitcher right     |
+--------------------------------------------------------+
| 4 PricingCards (Explorer / Pro / Elite / Institution)  |
|   each: tier name / price / period / 6-8 features / CTA|
+--------------------------------------------------------+
| Comparison table (collapsible on mobile)               |
|   rows: feature, columns: tiers, cells: check / value  |
+--------------------------------------------------------+
| FAQ accordion (6 items)                                |
+--------------------------------------------------------+
| Footer: "Questions? partnerships@aidwiseai.pk"         |
+--------------------------------------------------------+
```

**States.**
- Empty: not applicable.
- Loading: skeleton — 4 card placeholders 280×420.
- Loaded: golden path.
- Processing: waitlist form submission spinner on button only.
- Error: pricing fetch fails → render server-cached fallback (PKR fixed, switcher disabled, toast "Live currency rates unavailable").
- Success: waitlist submitted — card flips to confirmation: "You're on the Pro waitlist. We'll email {email} when payment opens."
- Locked: Institution card always available but CTA is mailto, never POST.

**Interactions.** CurrencySwitcher persists to `localStorage.aidwise.currency` and re-fetches pricing. Tier CTA opens WaitlistForm accordion within the card (not a modal). Comparison table is sticky-header on scroll. FAQ accordion: single-open.

**Motion.** Card price re-renders crossfade 140ms on currency switch (no layout shift — width reserved with `min-w`). Accordion: 220ms ease-out height expand. Tier card hover: lift shadow only, no scale.

**Anti-slop check.**
- Banned: "Most popular" badge with gradient ribbon; "Save 20%!" callout with strikethrough red; faux-3D card; "Best value" auto-highlight without explanation.
- Allowed: "Recommended for serious applicants" (chip, neutral); strikethrough on annual price beside monthly; named features ("5 SOP drafts per month" not "Unlimited everything").

**Copy strings.**
- H1: "Pricing"
- Sub: "Pakistan-priced. Pay in PKR or your local currency."
- Explorer tier: "Free — forever", CTA "Get started"
- Pro tier: "PKR 2,999/month", CTA "Join Pro waitlist"
- Elite tier: "PKR 6,000/month", CTA "Join Elite waitlist"
- Institution tier: "Contact for pricing", CTA "Email partnerships"
- Currency switcher label: "Show prices in"
- Comparison table H2: "What you get at each tier"
- Mailto: `partnerships@aidwiseai.pk?subject=Institution+plan+enquiry`

**Accessibility.** Each PricingCard is a region with `aria-labelledby={tierTitleId}`. Comparison table has `<caption>`. Currency switcher is a `<select>` with `<label>`. Waitlist confirmation announces via `role="status"`.

**Responsive.**
- 375: cards stack vertically, comparison table collapses to per-tier accordion.
- 768: 2×2 card grid.
- 1024+: 4 cards in a row.

**Telemetry.** `upgrade.view`, `upgrade.currency_switch {from, to}`, `upgrade.cta_click {tier}`, `upgrade.waitlist_submit {tier}`, `upgrade.institution_email_click`, `upgrade.faq_open {id}`.

---

### 6.4 `/legal/[slug]` — Legal Viewer

**Purpose.** Display a legal document (Terms, Privacy, DPA, Cookie Policy, Refund) and capture explicit consent on version mismatch.

**Users + Entry.** Any user, often during signup or settings flow. Entry: footer links, signup form link, settings privacy panel, ConsentBar "Read full doc".

**Backend contract.** `GET /api/v1/privacy/legal/{slug}` → `{slug, version, title, body_md, effective_at, body_sha256}`. `POST /api/v1/privacy/consent` with `{slug, version, body_sha256}`.

**Anatomy.**
```
+----------------------------------+
| TopBar (if auth) or LandingNav   |
+----------------------------------+
| Doc header: title (Fraunces 32)  |
|   version chip + effective date  |
+----------------------------------+
| Body: rendered markdown, max-w   |
|   720, body 17/1.7, h2 24/1.3    |
+----------------------------------+
| ConsentBar (sticky bottom,       |
|   only if user must consent)     |
+----------------------------------+
```

**States.**
- Empty: not applicable (every legal slug must return a document).
- Loading: skeleton — title bar + 12 paragraph placeholders.
- Loaded: rendered markdown.
- Processing: consent submission — bar disables, label "Recording consent…" for ≤500ms.
- Error: 404 slug → "Document not found." with link to footer index. 5xx → error state inline with retry.
- Success: consent recorded — ConsentBar morphs into validated chip "You agreed to v1.0 on {date}", then dismisses after 3s.
- Locked: not applicable.
- Stale: version mismatch — ConsentBar appears, footer chip "Version 1.0 → 1.1 — please re-read and agree".

**Interactions.** Table of contents (left sidebar on lg+, accordion top on mobile). Anchor links to h2 sections. ConsentBar button always within reach (sticky). Print stylesheet available.

**Motion.** ConsentBar slides up 220ms on first render. Section anchors smooth-scroll 200ms.

**Anti-slop check.**
- Banned: "TL;DR" auto-summary above legal text; emoji checkmarks beside bullet lists; collapsing main body into "Read more" accordion.
- Allowed: per-section anchor TOC; print button; "Last updated {date}" line below title.

**Copy strings.**
- ConsentBar label: "Version {version} of {title} is in effect. Please review and agree."
- ConsentBar button: "I agree to version {version}"
- Consent recorded chip: "Agreed to {title} v{version} on {YYYY-MM-DD}"
- Not-found: "We couldn't find that document. View all policies in the footer."

**Accessibility.** Skip-to-content link. Section h2 ids match TOC anchors. ConsentBar has `role="region"` and `aria-label="Consent action"`. Markdown lists render as `<ul>`. Long tables get `<caption>`.

**Responsive.**
- 375: TOC collapses, body 16/1.7, ConsentBar full-width fixed.
- 1024+: TOC pinned left sidebar 240, body centered max-w 720.

**Telemetry.** `legal.view {slug, version}`, `legal.consent_submitted {slug, version}`, `legal.anchor_click {anchor_id}`, `legal.print_click`.

---

### 6.5 `/signup` — Registration

**Purpose.** Create an account in under 60 seconds, capturing the minimum required (email, password, PDPB consent) plus invite-code variants (cohort + B2B fields) when present.

**Users + Entry.** First-time user. Entry: landing CTA, booth landing CTA, /upgrade waitlist refer, organic. Next: `/onboarding`.

**Backend contract.** `POST /api/v1/auth/register` with `{email, password, marketing_opt_in, consent_v, invite_code?, air_uni_uni?, air_uni_dept?, air_uni_batch?}`. Returns `{access_token, refresh_token, user}`.

**Anatomy.**
```
+----------------------------------+
| LandingNav (mini, no nav links)  |
+----------------------------------+
| Left column (md+): editorial copy|
|   "Two minutes. Then matches."  |
|                                  |
| Right column: form                |
|   Invite chip (if ?invite=)      |
|   Email                          |
|   Password (12+ char meter)      |
|   Air U: uni + dept + batch      |
|     (only if invite=AIRU2026)    |
|   PDPB consent checkbox required |
|   Marketing opt-in checkbox      |
|   Primary CTA                    |
|   Sign-in link                   |
+----------------------------------+
```

**States.**
- Empty: form pristine, CTA disabled until email + password + PDPB consent valid.
- Loading: not applicable (server-rendered form).
- Loaded: golden path.
- Processing: CTA replaces label with spinner; all inputs disable; form caption "Creating your account…".
- Error: inline per-field (email taken, password too short). Network 5xx → toast "Couldn't reach AidwiseAI. Try again." with retry.
- Success: redirect to `/onboarding` (no celebration screen — onboarding starts immediately).
- Locked: invite-code expired → invite chip becomes sindoor "Code AIRU2026 expired May 26. You can still sign up for Explorer." Air U fields hide.

**Interactions.** Password meter (12+ char hard minimum, +12pt for 16+, +12pt for mixed case + digit). Show/hide password toggle. Invite chip removable on click. Enter submits.

**Motion.** Password meter bar fills 90ms linear. Error messages slide in 180ms from below their input. No success animation — navigation is the success signal.

**Anti-slop check.**
- Banned: confetti on submit success; password strength rated "Excellent! 🔥"; faux-social signup buttons that don't work; "By signing up, you agree to..." buried in 11px gray.
- Allowed: explicit consent checkbox with link to /legal/privacy; password meter labelled "Weak / OK / Strong"; mono "12 character minimum" helper text.

**Copy strings.**
- H1 (left col): "Two minutes. Then matches."
- Sub: "Set up your AidwiseAI account. We match you against live scholarships immediately after onboarding."
- Email label: "Email"
- Password label: "Password (12 characters minimum)"
- Air U cohort: "University", "Department", "Batch year"
- PDPB checkbox: "I have read and agree to the Privacy Notice (v1.0)."
- Marketing checkbox: "Email me when scholarships matching my profile open (you can unsubscribe anytime)."
- CTA: "Create account"
- Sign-in link: "Already have an account? Sign in"

**Accessibility.** Each field has `<label for>`. Password meter has `aria-live="polite"`. Consent checkbox is required and reads "Required, you must agree to the Privacy Notice." Errors are `<p role="alert">` beneath each input.

**Responsive.**
- 375: single column, editorial copy hides, form full-width.
- 1024+: split 5/7, editorial copy 5 / form 7.

**Telemetry.** `signup.view {invite_code?}`, `signup.field_blur {field}`, `signup.submit_attempt`, `signup.submit_success`, `signup.submit_error {error_code}`, `signup.password_meter_max`.

---

### 6.6 `/login` — Sign in

**Purpose.** Authenticate a returning user in under 15 seconds.

**Users + Entry.** Returning user. Entry: landing nav, signup "already have an account" link, expired-session redirect. Next: `/feed` or `?next=` original destination.

**Backend contract.** `POST /api/v1/auth/login` with `{email, password}`. Returns tokens + user. Refresh on 401 via stored refresh token.

**Anatomy.**
```
+----------------------------------+
| LandingNav (mini)                |
+----------------------------------+
| Centered form 380w               |
|   H1 "Sign in"                   |
|   Email                          |
|   Password                       |
|   Forgot password link           |
|   Primary CTA                    |
|   "Demo: student / admin" chips  |
|     (dev / staging only)         |
|   Signup link                    |
+----------------------------------+
```

**States.**
- Empty: pristine.
- Loading: not applicable.
- Loaded: golden path.
- Processing: CTA spinner.
- Error: 401 → inline "Email or password is incorrect."; 429 → "Too many attempts. Try again in 60 seconds." with countdown.
- Success: redirect to `?next=` or `/feed`.
- Locked: account-locked → "This account is under review. Email support@aidwiseai.pk."

**Interactions.** Demo chips (visible only when `NODE_ENV !== 'production'`): tap to fill student@example.com / admin@example.com with `strongpass1`. Enter submits.

**Motion.** Error inline message slide-in 180ms. No transition on success — navigation handles it.

**Anti-slop check.**
- Banned: social login buttons that don't work; "Welcome back!" hero illustration; biometric prompt mock.
- Allowed: dev-only demo chips; rate-limit countdown in mono; password show/hide.

**Copy strings.**
- H1: "Sign in"
- Email label: "Email"
- Password label: "Password"
- Forgot: "Forgot password?"
- CTA: "Sign in"
- Demo dev chips: "Demo: student", "Demo: admin"
- Signup link: "New here? Create an account"

**Accessibility.** Autocomplete `email` and `current-password`. CapsLock warning announced on password focus.

**Responsive.** Single centered column at all sizes. Form scales 380 → 100% at 375.

**Telemetry.** `login.view`, `login.submit_attempt`, `login.submit_success`, `login.submit_error {error_code}`, `login.demo_chip_click {role}`.

---

### 6.7 `/onboarding` — 5-step Pakistan Profile

**Purpose.** Capture the minimum profile to produce a useful match list, in under 3 minutes.

**Users + Entry.** Brand-new user post-signup. Entry: redirect from `/signup`. Next: `/dashboard/scholarships/match` (auto-generates first match).

**Backend contract.** `PATCH /api/v1/profile/me` after each step (save-as-you-go). On completion `POST /api/v1/scholarships/match` triggers and result page is preloaded.

**Anatomy.**
```
+----------------------------------+
| Progress: 5 segments, current    |
|   filled lapis                   |
+----------------------------------+
| Step header: "Step 2 of 5"       |
|   H1 (Fraunces 32 italic)        |
+----------------------------------+
| Form fields (1–4 per step)       |
+----------------------------------+
| Footer: Back / Skip / Continue   |
+----------------------------------+
```

**5 steps.**
1. **About you** — citizenship country code (PK default), current university (autocomplete from 25 PK unis), degree level (BS/MS/PhD/MBA select).
2. **Academic record** — GPA value + scale auto-detect (4.0 / 5.0 / first-class / percentage), expected graduation date (month picker).
3. **Test scores** — language test (IELTS / TOEFL / PTE / Duolingo) + score (or "haven't taken"), GRE/GMAT/SAT optional.
4. **Your goal** — target country (multi-select from UK/US/CA/DE/AU), target degree (BS/MS/PhD/MBA), target field (autocomplete 200-term), preferred intake (Fall/Spring 2027).
5. **Financial context** — funding requirement (single slider 0–PKR 5M/year), household income band (5 options), willing to relocate Y/N.

**States per step.**
- Empty: pristine, Continue disabled until required fields valid.
- Loading: not applicable (client-side).
- Loaded: golden path.
- Processing: Continue spinner during PATCH; if PATCH fails, retry inline.
- Error: per-field validation inline. Network: toast retry.
- Success: each step transitions forward 220ms layout. Final step submits and routes.
- Locked: not applicable.

**Interactions.** "Skip" available on steps 3 and 5 only. Back never destroys data (saved on every PATCH). Browser back arrow respects step state. Pressing Enter on focused input advances.

**Motion.** Step transition: outgoing step fades 140ms exit → incoming step slides from 16px right + fades 180ms enter. Progress segment fills 220ms ease-out.

**Anti-slop check.**
- Banned: "Almost there! 🚀"; floating mascot character; "AI is analyzing your profile" between steps; auto-skip on speed-fill.
- Allowed: "Step 2 of 5"; specific helper text ("If your GPA is 3.4 / 4.0, type 3.4 and pick 4.0"); save chip "Saved" with checkmark after each PATCH.

**Copy strings.**
- Step 1 H1: "About you."
- Step 2 H1: "Your academic record."
- Step 3 H1: "Your test scores."
- Step 4 H1: "Your goal."
- Step 5 H1: "Your funding context."
- Continue (steps 1–4): "Continue"
- Continue (step 5): "Show my matches"
- Skip: "Skip this step"
- GPA helper: "We support 4.0, 5.0, first-class, and percentage scales."
- Funding slider label: "Up to PKR {value} per year"

**Accessibility.** Each step is a `<form>` with `<fieldset>` and `<legend>`. Progress is a `<nav>` with `aria-label="Onboarding steps"`. Step transitions move focus to the new H1.

**Responsive.**
- 375: full-bleed, footer sticky bottom.
- 768+: max-w 560 centered.

**Telemetry.** `onboarding.step_view {step}`, `onboarding.step_complete {step, duration_ms}`, `onboarding.skip {step}`, `onboarding.complete {duration_total_ms}`, `onboarding.abandon {step}`.

---

### 6.8 `/feed` — Dashboard Home

**Purpose.** Give a returning student a 30-second status read (matches, deadlines, in-flight applications) and a one-click path into the most likely next action.

**Users + Entry.** Authenticated student. Entry: post-login redirect, sidebar logo click, bottom-tab Home. Next: any sidebar destination.

**Backend contract.** `GET /api/v1/auth/me`, `POST /api/v1/recommendations` (top 3), `GET /api/v1/tracker?summary=true`, `GET /api/v1/profile/me` (completeness check).

**Anatomy.**
```
+--------------------------------------------------+
| TopBar                                           |
+--------------------------------------------------+
| Page header: H1 + plan chip + currency badge     |
+--------------------------------------------------+
| If profile <80% complete: ProfileCompleteCard    |
|   1-row banner with completion bar + CTA         |
+--------------------------------------------------+
| Action grid 2×2 (md+) / 1×4 (sm)                 |
|   Find matches / Track applications / Draft SOP  |
|   / Practice visa                                |
+--------------------------------------------------+
| Recent matches: 3 CompactScholarshipCards        |
+--------------------------------------------------+
| Tracker summary: progress bar + 6 stage counts   |
+--------------------------------------------------+
```

**States.**
- Empty (no matches, no tracker): action grid + ProfileCompleteCard prominent. Recent matches block shows EmptyState "Run your first match. Takes 3 seconds." with CTA.
- Loading: skeleton — header + 4 action tiles + 3 card placeholders + tracker summary bar.
- Loaded: golden path.
- Processing: tracker summary refresh inline (no spinner; just numeric crossfade).
- Error: per-block ErrorState (tracker summary error doesn't break recent matches).
- Success: not applicable (read-only screen).
- Locked: not applicable (matches block respects free cap of 3).

**Interactions.** Action tile click → respective route. Recent match click → `/scholarships/[id]`. Tracker summary stage click → `/tracker?stage={stage}`.

**Motion.** Numeric counters in tracker summary tween from prev → next over 220ms ease-out. Cards fade-in 180ms on hydration.

**Anti-slop check.**
- Banned: "Good morning, Aisha! 👋"; rotating motivational quote; AI suggestion banner "Try this!"; trophy / streak counter.
- Allowed: "Welcome back, Aisha."; named action tiles; specific tracker counts ("2 in Applied, 1 in Shortlisted").

**Copy strings.**
- H1: "Welcome back, {first_name}."
- Plan chip: "Explorer" / "Pro trial — 4 days" / "Pro" / "Elite" / "Demo"
- ProfileCompleteCard: "Your profile is {pct}% complete. Finish for better matches."
- Action tiles: "Find matches", "Track applications", "Draft SOP", "Practice visa"
- Recent matches H2: "Recent matches"
- See-all: "See all matches"
- Tracker summary H2: "Your applications"

**Accessibility.** Action tiles are `<a>` not `<button>`. Profile completion uses `<progress>` element with `max=100`. Numeric counter changes announce via `role="status"`.

**Responsive.**
- 375: action grid 1 column, recent matches stack.
- 768: 2×2 grid.
- 1024+: 2×2 grid + side-by-side recent matches and tracker summary.

**Telemetry.** `feed.view`, `feed.action_tile_click {action}`, `feed.recent_match_click {scholarship_id}`, `feed.tracker_summary_click {stage}`, `feed.profile_complete_card_click`.

---

### 6.9 `/discover` — Browse all scholarships

**Purpose.** Let a student browse the full live scholarship catalog with filters, independent of match buckets.

**Users + Entry.** Student exploring the catalog. Entry: sidebar Discover, landing "See scholarships". Next: `/scholarships/[id]`.

**Backend contract.** `GET /api/v1/scholarships?country=&field=&funding=&deadline_before=&page=&page_size=`. Returns paginated list; premium tier rows are gated by tier for free/pro users.

**Anatomy.**
```
+--------------------------------------------------+
| Page header: H1 "Discover" + count "47 results"  |
+--------------------------------------------------+
| Sticky filter bar: country / field / funding /   |
|   deadline / search                              |
+--------------------------------------------------+
| List: 12 cards per page, paginated               |
|   each row: provider logo + title + meta chips + |
|   funding mono + deadline mono + Save icon       |
+--------------------------------------------------+
| Pagination: prev / 1 2 3 ... 4 / next            |
+--------------------------------------------------+
```

**States.**
- Empty (after filter): "No scholarships match these filters." with "Clear filters" CTA.
- Loading: 12 skeleton rows.
- Loaded: golden path.
- Processing: filter change → 200ms skeleton overlay on list area only.
- Error: ErrorState card in place of list with retry.
- Success: filter applied — header count updates inline.
- Locked: premium rows render with gold-leaf chip "Pro" and click → UpgradeWall inline modal.

**Interactions.** Filter inputs debounce 300ms. URL syncs filter state (shareable). Save toggles optimistically; rollback on error. Click row anywhere → detail.

**Motion.** Filter change: list opacity 0.4 for 200ms then crossfade to new results. Save icon ink-deep → validated 90ms.

**Anti-slop check.**
- Banned: "Smart filter" suggestions auto-checking themselves; "Hot scholarships" badge with flame icon; trending arrow on titles.
- Allowed: "47 results"; "Closing soon (next 14 days)" filter chip; mono deadline "31 Oct 2027".

**Copy strings.**
- H1: "Discover"
- Filter labels: "Country", "Field", "Funding", "Deadline", "Search"
- Save tooltip: "Save to your list"
- Unsave tooltip: "Remove from your list"
- Empty: "No scholarships match these filters."
- Locked chip: "Pro"
- UpgradeWall: backend `detail.message`

**Accessibility.** Filter bar is a `<form>` with submit on change. Results list is `<ul role="list">`. Each card is a `<li>` containing an `<a>`. Pagination uses `<nav aria-label="Pagination">`.

**Responsive.**
- 375: filter bar collapses to "Filters" drawer button + sort chip; cards stack.
- 1024+: filter bar inline at top, cards in single column with side meta.

**Telemetry.** `discover.view`, `discover.filter_change {filter, value}`, `discover.result_click {scholarship_id}`, `discover.save_toggle {scholarship_id, saved}`, `discover.pagination {page}`.

---

### 6.10 `/scholarships/[id]` — Scholarship Detail

**Purpose.** Give a student everything needed to decide whether to apply: eligibility, deadlines, funding, requirements, provenance.

**Users + Entry.** Student researching a specific scholarship. Entry: `/discover` row click, `/feed` recent matches, `/dashboard/scholarships/match` card, deep link. Next: `/tracker` (after Add) or back.

**Backend contract.** `GET /api/v1/scholarships/{id}`, `GET /api/v1/scholarships/{id}/provenance`. Premium tier may return 402 for non-premium.

**Anatomy.**
```
+--------------------------------------------------+
| TopBar with breadcrumb: Discover / {title}       |
+--------------------------------------------------+
| ScholarshipDetailHeader                          |
|   provider logo 56 / name Fraunces 32 italic /   |
|   validated stripe / 3 meta chips / CTA cluster  |
|     Primary: "Add to tracker"                    |
|     Secondary: "Save" / "Visit source"           |
+--------------------------------------------------+
| Body 2-column (lg+): left content / right aside  |
|   Left:                                          |
|     About / Eligibility (EligibilityMatrix) /   |
|     What's funded / How to apply / Documents     |
|   Right (sticky, 320 wide):                      |
|     Deadline countdown / Funding summary /       |
|     CompatibilityMeter / Provenance card         |
+--------------------------------------------------+
```

**States.**
- Empty: not applicable (an existing scholarship always has data).
- Loading: skeleton header + 4 paragraph blocks + aside.
- Loaded: golden path.
- Processing: Add-to-tracker → spinner on CTA, optimistic toast on success.
- Error: 404 → "This scholarship is no longer listed." with link to /discover. 5xx ErrorState page-level.
- Success: Add → toast "Added to Wishlist. Open tracker." with action link.
- Locked: premium for non-premium user → page renders header + UpgradeWall full overlay on body with `detail.message`.

**Interactions.** Add-to-tracker opens AddApplicationDialog with stage pre-set to Wishlist. Save toggles optimistically. Visit source opens external in new tab with `rel="noopener noreferrer"`.

**Motion.** Aside sticks at top: -32 offset, no animation. EligibilityMatrix row reveal stagger 60ms on load.

**Anti-slop check.**
- Banned: animated checkmark on eligibility row; "Apply now! ⚡" gradient button; provenance hidden in a footnote; AI-summary block above factual data.
- Allowed: validated stripe; "Source: chevening.org/apply/uk-{id}" mono link; "Last verified 2026-04-21" caption; explicit eligibility table.

**Copy strings.**
- Add CTA: "Add to tracker"
- Save tooltip: "Save without tracking"
- Visit source: "View on {provider}"
- Sticky aside title: "At a glance"
- Compatibility label: "Estimated Scholarship Fit Score" (never "Acceptance prediction")
- Provenance footer: "Source: {url}. Verified {date}."

**Accessibility.** EligibilityMatrix uses `<table>` with `<th scope>`. Compatibility meter has `role="meter"` with `aria-valuenow/min/max`. Sticky aside has `<aside>` with `aria-label="Scholarship summary"`.

**Responsive.**
- 375: aside becomes top card above body content.
- 1024+: 2-column with sticky right aside.

**Telemetry.** `scholarship.view {scholarship_id}`, `scholarship.add_tracker_click`, `scholarship.save_toggle`, `scholarship.visit_source_click`, `scholarship.upgrade_wall_shown`.

---

### 6.11 `/saved` — Saved Opportunities

**Purpose.** Let a student review the scholarships they bookmarked but have not yet tracked.

**Users + Entry.** Student. Entry: sidebar Saved. Next: `/scholarships/[id]` or `/tracker`.

**Backend contract.** `GET /api/v1/saved-opportunities`. `DELETE /api/v1/saved-opportunities/{id}`. `POST /api/v1/tracker` (promote to tracker).

**Anatomy.**
```
+----------------------------------+
| Page header: H1 + count          |
+----------------------------------+
| Sort: Recently saved / Deadline  |
+----------------------------------+
| List of saved scholarships       |
|   each: card with title +        |
|   deadline + Promote + Remove    |
+----------------------------------+
```

**States.**
- Empty: "Nothing saved yet. Use the save icon on any scholarship to bookmark it."
- Loading: 6 skeleton rows.
- Loaded: golden path.
- Processing: Promote → optimistic remove from saved + toast.
- Error: per-row error chip + retry.
- Success: toast "Moved to Wishlist in tracker."
- Locked: not applicable.

**Interactions.** Promote = `POST /api/v1/tracker` with stage=Wishlist + remove from saved on success. Remove = optimistic delete with undo toast (5s window).

**Motion.** Row remove: 220ms slide-up + fade out. Undo: row slides back in 180ms.

**Anti-slop check.**
- Banned: "You saved this 3 weeks ago!" guilt prompt; expiring saved-item countdown; reminder badge.
- Allowed: "Saved {date}" caption; sort by deadline; "Move to tracker" verb.

**Copy strings.**
- H1: "Saved"
- Sort: "Sort by"
- Promote: "Move to tracker"
- Remove: "Remove from saved"
- Empty: "Nothing saved yet. Use the save icon on any scholarship to bookmark it."

**Accessibility.** List `<ul role="list">`. Each row is `<li>` with two `<button>` actions. Undo toast has `aria-live="assertive"`.

**Responsive.**
- 375: card stack, actions move to overflow menu.
- 1024+: row layout with inline actions.

**Telemetry.** `saved.view`, `saved.promote {scholarship_id}`, `saved.remove {scholarship_id}`, `saved.sort_change {sort}`.

---

### 6.12 `/dashboard/scholarships/match` — Match Results

**Purpose.** Show a student the live match of their profile against the scholarship catalog, segmented into eligible / partial / stretch, respecting freemium caps.

**Users + Entry.** Student. Entry: end of onboarding, `/feed` "Find matches" tile, sidebar Matches. Next: `/scholarships/[id]`.

**Backend contract.** `POST /api/v1/scholarships/match` returns `{ items: [...], unlock_offer: { message, price, currency, plan } | null }`. Free cap = 3, Pro = 6, Elite = 12.

**Anatomy.**
```
+--------------------------------------------------+
| Page header: H1 + result count + Rerun button    |
+--------------------------------------------------+
| Tabs: Eligible (N) / Partial (N) / Stretch (N)   |
+--------------------------------------------------+
| Result grid: MatchCards 2-up (lg+), 1-up (sm)    |
|   each: CompatibilityMeter + title + provider +  |
|   deadline + funding + Save + Add CTA            |
+--------------------------------------------------+
| If cap hit: locked placeholders below grid       |
|   blurred preview + UpgradeWall inline           |
+--------------------------------------------------+
```

**States.**
- Empty: "No matches yet. Update your profile to broaden your match." + link to /profile.
- Loading: skeleton — 6 card placeholders.
- Loaded: golden path.
- Processing: Rerun → button spinner; grid fades to 0.4 opacity 200ms; on response crossfade 180ms.
- Error: "Couldn't compute matches. Retry." inline card.
- Success: result render.
- Locked (cap): below the unlocked cards, render 3–6 blurred placeholder cards behind an UpgradeWall with `unlock_offer.message` verbatim.

**Interactions.** Tab switch is instant (data already loaded). Card click → detail. Save / Add inline. Rerun re-POSTs match with current profile.

**Motion.** Tab indicator slides 220ms. Card hover lift only. Locked placeholders pulse opacity 0.4→0.5→0.4 over 1800ms (single subtle indicator that they are blocked).

**Anti-slop check.**
- Banned: "Your acceptance odds are 82%!"; "Top match for you 🏆"; auto-rerun on every focus; suggestion banner "Try these too".
- Allowed: "Estimated Scholarship Fit Score"; "3 eligible, 4 partial, 2 stretch"; "Rerun" not "Refresh AI".

**Copy strings.**
- H1: "Your matches"
- Tabs: "Eligible ({n})", "Partial ({n})", "Stretch ({n})"
- Rerun CTA: "Rerun match"
- Empty: "No matches yet. Update your profile to broaden your match."
- UpgradeWall: backend `unlock_offer.message`

**Accessibility.** Tabs are Radix Tabs (`role="tablist"`). Each MatchCard has `aria-describedby` referencing the compatibility meter. Locked placeholders are `aria-hidden="true"` and the wall is announced via `role="region"`.

**Responsive.**
- 375: tabs scroll horizontal; cards 1-up.
- 1024+: cards 2-up.

**Telemetry.** `match.view`, `match.tab_change {bucket}`, `match.rerun_click`, `match.card_click {scholarship_id}`, `match.upgrade_wall_shown {bucket}`, `match.upgrade_cta_click`.

---

### 6.13 `/tracker` — Kanban Application Tracker

**Purpose.** Let a student visualize their applications across 6 stages with a 14-key checklist per card and deadline urgency, respecting freemium caps.

**Users + Entry.** Student. Entry: sidebar Tracker, `/feed` summary stage click. Next: tracker card drawer (in-page).

**Backend contract.** `GET /api/v1/tracker`, `POST /api/v1/tracker`, `PATCH /api/v1/tracker/{id}/stage`, `PATCH /api/v1/tracker/{id}/checklist`, `DELETE /api/v1/tracker/{id}`. Free cap 3, Pro 6, Elite 12.

**Anatomy.**
```
+--------------------------------------------------+
| Page header: H1 + count "{n} of {cap}" + Add CTA |
+--------------------------------------------------+
| Deadline banner (if any deadline <14 days):      |
|   sindoor-soft bg, "{N} deadlines within 14 days"|
+--------------------------------------------------+
| Board: 6 columns horizontal scroll               |
|   Wishlist / Applied / Shortlisted / Pending /   |
|   Rejected / Accepted                            |
|   Each column: header (count) + cards + empty    |
|     dashed-border "Drag cards here" if empty     |
+--------------------------------------------------+
| Card drawer (slide-in right): full checklist,    |
|   deadline edit, stage select, delete            |
+--------------------------------------------------+
```

**States.**
- Empty (whole board): "No applications tracked yet. Add your first." center-screen.
- Empty (single column): dashed-border placeholder "Drag cards here".
- Loading: skeleton — 6 column headers + 3 card placeholders distributed.
- Loaded: golden path.
- Processing: card move → optimistic; on error rollback + toast.
- Error: per-card error chip with retry; whole-board fetch error: ErrorState.
- Success: stage change → silent (visual is the confirmation).
- Locked (cap exhausted): Add CTA disabled with tooltip "{plan} plan allows {cap} applications. Upgrade for more."
- Quota approaching: at cap-1, header count goes gold-leaf; tooltip "1 slot remaining."

**Interactions.** Drag-and-drop between columns (HTML5 native DnD; touch fallback: long-press card → context menu "Move to…"). Click card → drawer slide-in 220ms. Checklist toggle is optimistic. Delete = typed-confirm dialog ("Type the scholarship name to confirm").

**Motion.** Card grabbed: scale 1.0 → 1.02 + lift shadow 180ms. Drop: 220ms layout-bezier into new column. Drawer: 220ms ease-out slide-in from right.

**Anti-slop check.**
- Banned: trophy animation on move to Accepted; confetti on Accepted; "Hot streak" badge; AI-suggestion floating button.
- Allowed: subtle validated-soft column tint on Accepted; mono deadline countdown; checklist count "8 of 14 done".

**Copy strings.**
- H1: "Application tracker"
- Count: "{n} of {cap}"
- Add CTA: "Add application"
- Deadline banner: "{n} deadline{s} within 14 days"
- Stage labels: "Wishlist", "Applied", "Shortlisted", "Pending", "Rejected", "Accepted"
- Empty per column: "Drag cards here"
- Locked tooltip: "{plan} plan allows {cap} applications. Upgrade for more."

**Accessibility.** Each column is `<section role="region" aria-label="{stage}">`. Cards are `<article>` with drag handle as `<button>`. Keyboard alternative: focus card → Space picks up → Arrow keys move → Space drops. Drawer is a `<dialog>` with focus trap.

**Responsive.**
- 375: board scrolls horizontally; each column 280 wide; sticky column header.
- 1024+: 6 columns visible, no horizontal scroll.

**Telemetry.** `tracker.view`, `tracker.add_click`, `tracker.stage_change {tracker_id, from, to}`, `tracker.card_open {tracker_id}`, `tracker.checklist_toggle {tracker_id, key, value}`, `tracker.delete {tracker_id}`, `tracker.cap_hit {plan}`.

---

### 6.14 Tracker → Add Application Dialog

**Purpose.** Add a new tracker item with scholarship + stage + deadline + initial checklist defaults.

**Users + Entry.** Student. Entry: "Add application" CTA on `/tracker`, "Add to tracker" CTA on `/scholarships/[id]`. Next: returns to `/tracker` with new card visible.

**Backend contract.** `POST /api/v1/tracker` with `{scholarship_id, stage, deadline_at}`.

**Anatomy.**
```
+----------------------------------+
| Modal (max-w 560)                |
|   Title: "Add application"       |
|   Scholarship picker autocomplete|
|     (from match results + saved) |
|   Stage select (default Wishlist)|
|   Deadline date picker           |
|   Add CTA / Cancel               |
+----------------------------------+
```

**States.**
- Empty: pristine; Add disabled until scholarship picked.
- Loading: not applicable (autocomplete is local cached).
- Loaded: golden path.
- Processing: Add → spinner; on success modal closes + toast.
- Error: 402 (cap exhausted) → modal body replaces with UpgradeWall inline + close.
- Success: card appears in column optimistically.
- Locked: see error 402 above.

**Interactions.** Autocomplete with 200ms debounce. Date picker keyboard-navigable. Esc closes.

**Motion.** Modal: scrim fade 180ms, modal scale 0.96→1.0 + opacity 0→1 180ms.

**Anti-slop check.**
- Banned: "Great choice! 🎯" on add; auto-suggesting scholarships you've not matched; "AI recommends Wishlist".
- Allowed: pre-fill from deep link; "Tip: deadline within 14 days will appear in your dashboard banner."

**Copy strings.**
- Title: "Add application"
- Scholarship label: "Scholarship"
- Stage label: "Stage"
- Deadline label: "Deadline"
- Add CTA: "Add"

**Accessibility.** Modal as `<dialog>` with `aria-labelledby`. First focus on scholarship picker. Esc closes; Enter submits when valid.

**Responsive.** Modal stretches full-width on 375 with 16 side gutters.

**Telemetry.** `tracker.dialog_open`, `tracker.dialog_submit`, `tracker.dialog_cancel`, `tracker.dialog_error {error_code}`.

---

### 6.15 `/documents` — Documents List

**Purpose.** Show the student all generated documents (SOPs, professor emails, strategy reports, visa transcripts) with status and quick re-open.

**Users + Entry.** Student. Entry: sidebar Documents. Next: `/documents/[id]` or `/documents/sop` to create new.

**Backend contract.** `GET /api/v1/documents?type=&page=&page_size=`.

**Anatomy.**
```
+----------------------------------+
| Page header: H1 + Add CTA        |
|   (dropdown: SOP / Prof email)   |
+----------------------------------+
| Filter chips: All / SOP / Prof   |
|   email / Strategy / Visa        |
+----------------------------------+
| Table rows:                      |
|   icon / title / type chip /     |
|   updated / status / actions     |
+----------------------------------+
```

**States.**
- Empty: "No documents yet. Draft your first SOP." with primary CTA.
- Loading: 8 skeleton rows.
- Loaded: golden path.
- Processing: not applicable.
- Error: ErrorState in place of table.
- Success: not applicable.
- Locked: row-level lock chip for Elite documents (professor email, strategy report) on lower tiers.

**Interactions.** Row click → detail. Type chip click filters. Actions: open, duplicate, delete.

**Motion.** Row hover: paper-warm bg 90ms.

**Anti-slop check.**
- Banned: "AI-generated" tag on every row; sparkle next to titles; "Last edited by AI" line.
- Allowed: type chip with semantic color; "Updated 2026-05-12 14:22" mono; explicit "Draft" / "Final" status chip.

**Copy strings.**
- H1: "Documents"
- Add dropdown: "Draft SOP", "Draft professor email"
- Filter: "All", "SOPs", "Professor emails", "Strategy reports", "Visa transcripts"
- Empty: "No documents yet. Draft your first SOP."
- Status chips: "Draft", "Final"

**Accessibility.** Table with `<th scope="col">`. Status uses chip + ARIA text. Filter chips are `<button role="tab">`.

**Responsive.**
- 375: table collapses to cards; each card shows title + type + updated.
- 1024+: full table.

**Telemetry.** `documents.view`, `documents.filter {type}`, `documents.row_click {document_id}`, `documents.add_click {type}`, `documents.delete {document_id}`.

---

### 6.16 `/documents/[id]` — Document Detail

**Purpose.** Show a generated document with its 4-partition feedback (mentor or rubric), allow edit, allow re-generation.

**Users + Entry.** Student. Entry: documents list, deep link from tracker. Next: back to list or new draft.

**Backend contract.** `GET /api/v1/documents/{id}`. Polls every 5s while `status=processing`. `PATCH /api/v1/documents/{id}` for edits. `POST /api/v1/documents/{id}/regenerate` for re-draft.

**Anatomy.**
```
+--------------------------------------------------+
| TopBar with breadcrumb                            |
+--------------------------------------------------+
| Document header: title (Fraunces 24) + meta      |
|   type chip / version / Updated / Status         |
+--------------------------------------------------+
| 2-column (lg+):                                  |
|   Left: document body (rendered or editor)       |
|     generated stripe                             |
|   Right: feedback partitions (mentor or rubric)  |
|     Strengths / Revision priorities /            |
|     Caution notes / Summary                      |
+--------------------------------------------------+
| Footer actions: Edit / Regenerate / Download     |
+--------------------------------------------------+
```

**States.**
- Empty: not applicable.
- Loading: skeleton body + 4 feedback placeholders.
- Loaded: golden path.
- Processing: status=processing → body shows progress "Drafting paragraph {n} of {N}" with progress bar; feedback panels show "Available after generation completes."
- Error: status=failed → "Generation failed. {error_message}. Regenerate." CTA.
- Success: status=completed → full render.
- Locked (Elite feedback for non-Elite): feedback partitions render UpgradeWall inline with `detail.message`.

**Interactions.** Edit toggles body to textarea with toolbar. Regenerate prompts "Replace current draft?" inline. Download = .docx export.

**Motion.** Status transition processing → completed: progress bar fills last 220ms then fades.

**Anti-slop check.**
- Banned: "AI gave this an A!"; rotating motivational tip in feedback panel; "Try saying it like…" auto-suggestions.
- Allowed: explicit partition titles; "Revision priority 1 of 4: tighten paragraph 2 opening."

**Copy strings.**
- Status chips: "Drafting", "Draft", "Final", "Failed"
- Feedback partition titles: "Summary", "Strengths", "Revision priorities", "Caution notes"
- Edit CTA: "Edit"
- Regenerate CTA: "Regenerate"
- Download CTA: "Download .docx"
- Processing helper: "Drafting paragraph {n} of {N}"

**Accessibility.** Body is `<article>` with `aria-busy="true"` while processing. Status announces via `role="status"`. Editor textarea has `<label>`.

**Responsive.**
- 375: feedback collapses into accordion below body.
- 1024+: 2-column with sticky feedback aside.

**Telemetry.** `document.view {document_id, type}`, `document.edit_open`, `document.save`, `document.regenerate`, `document.download`, `document.poll_complete {duration_ms}`.

---

### 6.17 `/documents/sop` — SOP Builder

**Purpose.** Generate a Pakistan-context Statement of Purpose tailored to a target program in 30–60 seconds, with Elite line-by-line feedback if entitled.

**Users + Entry.** Student. Entry: sidebar Documents → Draft SOP, tracker card "Draft SOP" link (carries scholarship context), deep link from /scholarships/[id]. Next: `/documents/[id]` for the generated draft.

**Backend contract.** `POST /api/v1/documents/sop/draft` with `{scholarship_id?, target_program, target_provider, motivation_seed, pakistan_context}`. Free=1 lifetime, Pro=5/month, Elite=10/month.

**Anatomy.**
```
+--------------------------------------------------+
| Page header: H1 + quota chip "1 of 5 this month" |
+--------------------------------------------------+
| 2-panel layout                                   |
|   Left 40%: inputs (program / provider / seed /  |
|     context) + Generate CTA                      |
|   Right 60%: live preview (generated stripe)     |
|     while idle: editorial empty state            |
|     while drafting: progress + paragraph render  |
|     after complete: full SOP + Elite feedback    |
+--------------------------------------------------+
| Footer: Save / Discard                           |
+--------------------------------------------------+
```

**States.**
- Empty: preview shows "Your SOP will appear here as it generates." with example quote in muted ink.
- Loading: not applicable on entry (form is local).
- Loaded: golden path post-generation.
- Processing: "Drafting paragraph {n} of 5" + per-paragraph fill (paragraph appears once complete, not character-by-character — banned theatre). Save and Discard disabled during processing.
- Error: model error → "Couldn't generate. {detail}. Retry." Quota error → quota chip turns sindoor + "You've used your monthly SOP quota. Upgrade or wait until {date}."
- Success: preview fully rendered + toast "Saved as draft."
- Locked (quota exhausted): Generate CTA disabled with tooltip + inline UpgradeWall in preview area.

**Interactions.** "Use my profile" link populates motivation_seed with profile summary. Generate kicks off POST. While processing, user can edit input fields (queued; next generate uses latest). Save = persist as DocumentRecord. Discard = clear preview after confirm.

**Motion.** Paragraph reveal: each paragraph fades + slides 8px up 180ms ease-out once received. Progress bar fills smoothly. No typewriter.

**Anti-slop check.**
- Banned: typewriter character-by-character animation; "AI is writing your story… ✍️"; spinner-per-paragraph; "Generating brilliance"; floating mascot.
- Allowed: "Drafting paragraph 3 of 5"; named paragraph headings ("Motivation", "Academic background", "Why this program", "Why this country", "Future plan"); explicit quota chip.

**Copy strings.**
- H1: "Draft your SOP"
- Quota chip Free: "1 SOP, lifetime", Pro/Elite: "{used} of {cap} this month"
- Program label: "Target program"
- Provider label: "University or provider"
- Seed label: "Why this program (1–2 sentences)"
- Context label: "Pakistan context (optional — past internships, family, constraints)"
- Generate CTA: "Generate SOP"
- Processing: "Drafting paragraph {n} of 5"
- Quota exhausted (free): "You've used your free SOP. Upgrade to Pro for 5 SOPs a month."

**Accessibility.** Form fields each have `<label>`. Generate CTA disabled state announces via `aria-disabled`. Processing progress is `<progress>` with `aria-label="Generation progress"`. Preview is `<article aria-live="polite">`.

**Responsive.**
- 375: panels stack — inputs above, preview below.
- 1024+: 40/60 split.

**Telemetry.** `sop.view`, `sop.use_profile_click`, `sop.generate_attempt {scholarship_id?, target_program}`, `sop.generate_paragraph {n, duration_ms}`, `sop.generate_complete {duration_ms}`, `sop.generate_error {error_code}`, `sop.save`, `sop.discard`, `sop.quota_exhausted`.

---

### 6.18 `/documents/professor-email` — Professor Email

**Purpose.** Draft a personalized inquiry email to a target professor in 15–30 seconds. Elite-tier only in v1.

**Users + Entry.** Elite student. Entry: sidebar Documents → Draft professor email. Next: `/documents/[id]`.

**Backend contract.** `POST /api/v1/documents/professor-email` with `{professor_name, professor_affiliation, target_program, research_interest_overlap, your_summary}`. 402 for non-Elite.

**Anatomy.**
```
+----------------------------------+
| Page header + Elite chip         |
+----------------------------------+
| 2-panel (same as SOP)            |
|   Left: 5 inputs + Generate      |
|   Right: preview                 |
+----------------------------------+
| Tips footer (collapsible):       |
|   "Email guidelines for          |
|    professors in UK / US / DE"   |
+----------------------------------+
```

**States.**
- Empty: preview "Your email will appear here." + 3-bullet tips ("Subject line stays specific", "Cite their work in 1 sentence", "Ask one clear question").
- Loading: not applicable on entry.
- Loaded: post-generation render.
- Processing: "Drafting email…" single progress bar (email is short — no per-paragraph).
- Error: same as SOP error patterns.
- Success: toast "Saved as draft."
- Locked: full-screen UpgradeWall with `detail.message` for non-Elite.

**Interactions.** "Find researcher" link opens `/discover?type=researcher` (out of v1 scope; renders a "Coming Q3" badge). Copy-to-clipboard button on preview.

**Motion.** Same as SOP processing pattern.

**Anti-slop check.**
- Banned: "Hi Professor [Name]!" boilerplate left in output; emoji greeting; "Looking forward to hearing from you!" canned closer.
- Allowed: explicit subject line in mono; named professor; one specific paper cited.

**Copy strings.**
- H1: "Draft a professor email"
- Elite chip: "Elite"
- Inputs: "Professor name", "Affiliation", "Target program", "Research overlap (1–2 sentences)", "About you (1 sentence)"
- Generate CTA: "Generate email"
- Locked: backend `detail.message`

**Accessibility.** Same as SOP. Elite chip is a `<span aria-label="Elite tier feature">`. Tips section is a `<details>`.

**Responsive.** Same as SOP.

**Telemetry.** `prof_email.view`, `prof_email.generate_attempt`, `prof_email.generate_complete`, `prof_email.locked_view`, `prof_email.copy_click`.

---

### 6.19 `/interviews` — Interviews List

**Purpose.** Show the student all past interview sessions (visa + generic adaptive) with rubric trends.

**Users + Entry.** Student. Entry: sidebar Interviews. Next: `/interviews/[id]` or `/interviews/visa`.

**Backend contract.** `GET /api/v1/interviews?type=&page=`.

**Anatomy.**
```
+----------------------------------+
| Page header + 2 CTAs:            |
|   Practice visa / Practice generic|
+----------------------------------+
| Trend strip: 5 rubric chips with |
|   small sparklines (mono)        |
+----------------------------------+
| Sessions table:                  |
|   icon / type / country / date / |
|   summary score / open           |
+----------------------------------+
```

**States.**
- Empty: "No sessions yet. Practice your first visa interview." + Visa CTA.
- Loading: skeleton trend strip + 6 rows.
- Loaded: golden path.
- Processing: not applicable.
- Error: ErrorState in table area.
- Success: not applicable.
- Locked: not applicable (sessions are gated at start).

**Interactions.** Row click → `/interviews/[id]` (generic) or `/interviews/visa?session={id}`.

**Motion.** Sparklines render once on intersection, 600ms ease-out.

**Anti-slop check.**
- Banned: streak counter "5-day practice streak! 🔥"; level-up animation; "Coach of the day" widget.
- Allowed: trend chips ("Confidence: 7.2 ↑ from 6.4"); mono date "2026-05-14 18:22".

**Copy strings.**
- H1: "Interviews"
- CTAs: "Practice visa", "Practice generic"
- Trend strip labels: "Motivation", "Finances", "Ties", "Communication", "Overall"
- Empty: "No sessions yet. Practice your first visa interview."

**Accessibility.** Trend chips render numbers and `<svg>` sparklines with `aria-hidden` (numeric value is the accessible name).

**Responsive.**
- 375: trend strip scrolls horizontally; table → cards.
- 1024+: full table.

**Telemetry.** `interviews.view`, `interviews.row_click {session_id}`, `interviews.cta_visa_click`, `interviews.cta_generic_click`.

---

### 6.20 `/interviews/[id]` — Generic Adaptive Interview

**Purpose.** Practice generic interview Q&A (admissions, scholarship, fellowship) with adaptive difficulty and rubric feedback.

**Users + Entry.** Student. Entry: row click from /interviews. Next: same screen continues until session ends.

**Backend contract.** `GET /api/v1/interviews/{id}`, `POST /api/v1/interviews/{id}/answer`, `GET /api/v1/interviews/{id}/summary`.

**Anatomy.** Same shape as visa simulator (§6.21) without country setup screen. Re-uses QuestionCard, FeedbackPanel, SummaryRadar, SessionSummary.

**States.** Same template as §6.21.

**Interactions.** Same as §6.21.

**Motion.** Same as §6.21.

**Anti-slop check.** Same as §6.21.

**Copy strings.**
- H1: "Practice interview — {topic}"

**Accessibility.** Same as §6.21.

**Responsive.** Same as §6.21.

**Telemetry.** `interview_generic.*` events mirror visa events.

---

### 6.21 `/interviews/visa` — Visa Interview Simulator

**Purpose.** Practice a country-specific visa interview: setup → Q&A loop → study-mode feedback → summary radar. Free cuts at Q3. Elite persists transcript.

**Users + Entry.** Student. Entry: sidebar Interviews → Practice visa, `/feed` Practice visa tile, deep link. Next: `/interviews/[id]` for summary.

**Backend contract.** `POST /api/v1/interviews/visa/start` with `{country_code, mode: "study"|"exam"}`. `POST /api/v1/interviews/visa/{id}/answer` with `{text}`. `GET /api/v1/interviews/visa/{id}/summary`. Elite: transcript persisted as DocumentRecord.

**Anatomy (3 panes).**
```
[1] SetupScreen
+----------------------------------+
| H1 "Practice visa interview"     |
+----------------------------------+
| Country tile grid (4×1 lg, 2×2sm)|
|   each: country name + Q count + |
|   approval estimate chip         |
+----------------------------------+
| Mode toggle: Study / Exam        |
+----------------------------------+
| Start CTA                        |
+----------------------------------+

[2] QuestionCard (one at a time)
+----------------------------------+
| Progress: "Question {n} of {N}"  |
+----------------------------------+
| Question text (Fraunces 24)      |
+----------------------------------+
| Answer input (textarea + mic)    |
+----------------------------------+
| Submit / Skip                    |
+----------------------------------+
| (Study mode) FeedbackPanel       |
|   slides in after submit         |
+----------------------------------+

[3] SessionSummary
+----------------------------------+
| H1 "Session summary"             |
+----------------------------------+
| SummaryRadar (5 axes)            |
+----------------------------------+
| Transcript preview (Elite)       |
+----------------------------------+
| Practice again / Save transcript |
+----------------------------------+
```

**States.**
- Empty: SetupScreen renders default.
- Loading: setup — country tiles skeleton (4); Q&A — full panel skeleton; summary — radar placeholder.
- Loaded: golden path.
- Processing: Submit → button spinner; FeedbackPanel (study mode) loads in 180ms after answer; in exam mode, next question immediately.
- Error: per-action inline; transcript save error → toast.
- Success: each question advance is the success signal; summary appears at session end.
- Locked: free hits Q3 cutoff → "Free practice ends here. Upgrade to Pro for full sessions." inline UpgradeWall. Elite-only transcript export shows lock on non-Elite.

**Interactions.** Mic press-and-hold; release submits text via STT (out of v1 — render as "Coming Q3" badge in mic button tooltip). Text input always available. Skip increments to next question without submission. Esc returns to setup with confirm.

**Motion.** Question transition: outgoing fade 140ms + 8px slide up; incoming fade 180ms + 8px slide from bottom. FeedbackPanel slide-in from right 220ms. SummaryRadar: axes draw 600ms ease-out once.

**Anti-slop check.**
- Banned: "Great answer! 🎉"; applause sound on submit; "AI Coach" persona; flag emoji on country tiles; live scrolling transcript like a chatbot; auto-replay confidence loops.
- Allowed: "Question 3 of 10"; rubric scores "Motivation 7/10"; specific feedback "Your answer didn't address why this country specifically — try naming UK universities you applied to."

**Copy strings.**
- Setup H1: "Practice visa interview"
- Mode toggle: "Study mode (feedback after each answer)", "Exam mode (feedback at end)"
- Country tile: "{country_name}", "{n} questions", "Approval estimate: {pct} (educated estimate)"
- Q&A submit: "Submit"
- Skip: "Skip"
- Free cutoff: "Free practice covers 3 questions. Upgrade to Pro for full sessions."
- Summary H1: "Session summary"
- Save transcript CTA (Elite): "Save transcript to documents"

**Accessibility.** Mic button has `aria-label="Hold to record answer"` (and `aria-disabled` while coming-Q3). Progress is `<progress>`. SummaryRadar provides tabular fallback below the chart for screen readers.

**Responsive.**
- 375: Setup 2×2 tiles; Q&A panel single column; Summary radar 280 wide.
- 1024+: setup 4×1; Q&A 720 max-w; FeedbackPanel right aside.

**Telemetry.** `visa.setup_view`, `visa.session_start {country, mode}`, `visa.answer_submit {q_index, duration_ms}`, `visa.answer_skip {q_index}`, `visa.cutoff_hit {plan}`, `visa.summary_view`, `visa.transcript_save`, `visa.practice_again_click`.

---

### 6.22 `/profile` — Profile Editor (6 cards)

**Purpose.** Let a student maintain the full profile that drives matches, B2B share snapshots, and SOP context.

**Users + Entry.** Student. Entry: sidebar Profile, /feed ProfileCompleteCard CTA. Next: any in-app destination.

**Backend contract.** `GET /api/v1/profile/me`, `PATCH /api/v1/profile/me`. `GET /api/v1/universities?country={code}` for shortlist picker.

**Anatomy.**
```
+--------------------------------------------------+
| Page header: H1 + completion meter               |
+--------------------------------------------------+
| 6 cards (stacked):                               |
|   1. Contact (email locked, phone, whatsapp,     |
|        city of origin)                           |
|   2. Academic (current uni, degree, GPA, grad)   |
|   3. Tests (language, GRE, GMAT, SAT)            |
|   4. Goal (target countries[], fields[],         |
|        degree level, intake, funding requirement)|
|   5. Aspirations (target universities[],         |
|        research interest, work experience)       |
|   6. Background (household income band,          |
|        referral source, B2B share consent)       |
+--------------------------------------------------+
| Save / Discard (sticky footer when dirty)        |
+--------------------------------------------------+
```

**States.**
- Empty: pristine fields with placeholders matching field semantics.
- Loading: skeleton — 6 card placeholders.
- Loaded: golden path.
- Processing: Save → button spinner; on success "Saved" chip 2s.
- Error: per-field error; whole-form error → toast with retry.
- Success: dirty footer dismisses.
- Locked: not applicable (profile is always editable). B2B share consent toggle has a separate Pro+ gate text below it.

**Interactions.** Auto-save on field blur (debounced 800ms). Manual Save also available for assurance. Discard reverts to last server state.

**Motion.** Sticky footer slide-up 220ms when dirty; slide-down 140ms when saved/discarded. Completion meter tweens 300ms.

**Anti-slop check.**
- Banned: "Profile strength: Excellent ⭐⭐⭐⭐⭐"; AI-prefilling fields from typing in another field; "Pro tip" banner inside card.
- Allowed: completion meter "{pct}% complete"; field-level helper "Used for SOP context, not shared with universities."; B2B section explicit consent.

**Copy strings.**
- H1: "Profile"
- Card titles: "Contact", "Academic record", "Test scores", "Your goal", "Aspirations", "Background"
- Save: "Save changes"
- Discard: "Discard"
- B2B consent label: "Allow AidwiseAI to share an anonymized snapshot with partner universities you opt into."
- B2B consent helper: "Pro+ feature. Snapshot captured at share time. You can revoke anytime."

**Accessibility.** Each card is a `<section aria-labelledby>`. Sticky footer announces "Unsaved changes" via `role="status"` when first dirty.

**Responsive.**
- 375: cards full-width stack.
- 1024+: cards 720 max-w centered.

**Telemetry.** `profile.view`, `profile.field_save {field}`, `profile.save_all`, `profile.discard`, `profile.b2b_consent_toggle {value}`, `profile.completion_meter {pct}`.

---

### 6.23 `/settings` — Settings (incl. Privacy panel)

**Purpose.** Let a student manage account, privacy, notifications, density, plan, and destructive actions (export, delete).

**Users + Entry.** Student. Entry: sidebar Settings, TopBar avatar menu → Settings. Next: any in-app destination.

**Backend contract.** `GET/PATCH /api/v1/auth/me` for account fields. `POST /api/v1/privacy/data-export`, `POST /api/v1/privacy/account-deletion`, `DELETE /api/v1/privacy/account-deletion`. `PATCH /api/v1/profile/me` for marketing/notifications opt-in.

**Anatomy.**
```
+--------------------------------------------------+
| Page header: H1                                  |
+--------------------------------------------------+
| Left rail (lg+) tabs: Account / Privacy /        |
|   Notifications / Appearance / Plan / Danger     |
+--------------------------------------------------+
| Right pane: tab content                          |
+--------------------------------------------------+
```

**Tab contents.**
1. **Account** — display name, email (locked), password change (link), session list with revoke.
2. **Privacy** — cookie preferences (4 toggles), marketing opt-in, B2B share consent (Pro+), data export request + history, consent history table.
3. **Notifications** — email digest frequency (Daily / Weekly / Off), deadline reminders (On / Off), WhatsApp alerts (Elite only).
4. **Appearance** — density (Comfortable / Compact), reduced motion (Auto / On / Off), language (English / اردو — Urdu out of v1 stub).
5. **Plan** — current plan chip, billing country, currency, "See pricing" link, "Cancel renewal" (when applicable).
6. **Danger** — Export my data (POST → status card), Delete my account (typed-confirm dialog → POST → 30-day window with cancel).

**States.**
- Empty per tab: not applicable.
- Loading: per-tab skeleton.
- Loaded: golden path.
- Processing: Each toggle is optimistic with rollback toast.
- Error: inline per-control.
- Success: chip "Saved" 2s.
- Locked: B2B share consent is disabled with helper "Available on Pro and Elite." WhatsApp alerts disabled with "Available on Elite."

**Interactions (Danger).**
- Export = single click → status card appears: "Export requested. We'll email you when it's ready (usually <1 hour)."
- Delete = typed-confirm dialog requires user to type "DELETE MY ACCOUNT" verbatim. On success → 30-day window: full-screen takeover with mono countdown + Cancel deletion CTA.

**Motion.** Tab change: pane fades 140ms exit + 180ms enter. Toggle: micro 90ms color/opacity. Danger dialog: scrim + scale-in same as standard modal.

**Anti-slop check.**
- Banned: "Are you sure you want to leave? 😢"; satisfaction survey on delete; "We'll miss you!" copy; auto-export without confirmation.
- Allowed: explicit "DELETE MY ACCOUNT" typed-confirm; 30-day window countdown; consent history table.

**Copy strings.**
- H1: "Settings"
- Tabs: "Account", "Privacy", "Notifications", "Appearance", "Plan", "Danger"
- Privacy explainer: "We follow PDPB. Sensitive categories (religion, politics, biometric) are never collected."
- Export CTA: "Export my data"
- Export status: "Your export is being prepared. Estimated ready: {time}."
- Delete CTA: "Delete my account"
- Delete confirm helper: "Type DELETE MY ACCOUNT to confirm. You have 30 days to cancel."
- 30-day banner: "Your account will be deleted on {date}. Cancel deletion."

**Accessibility.** Tabs as Radix Tabs. Danger pane uses `role="region" aria-label="Danger zone"`. Typed-confirm input has `aria-describedby` referencing the helper.

**Responsive.**
- 375: tabs become horizontal scroll chips above pane.
- 1024+: left rail tabs.

**Telemetry.** `settings.view {tab}`, `settings.toggle {tab, key, value}`, `settings.export_request`, `settings.delete_request`, `settings.delete_cancel`, `settings.consent_history_view`.

---

### 6.24 `/admin` — Admin KPI Overview

**Purpose.** Give an operator a 5-second read on platform health (ingestion, curation, matches, alerts) with polling.

**Users + Entry.** Admin/owner. Entry: post-login (if admin). Next: any admin sub-route.

**Backend contract.** `GET /api/v1/analytics?since=` (polls every 60s).

**Anatomy.**
```
+--------------------------------------------------+
| Page header + Refresh button + Auto-refresh chip |
+--------------------------------------------------+
| KPI grid 4 columns:                              |
|   Ingestion (24h) / Curation backlog /           |
|   Match volume (24h) / Alerts fired (24h)        |
| Each: number mono 32 + trend chip + sparkline    |
+--------------------------------------------------+
| Alerts table (last 10): time / severity /        |
|   source / message / link                        |
+--------------------------------------------------+
```

**States.**
- Empty: "No KPI data in the last 24 hours."
- Loading: skeleton — 4 KPI cards + 10 alert rows.
- Loaded: golden path.
- Processing: polling refresh is silent (no overlay); on success crossfade 180ms on numbers only.
- Error: ErrorState replaces grid; polling pauses with retry button.
- Success: not applicable (read-only).
- Locked: not applicable.

**Interactions.** Refresh manual. Auto-refresh toggle.

**Motion.** Number crossfade 180ms on poll update.

**Anti-slop check.**
- Banned: "All systems go ✅"; rainbow status indicator; "Health score: 99.9!"; auto-tweet of KPIs.
- Allowed: explicit values; "Ingestion: 12 runs (8 success, 4 degraded)"; severity color chips.

**Copy strings.**
- H1: "Overview"
- KPI titles: "Ingestion (24h)", "Curation backlog", "Match volume (24h)", "Alerts fired (24h)"
- Auto-refresh chip: "Auto-refresh: 60s"

**Accessibility.** Auto-refresh polling pauses when user focuses any control. Number changes announce only when changed by >10%.

**Responsive.**
- 375: KPI grid 1×4 stack.
- 1024+: 4×1 row.

**Telemetry.** `admin.overview_view`, `admin.refresh_click`, `admin.auto_refresh_toggle`, `admin.alert_click {alert_id}`.

---

### 6.25 `/admin/ingestion` + `/admin/ingestion/[id]` — Ingestion

**Purpose.** Manage scraper sources and runs: start runs, view diagnostics, retry, audit source health.

**Users + Entry.** Admin. Entry: sidebar Ingestion. Next: source detail, audit, curation.

**Backend contract.** `GET /api/v1/curation/sources`, `POST /api/v1/curation/sources/{id}/run`, `GET /api/v1/curation/ingestion-runs?source_id=`, `GET /api/v1/curation/ingestion-runs/{id}` (with diagnostics + snapshot).

**Anatomy (list).**
```
+--------------------------------------------------+
| Header + bulk actions (Start selected / Retry)   |
+--------------------------------------------------+
| Filter: status (all/healthy/degraded/down) +     |
|   country + last-run age                         |
+--------------------------------------------------+
| Sources table: select / name / status chip /     |
|   last run / failure count / next ETA / actions  |
+--------------------------------------------------+
| Pagination                                       |
+--------------------------------------------------+
```

**Anatomy (detail).**
```
+--------------------------------------------------+
| Source header + status                           |
+--------------------------------------------------+
| Run timeline: vertical list of runs              |
|   each: status / start / duration / records /    |
|   diagnostics expand                             |
+--------------------------------------------------+
| Diagnostics panel: parser logs / HTTP traces /   |
|   snapshot diff / errors                         |
+--------------------------------------------------+
| Snapshot viewer (collapsible, 720 max-w mono)    |
+--------------------------------------------------+
```

**States.**
- Empty (list): "No sources registered yet."
- Empty (detail): "No runs for this source yet. Start one."
- Loading: skeleton rows / timeline.
- Loaded: golden path.
- Processing: starting a run → row status chip transitions to "Running" with mono spinner.
- Error: per-row error chip + retry; whole-page error ErrorState.
- Success: silent (state chip is the signal).
- Locked: not applicable.

**Interactions.** Bulk select with shift-click range. Filter persists in URL. Diagnostics panel is `<details>`.

**Motion.** Row status crossfade 180ms on poll update. Diagnostics expand 220ms.

**Anti-slop check.**
- Banned: "Healthy 💚"; flame emoji on degraded; auto-restart loop on every page focus.
- Allowed: status chip ("Healthy / Degraded / Down"); mono "Last run: 2026-05-17 12:14"; explicit fail count.

**Copy strings.**
- H1: "Ingestion sources"
- Source table cols: "Name", "Status", "Last run", "Failures", "Next ETA"
- Detail H1: "{source name}"
- Run row: "Run {id} — {status}", "Records: {count}", "Duration: {duration}"

**Accessibility.** Bulk select uses `<input type="checkbox">` with `aria-label`. Run list is `<ol>` with semantic ordering. Diagnostics `<pre>` for logs.

**Responsive.**
- 375: table → cards; bulk select disabled (use detail).
- 1024+: full table.

**Telemetry.** `admin.ingestion_view`, `admin.ingestion_filter {filter}`, `admin.ingestion_start_run {source_id}`, `admin.ingestion_retry {source_id}`, `admin.ingestion_detail_view {source_id}`, `admin.ingestion_run_expand {run_id}`.

---

### 6.26 `/admin/curation` + `/admin/curation/[id]` — Curation

**Purpose.** Move records from raw → validated → published, with audit trail.

**Users + Entry.** Admin. Entry: sidebar Curation. Next: record detail.

**Backend contract.** `GET /api/v1/curation/records?state=`, `PATCH /api/v1/curation/records/{id}`, audit on every change.

**Anatomy (list).**
```
+--------------------------------------------------+
| Header + state filter (raw/validated/published)  |
+--------------------------------------------------+
| Records table: title / source / state /          |
|   confidence / updated / open                    |
+--------------------------------------------------+
```

**Anatomy (detail).**
```
+--------------------------------------------------+
| Header: title + state chip + confidence chip     |
+--------------------------------------------------+
| 2-column: left edit form (title, provider,       |
|   funding, deadline, country, field, tier,       |
|   eligibility) / right preview (rendered card)   |
+--------------------------------------------------+
| Audit trail (collapsible): 10 latest changes     |
+--------------------------------------------------+
| Footer: Discard / Save / Promote                 |
+--------------------------------------------------+
```

**States.** Similar to other admin screens; processing on save; error inline; success crossfade preview.

**Interactions.** Promote requires state-machine valid transition. Audit entries are read-only.

**Motion.** Preview crossfade 180ms on field commit.

**Anti-slop.**
- Banned: AI auto-fill button labelled "Auto-curate ✨"; gold star on high-confidence; emoji status.
- Allowed: confidence chip "0.87"; promote button labelled by next-state; audit row "Promoted to validated by {admin} at {time}".

**Copy strings.** "Curation", "Raw", "Validated", "Published", "Promote to validated", "Promote to published", "Audit trail".

**Accessibility.** Form fields fully labelled. State chip carries `aria-label="Current state: validated"`.

**Responsive.** Detail collapses to single column on 375 with preview as accordion below.

**Telemetry.** `admin.curation_view`, `admin.curation_filter`, `admin.curation_detail_view {id}`, `admin.curation_save {id}`, `admin.curation_promote {id, from, to}`.

---

### 6.27 `/admin/users` — Users

**Purpose.** Search users, change plan, change role, force password reset.

**Users + Entry.** Admin/owner. Entry: sidebar Users.

**Backend contract.** `GET /api/v1/access-control/users?q=`, `PATCH /api/v1/access-control/users/{id}` (plan/role), `POST /api/v1/access-control/users/{id}/reset-password`.

**Anatomy.**
```
+----------------------------------+
| Search + filter (role/plan)      |
+----------------------------------+
| Users table: email / name / role |
|   / plan / created / actions     |
+----------------------------------+
| Pagination                       |
+----------------------------------+
```

**States.** Standard admin patterns.

**Interactions.** Role mutation opens dialog with select + reason field + confirm. Password reset → confirm dialog → POST → toast.

**Motion.** Row update crossfade 180ms.

**Anti-slop.**
- Banned: "Make admin 👑"; role chip with crown emoji.
- Allowed: text role chip; explicit "Reason for role change" field; audit-log "Role changed by {admin} at {time}".

**Copy.** "Users", "Search by email or name", role chips, "Change role", "Reset password".

**Accessibility.** Mutation dialog focus-trapped. Reason field required and `aria-required`.

**Responsive.** Table → cards on 375.

**Telemetry.** `admin.users_view`, `admin.users_search {q}`, `admin.users_role_change {user_id, from, to}`, `admin.users_password_reset {user_id}`.

---

### 6.28 `/admin/audit` — Audit

**Purpose.** Searchable audit log of admin actions for compliance.

**Users + Entry.** Admin/owner. Entry: sidebar Audit.

**Backend contract.** `GET /api/v1/access-control/audit?actor=&action=&since=`.

**Anatomy.**
```
+----------------------------------+
| Filters: actor / action / range  |
+----------------------------------+
| Audit table: time / actor /      |
|   action / target / diff         |
+----------------------------------+
```

**States.** Standard. Empty: "No audit entries match these filters." Loading: 20 skeleton rows. Error: ErrorState.

**Interactions.** Diff expand inline. Revert action (if applicable) opens typed-confirm dialog.

**Motion.** Row diff expand 220ms.

**Anti-slop.**
- Banned: "View as story" timeline ribbon; emoji severity badges.
- Allowed: mono timestamps; structured diff blocks.

**Copy.** "Audit", "Actor", "Action", "Target", "Revert".

**Accessibility.** Diff `<pre>` with `aria-label`. Revert button confirms via typed-confirm.

**Responsive.** Table → stacked cards on 375.

**Telemetry.** `admin.audit_view`, `admin.audit_filter`, `admin.audit_revert {entry_id}`.

---

### 6.29 `/admin/rec-eval` — Recommendation Benchmarks

**Purpose.** Show recommendation quality metrics across benchmark cases.

**Users + Entry.** Admin/owner.

**Backend contract.** `GET /api/v1/recommendations/benchmarks`.

**Anatomy.**
```
+----------------------------------+
| Aggregate chart (recall, prec)   |
+----------------------------------+
| Per-case table                   |
+----------------------------------+
```

**States.** Standard.

**Interactions.** Click per-case → diff modal showing expected vs actual.

**Motion.** Chart axes draw once 600ms.

**Anti-slop.**
- Banned: leaderboard-style ranking; "AI improved by 12% 🚀"; trophy on best case.
- Allowed: explicit metric definitions; mono percentages.

**Copy.** "Recommendation evaluation", "Recall", "Precision", "Per-case results".

**Accessibility.** Chart provides tabular fallback.

**Responsive.** Chart full-width on 375 with horizontal table scroll.

**Telemetry.** `admin.rec_eval_view`, `admin.rec_eval_case_click {case_id}`.

---

### 6.30 `/mentor/queue` + `/mentor/documents/[id]` — Mentor

**Purpose.** Let a mentor review student SOPs and submit structured feedback (summary, strengths, revision priorities, caution notes).

**Users + Entry.** Mentor. Entry: post-login (mentor role) → /mentor/queue.

**Backend contract.** `GET /api/v1/mentor/queue`, `GET /api/v1/mentor/documents/{id}`, `POST /api/v1/mentor/documents/{id}/review`.

**Anatomy (queue).**
```
+----------------------------------+
| Header: H1 + count               |
+----------------------------------+
| Filter: type / urgency           |
+----------------------------------+
| Queue list: student email /      |
|   type / submitted / take CTA    |
+----------------------------------+
```

**Anatomy (review).**
```
+----------------------------------+
| 2-column                         |
| Left: document body (read-only)  |
| Right: review form               |
|   Summary / Strengths /          |
|   Revision priorities (ordered)/ |
|   Caution notes / Submit         |
+----------------------------------+
```

**States.**
- Empty (queue): "Queue is empty."
- Loading: skeleton.
- Loaded: golden path.
- Processing: Submit spinner; on success → return to queue + toast.
- Error: inline per-field.
- Success: queue row removed; next item highlighted.
- Locked: not applicable.

**Interactions.** Revision priorities are an ordered drag-reorder list (1-N). Caution notes optional. Submit confirms count of priorities.

**Motion.** List reorder 220ms.

**Anti-slop.**
- Banned: AI-suggested feedback templates; "Mentor of the month" badge; auto-grade slider.
- Allowed: explicit field labels; "Submit review to {student_email}"; structured priorities.

**Copy.**
- Queue H1: "Mentor queue"
- Review H1: "Review for {student_email}"
- Submit: "Submit review"
- Caution helper: "Optional. Use for tone or eligibility concerns."

**Accessibility.** Drag-reorder has keyboard fallback (Up/Down arrows when focused).

**Responsive.**
- 375: document body collapses to "View document" link, form full-width.
- 1024+: 2-column.

**Telemetry.** `mentor.queue_view`, `mentor.take_doc {doc_id}`, `mentor.review_save {doc_id}`, `mentor.review_priority_reorder`.

---

### 6.31 `/partners` + `/partners/universities` — Partners

**Purpose.** Let a partner (university admin) view their institution dashboard and manage university listings.

**Users + Entry.** Partner role. Entry: post-login. Next: /partners/universities.

**Backend contract.** `GET /api/v1/b2b/institution`, `GET /api/v1/universities?institution_id=`, `PATCH /api/v1/universities/{id}`.

**Anatomy.** Mirror admin patterns: header + filter + table + detail editor.

**States.** Standard.

**Interactions.** Institution-scoped — partner cannot see other institutions' data.

**Motion.** Standard.

**Anti-slop.**
- Banned: "Recruit students 🎓"; engagement leaderboard with emoji ranks.
- Allowed: explicit metrics (DPA signed at, snapshot count); structured edit form.

**Copy.** "Partners", "Universities", "DPA signed: {date}", "Snapshots received: {count}".

**Accessibility.** Standard.

**Responsive.** Standard.

**Telemetry.** `partners.view`, `partners.universities_view`, `partners.university_edit {id}`.

---

### 6.32 `404` Not Found

**Purpose.** Tell a user the URL doesn't exist and route them somewhere useful.

**Anatomy.**
```
+----------------------------------+
| H1 "Page not found."             |
| Description                      |
| 2 CTAs: Go home / See pricing    |
+----------------------------------+
```

**States.** Single state.

**Copy.**
- H1: "We couldn't find that page."
- Description: "The link may be broken or the page may have moved."
- CTAs: "Go to dashboard" (auth) / "Go to AidwiseAI" (public), "See pricing"

**Anti-slop.** Banned: "Lost in space 🚀", broken-robot illustration. Allowed: text-only, useful CTAs.

**Accessibility.** Single H1.

**Telemetry.** `system.404 {path}`.

---

### 6.33 `500` Server Error

**Purpose.** Tell a user something went wrong on our side and let them retry or report.

**Anatomy.** Similar to 404.

**Copy.**
- H1: "Something went wrong on our side."
- Description: "We've logged the error. Try again, or email support@aidwiseai.pk."
- CTAs: "Try again", "Email support"

**Anti-slop.** Banned: hand-drawn frown face, "Oopsy daisy". Allowed: explicit, useful.

**Accessibility.** Includes incident ID mono for support reference (`<code>{request_id}</code>`).

**Telemetry.** `system.500 {path, request_id}`.

---

### 6.34 `/offline` Offline / Network Failure

**Purpose.** Detect offline state and pause polling, queue mutations, inform the user.

**Anatomy.** Persistent top banner: "You're offline. Changes will sync when you reconnect."

**States.**
- Offline: banner sticky top + each form has "Will save when online" helper.
- Reconnecting: banner morphs "Reconnecting…" 90ms color shift.
- Online: banner dismisses 140ms; toast "Back online. Synced N changes."

**Copy.**
- Banner: "You're offline. Changes will sync when you reconnect."
- Toast: "Back online. {n} change{s} synced."

**Anti-slop.** Banned: "No internet 😢", retry counter. Allowed: explicit state, sync counter.

**Telemetry.** `system.offline`, `system.reconnect {queued_count}`.

---

### 6.35 `/denied` RBAC Denied

**Purpose.** Tell a user they don't have access to the requested resource.

**Copy.**
- H1: "You don't have access to that."
- Description: "If you think this is wrong, email support@aidwiseai.pk."
- CTAs: "Go to dashboard", "Email support"

**Anti-slop.** Banned: lock-with-key animation, "Naughty naughty!" Allowed: plain.

**Telemetry.** `system.denied {path, role}`.

---

### 6.36 `/maintenance` Maintenance Window

**Purpose.** Take the app down with grace during a scheduled maintenance window.

**Copy.**
- H1: "AidwiseAI is down for scheduled maintenance."
- Description: "We expect to be back by {end_time_pkt}. Thanks for your patience."

**Anti-slop.** Banned: "Working hard! 💪" illustration, fake-progress bar. Allowed: explicit end time, status link.

**Telemetry.** `system.maintenance_view`.

---

## §7 Copy System

### 7.1 Brand strings

- Display brand: **AidwiseAI** (exact casing). Never "Aidwise AI" or "AidwiseAI AI".
- Tagline: "Funded master's degrees, found for you."
- Short pitch: "AidwiseAI matches Pakistani students with fully-funded scholarships in the UK, US, Canada, Germany, and Australia."
- Mailto: `partnerships@aidwiseai.pk`, `support@aidwiseai.pk`.
- Domain: `aidwiseai.com` (production), `aidwiseai.pk` (alternate).

### 7.2 CTA verb library

Allowed: Add, Generate, Draft, Save, Submit, Practice, Continue, Get started, Sign in, Show, Run, Rerun, See, Open, View, Edit, Delete, Cancel, Confirm, Promote, Move, Skip, Try again, Retry, Download, Copy, Email, Visit, Match, Track, Discover.

Banned: Unlock, Unleash, Boost, Supercharge, Hack, Crush, Dominate, Master, Maximize, Optimize (as user-facing verb).

### 7.3 Empty-state copy register

Empty state = (icon) + (specific reason) + (immediate next action). Never "No data".

- Matches: "No matches yet. Update your profile to broaden your match." + "Edit profile"
- Tracker: "No applications tracked yet. Add your first." + "Add application"
- Saved: "Nothing saved yet. Use the save icon on any scholarship to bookmark it." + (no CTA, instruction is enough)
- Documents: "No documents yet. Draft your first SOP." + "Draft SOP"
- Interviews: "No sessions yet. Practice your first visa interview." + "Practice visa"
- Audit: "No audit entries match these filters." + "Clear filters"

### 7.4 Error message register

Pattern: (what failed) + (why, if knowable) + (what to do).

- 400 validation: "Email or password is incorrect."
- 402 plan-required: backend `detail.message` verbatim.
- 404: "We couldn't find that page."
- 429: "Too many attempts. Try again in {n} seconds."
- 451 consent: "Please re-read the latest Privacy Notice and agree to continue."
- 500: "Something went wrong on our side. We've logged it. Try again, or email support."
- Network: "Couldn't reach AidwiseAI. Check your connection."

### 7.5 Banned phrase ledger

`Unlock`, `Unleash`, `Magic`, `Magical`, `AI is thinking`, `AI is generating`, `Powered by AI`, `Revolutionary`, `Game-changing`, `Seamlessly`, `Leverage`, `Synergize`, `Next-generation`, `World-class`, `Cutting-edge`, `Reimagined`, `Reinvented`, `Smart` (adjective for software), `Effortless`, `Just a moment`, `Hang tight`, `Almost there`, `Hold tight`, `Awesome`, `Oopsy`, `Whoops`, `Uh-oh`, `Naughty`, `Lost in space`.

Verification command: `grep -iE "unlock|magic|powered by AI|seamlessly|leverage|synergize|game-changing|world-class|cutting-edge|reimagined|effortless" Front-upgrade.md` should return only this charter section's lines (which name and ban them).

---

## §8 Motion Spec

### 8.1 Tokens

```
--motion-micro:   90ms  linear
--motion-enter:   180ms cubic-bezier(0.22, 1, 0.36, 1)
--motion-exit:    140ms cubic-bezier(0.32, 0, 0.67, 0)
--motion-layout:  220ms cubic-bezier(0.22, 1, 0.36, 1)
```

### 8.2 Per-interaction durations

| Interaction              | Token             |
|--------------------------|-------------------|
| Hover color/opacity      | micro             |
| Button press             | micro             |
| Toast enter              | enter             |
| Toast exit               | exit              |
| Modal scrim              | enter             |
| Modal scale-in           | enter             |
| Tab indicator slide      | layout            |
| Kanban card move         | layout            |
| Accordion expand         | layout            |
| List row insert          | enter (+ layout)  |
| List row remove          | exit (+ layout)   |
| Drawer slide-in          | layout            |
| Page transition (route)  | (none; instant)   |

### 8.3 Reduced motion

`@media (prefers-reduced-motion: reduce)` collapses every duration > 120ms to opacity-only crossfade at 100ms. Layout reorder becomes instant. Slide / scale animations become fade-only.

### 8.4 Animation discipline

- Animate only `opacity` and `transform`. Never `width`, `height`, `top`, `left`, `margin`, `padding`, `box-shadow` color.
- A single screen renders at most 1 background-running animation (e.g. trial banner color pulse). No persistent motion otherwise.
- Numeric counters tween 220ms ease-out on real value change. Skip tween if delta >50% (jump cut feels more honest).

---

## §9 Accessibility Spec

### 9.1 Floor (all surfaces inherit)

- WCAG 2.2 AA contrast: ≥4.5:1 body, ≥3:1 ≥24px.
- All interactive elements ≥44×44.
- Focus visible 2px ring, never coloured by component.
- Tab order = DOM order = visual order.
- All form inputs have `<label for>` (never placeholder-as-label).
- All icon-only buttons have `aria-label`.
- All async status changes announce via `role="status"` polite, or `role="alert"` for errors.
- All images have `alt`; decorative `alt=""`.
- Color is never the only signal.

### 9.2 Per-surface audit grid

| Screen                            | Has H1 | Tab order | Focus trap (modal) | Color-not-only | Live region |
|-----------------------------------|--------|-----------|--------------------|----------------|-------------|
| /                                 | Y      | Y         | n/a                | Y              | n/a         |
| /booth/air-university             | Y      | Y         | n/a                | Y              | Y           |
| /upgrade                          | Y      | Y         | n/a                | Y              | Y (status)  |
| /legal/[slug]                     | Y      | Y         | n/a                | Y              | Y (status)  |
| /signup                           | Y      | Y         | n/a                | Y              | Y (alert)   |
| /login                            | Y      | Y         | n/a                | Y              | Y (alert)   |
| /onboarding                       | Y      | Y         | n/a                | Y              | Y (status)  |
| /feed                             | Y      | Y         | n/a                | Y              | Y (status)  |
| /discover                         | Y      | Y         | n/a                | Y              | n/a         |
| /scholarships/[id]                | Y      | Y         | n/a                | Y              | Y (status)  |
| /saved                            | Y      | Y         | n/a                | Y              | Y (status)  |
| /dashboard/scholarships/match     | Y      | Y         | n/a                | Y              | Y (status)  |
| /tracker                          | Y      | Y         | Y (drawer)         | Y              | Y (status)  |
| /documents                        | Y      | Y         | n/a                | Y              | n/a         |
| /documents/[id]                   | Y      | Y         | n/a                | Y              | Y (status)  |
| /documents/sop                    | Y      | Y         | n/a                | Y              | Y (status)  |
| /documents/professor-email        | Y      | Y         | n/a                | Y              | Y (status)  |
| /interviews                       | Y      | Y         | n/a                | Y              | n/a         |
| /interviews/[id]                  | Y      | Y         | n/a                | Y              | Y (status)  |
| /interviews/visa                  | Y      | Y         | n/a                | Y              | Y (status)  |
| /profile                          | Y      | Y         | n/a                | Y              | Y (status)  |
| /settings                         | Y      | Y         | Y (typed-confirm)  | Y              | Y (status)  |
| /admin/*                          | Y      | Y         | Y (dialogs)        | Y              | Y (status)  |
| /mentor/*                         | Y      | Y         | n/a                | Y              | Y (status)  |
| /partners/*                       | Y      | Y         | n/a                | Y              | n/a         |
| 404/500/offline/denied/maintenance| Y      | Y         | n/a                | Y              | n/a         |

### 9.3 Screen reader contract

- Route changes announce new page title via `<title>` update.
- Optimistic mutations announce success ("Added to Wishlist") and rollback ("Couldn't move card — restored").
- Long-running operations announce start ("Generating SOP") and completion ("SOP ready").
- Locked content announces "Locked — Pro required".

---

## §10 Performance Budgets

### 10.1 Hard ceilings

| Metric                          | Budget                                    |
|---------------------------------|-------------------------------------------|
| Largest Contentful Paint (LCP)  | < 1.8s on /feed at p75 4G                 |
| Interaction to Next Paint (INP) | < 200ms p75 across all surfaces           |
| Initial JS bundle (gzipped)     | ≤ 180 KB                                  |
| Per-route JS (gzipped)          | ≤ 60 KB                                   |
| Image weight per page           | ≤ 240 KB total above the fold             |
| Web font weight                 | ≤ 80 KB total (3 families subset Latin + Latin-ext) |
| Time to Interactive (TTI)       | < 3s on /feed at p75 4G                   |
| Cumulative Layout Shift (CLS)   | < 0.05 on every page                      |

### 10.2 Tactics

- SSR / SSG marketing pages. Hydration partial where possible.
- `next/font` for Fraunces, Inter, JetBrains Mono — subset Latin + Latin-ext, weights 400/500/600.
- Images via `next/image` with explicit width/height. WebP + AVIF.
- Above-the-fold images `priority`. Below-the-fold `loading="lazy"`.
- Skeleton screens, not spinners, on first paint.
- Code-split heavy admin charts (Recharts) — load only on chart pages.
- React Query: 30s default stale, no retry on 4xx, optimistic for mutations.

### 10.3 Anti-pattern enforcement

- No client-side framework on marketing pages beyond minimal interactivity.
- No third-party analytics that block first paint.
- No CSS-in-JS runtime (Tailwind 4 atomic CSS only).
- No icon font (SVG only).
- No video autoplay above the fold.

---

## §11 Self-Review Checklist (delivery gate)

A frontend engineer reviewing their own PR runs this checklist before requesting review.

### 11.1 Voice & Copy
- [ ] Zero banned phrases (`grep -iE` against §7.5 ledger returns no hits).
- [ ] Every CTA uses a verb from §7.2 allowed list.
- [ ] Every empty state matches §7.3 register (reason + next action).
- [ ] Every error matches §7.4 pattern.
- [ ] Brand is exactly "AidwiseAI" everywhere user-facing.

### 11.2 Tokens
- [ ] No raw hex colors in component code — only `var(--token)`.
- [ ] No `#F7F5F0` leftovers from prior spec.
- [ ] All radii match §2.3 scale.
- [ ] All shadows from §2.3 (hairline / lift / raised) — no glow, no coloured shadow.

### 11.3 States coverage
- [ ] Every screen documents empty / loading / loaded / processing / error / success / locked (where applicable).
- [ ] Skeleton renders once per route load (never per item).
- [ ] Optimistic mutations carry rollback toasts.
- [ ] 402 renders UpgradeWall with backend `detail.message`.

### 11.4 Motion
- [ ] All animated properties are `opacity` or `transform`.
- [ ] All durations from §8.1 token table.
- [ ] `prefers-reduced-motion: reduce` collapses non-essential motion.

### 11.5 Accessibility
- [ ] Single H1 per screen.
- [ ] All inputs have `<label for>`.
- [ ] All icon-only buttons have `aria-label`.
- [ ] Tab order matches visual order.
- [ ] Focus ring visible 2px on every interactive.
- [ ] Color is never the only signal.
- [ ] Async status announces via live region.

### 11.6 Anti-slop visuals
- [ ] No emoji in any UI string (`grep -E "[🚀✨🎉🔥⚡👋🎯💪]" frontend/src` returns 0).
- [ ] No gradient mesh / blob background.
- [ ] No sparkle / glow / neon.
- [ ] No marquee / auto-carousel.
- [ ] No bouncy hover, no scale-up that shifts layout.

### 11.7 Performance
- [ ] Initial JS ≤ 180 KB gzipped.
- [ ] LCP < 1.8s on /feed at p75 4G.
- [ ] CLS < 0.05 on the changed route.

### 11.8 Data + RBAC
- [ ] Backend `detail.message` consumed verbatim on 402.
- [ ] Public surfaces return only published scholarships.
- [ ] No B2B leakage into student-facing recommendations (CI trust-boundary test green).
- [ ] PDPB consent captured at signup; version-mismatch flow honoured.

### 11.9 Telemetry
- [ ] All events from per-screen Telemetry sections fire as specified.
- [ ] Event payloads contain only documented fields.

### 11.10 Final sign-off

- [ ] Spec read in full by reviewer (this doc).
- [ ] Each screen in scope of the PR has its §6 entry referenced in the PR description.
- [ ] Self-review run twice: once on desktop, once on mobile.

---

*End of specification. Version v4 — purpose-built rewrite, authored 2026-05-17. Supersedes all prior frontend planning documents. The prior version is retained at `Front-upgrade.legacy.md` for sprint-history reference only.*
