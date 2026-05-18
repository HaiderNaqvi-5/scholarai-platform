# Front-upgrade — AidwiseAI Frontend Design Specification (v3)

> Prototype-ready spec for every screen, component, copy string, and interaction.
> Target user: Pakistani MS / PhD / MBA applicant chasing fully-funded programs abroad.
> Competitor to beat: GoScholar.ai.
> **Public display brand: AidwiseAI.** Internal / repo brand: ScholarAI. Use **AidwiseAI** in all
> user-facing copy, logos, and metadata. (This reconciles `frontend/CLAUDE.md`,
> which is authoritative on brand, against the older `DESIGN_SPEC.md` "rename to ScholarAI" note.)

This document supersedes `DESIGN_SPEC.md`. It is reconciled against the **actual codebase**:
`frontend/src/app/globals.css` tokens, `components/ui/*` primitives, `components/UpgradeWall`,
`components/shell/Sidebar`, the `lib/api/endpoints/*` modules, and the backend `StudentProfile`
contract. Every screen section ends with a **Code map** line: the file that owns it today and
whether the work is *new*, *rewrite*, or *extend*.

---

## Table of Contents

1. [Design System](#1-design-system)
2. [Global Shell & Navigation](#2-global-shell--navigation)
3. [Landing Page](#3-landing-page)
4. [Signup & Login](#4-signup--login)
5. [Onboarding (5 Steps)](#5-onboarding-5-steps)
6. [Dashboard (Home)](#6-dashboard-home)
7. [Scholarship Finder](#7-scholarship-finder)
8. [Application Tracker (Kanban)](#8-application-tracker-kanban)
9. [SOP Builder](#9-sop-builder)
10. [Visa Interview Simulator](#10-visa-interview-simulator)
11. [Upgrade Page](#11-upgrade-page)
12. [Privacy & Consent UI](#12-privacy--consent-ui)
13. [Shared Components](#13-shared-components)
14. [Screen Inventory](#14-screen-inventory)
15. [Key Copy Strings](#15-key-copy-strings)

---

## 1. Design System

The design system is **already implemented** in `frontend/src/app/globals.css` as a Tailwind 4
`@theme` block plus three `@utility` helpers. This section documents the tokens that exist and
flags the two gaps the Pakistan pivot needs.

### 1.1 Color Palette — as defined in `globals.css @theme`

```
-- Backgrounds --
--color-paper:        #F7F5F0   primary background, warm off-white   (also --color-background)
--color-paper-warm:   #F1EDE4   hover states, section fills, chips
--color-paper-dim:    #E7E1D5   dividers, progress-track, skeleton base
--color-paper-white:  #FFFDF9   card + input backgrounds

-- Ink (text) --
--color-ink:          #0C1117   primary text, primary button fill    (also --color-foreground)
--color-ink-strong:   #1B2633   headings, primary button hover
--color-ink-muted:    #334155   body text, secondary text
--color-ink-subtle:   #64748B   labels, captions, placeholders

-- Semantic --
--color-validated:      #426B5A   verified facts, eligibility confirmed, success
--color-validated-soft: #DDE9E2   validated background tint
--color-caution:        #B7791F   warnings, partial eligibility, amber
--color-caution-soft:   #F4E7CF   caution background tint
--color-danger:         #B94A48   errors, red flags, deadlines < 14 days
--color-danger-soft:    #F4D8D6   danger background tint
--color-generated:      #2E5B9A   AI-generated content, links, info
--color-generated-soft: #DCE6F4   generated background tint

-- Borders & Rings --
--color-border:  rgba(12,17,23,0.08)    every card / input / divider border
--color-ring:    rgba(46,91,154,0.32)   focus ring (also :focus-visible uses solid --color-generated)
```

**Gap 1 — no `gold` token.** The Pakistan pivot (Premium / Elite tier, demo banner, pricing
emphasis) needs a gold accent. Add to `@theme`, do **not** invent it inline per-component:

```
--color-gold:      #8B6914   Premium / Elite tier, demo banner, pricing emphasis
--color-gold-soft: #F5EDD6   gold background tint
```

Color discipline (per `impeccable` / `design-taste-frontend`): the palette is **Restrained** —
tinted warm neutrals plus semantic accents used only for meaning. Gold is the one identity accent
and must stay under ~10% of any surface. Never `#000` / `#fff`; the neutrals are already tinted
warm. No purple, no neon, no gradient text.

### 1.2 Typography

```
Display font:  Sora            weights 500 / 600 / 700   (--font-display) — all h1–h4
Body font:     IBM Plex Sans   weights 400 / 500 / 600   (--font-sans, var --font-ui) — body, UI
Mono font:     IBM Plex Mono   weights 400 / 500         (--font-mono) — data, route labels, kbd, step labels

Loaded via next/font in app/layout.tsx. globals.css sets:
  body            -> --font-sans, line-height 1.6, font-feature-settings "ss01" "cv11"
  h1,h2,h3,h4     -> --font-display, letter-spacing -0.01em

Type scale (Tailwind utilities in use across the codebase):
  text-xs    12px    captions, kbd, step eyebrows, badge text
  text-sm    14px    secondary body, helper text, nav items
  text-[15px] 15px   default body / input text (md button, inputs)
  text-base  16px    lead paragraphs
  text-lg    18px    CardTitle, section sub-heads
  text-xl    20px    UpgradeWall headline, question text
  text-3xl   30px    page h1 (onboarding, dashboard)
  text-[44px]/[64px] landing hero (responsive)
```

Hierarchy comes from **scale + weight contrast** (≥1.25 ratio between steps), never from a flat
scale. Body line length capped at 65–75ch.

### 1.3 Spacing & Radius

```
Spacing scale (Tailwind default 4px base): 4 8 12 16 20 24 32 40 48 64 80 96
  Cards pad p-5 (20px). Panels / modals pad p-6–p-8. Page gutters px-5 mobile, px-6 desktop.

Radius (globals.css @theme):
  --radius-sm:    12px   buttons, inputs, chips, small controls, nav items
  --radius-card:  16px   cards (ui/card.tsx uses rounded-[16px])
  --radius-panel: 20px   panels, modals, large cards, UpgradeWall card
  --radius-hero:  24px   hero card, large display surfaces
```

Vary padding for rhythm; do not apply identical padding to every block. Cards are not the default
container — use `border-t` / `divide-y` / negative space to group data unless elevation is
functionally needed. Never nest a card inside a card.

### 1.4 Shadows

```
--shadow-quiet: 0 12px 32px rgba(12,17,23,0.04)   resting cards, dropdowns
--shadow-soft:  0 20px 48px rgba(12,17,23,0.07)   hover cards, modals, active panels
UpgradeWall card uses an inline 0 8px 30px rgba(12,17,23,0.07).
```

Shadows are wide and low-opacity, tinted toward the ink hue. No glows, no hard drop shadows.
(Note: these differ from the old `DESIGN_SPEC.md` shadow values — `globals.css` is authoritative.)

### 1.5 Buttons — `components/ui/button.tsx` (CVA, exists)

```
Component: <Button variant size asChild loading />   — rounded-[12px], tap-target (44x44 min),
           focus-visible:ring-2 ring-[--color-ring], transition-colors 150ms, loading spinner slot.

variant:
  primary    (default)  bg-ink text-paper, hover bg-ink-strong, active bg-ink-strong
  secondary             border + bg-paper-white text-ink, hover bg-paper-warm
  ghost                 transparent text-ink, hover bg-paper-warm
  danger                bg-danger text-paper-white, hover opacity-90
  validated             bg-validated text-paper-white, hover opacity-90

size:
  sm    h-9  (36px)  px-3  text-sm
  md    h-11 (44px)  px-4  text-[15px]   <- default
  lg    h-12 (48px)  px-6  text-base
  icon  size-11 (44x44)
```

**Gap 2 — no `gold` variant.** Pricing / upgrade CTAs need it. Add a `gold` variant
(`bg-gold text-paper-white hover:opacity-90`) rather than hand-rolling gold buttons.
The old spec's "52px hero button" maps to `size="lg"` (48px) — keep `lg`, do not add a 6th size.

### 1.6 Form Inputs — `components/ui/input.tsx`, `ui/label.tsx`

```
Input:  h-11 (44px), bg-paper-white, border 1px --color-border, rounded-[12px], px-3, text-[15px],
        placeholder text-ink-subtle. Focus: ring-2 --color-ring + border-generated.
        Error: border-danger, helper text-danger below. Native <select> shares the same shell.
Label:  Radix Label, sits ABOVE the input, gap-2 between label and control. Helper text-xs
        text-ink-subtle directly under the label; error text-xs text-danger directly under input.
```

Always: label above, helper optional but present in markup, error below. Inputs ≥16px font on
mobile to prevent iOS zoom (the `text-[15px]` is fine on desktop; bump to `text-base` < 768px).

### 1.7 Cards — `components/ui/card.tsx`

```
<Card>            rounded-[16px], border 1px --color-border, bg-paper-white, transition-colors 150ms
<CardHeader>      flex-col gap-1, p-5 pb-3
<CardTitle>       font-display text-lg leading-tight text-ink   (renders <h3>)
<CardDescription> text-sm text-ink-muted
<CardBody>        p-5 pt-2
<CardFooter>      flex items-center gap-2, p-5 pt-3

Interactive card hover: shadow-soft, border-color rgba(12,17,23,0.14), translateY(-1px), 150ms.
Apply hover ONLY to cards that navigate or expand. Static cards stay flat.
```

### 1.8 Badges & Chips — `components/ui/badge.tsx`

```
<Badge tone />   inline-flex, rounded-full, px-2.5 py-1, text-xs font-medium leading-none

tone:
  neutral   (default)  bg-paper-warm   text-ink-muted
  validated            bg-validated-soft  text-validated
  generated            bg-generated-soft  text-generated
  caution              bg-caution-soft    text-caution
  danger               bg-danger-soft     text-danger
  ink                  bg-ink             text-paper
```

**Gap 3 — no `gold` tone.** Add `gold` (`bg-gold-soft text-gold`) for "Most popular", demo, and
Elite-tier badges. Selectable chips (onboarding fields, finder filters) are a separate pattern:
`h-10 rounded-full px-4`, active `bg-ink text-paper`, inactive `border + bg-paper-white`.

### 1.9 Left-Border Stripes — `globals.css @utility` (exists, project-mandated)

```
.validated-stripe  border-left: 3px solid var(--color-validated)
.generated-stripe  border-left: 3px solid var(--color-generated)
.caution-stripe    border-left: 3px solid var(--color-caution)
```

These distinguish **validated facts** from **AI-generated content** and are a **PR-blocking
requirement** in `frontend/CLAUDE.md` (design rule 1). They are a deliberate, semantic exception
to the general "no side-stripe borders" guidance: paired with a full border + background tint,
they carry meaning, not decoration. Usage:
- `validated-stripe` + `validated-soft` bg + "Verified" badge + source link — for scholarship
  facts (deadlines, amounts, eligibility).
- `generated-stripe` + `generated-soft` bg + 14px Lucide `Sparkles` + one-line provenance — for
  AI output (SOP draft, match reasons, interview feedback).
- `caution-stripe` + `caution-soft` bg — for warnings (missing field, near deadline, AI disclaimer).
Never mix validated and generated inside one paragraph.

### 1.10 Icons — Lucide only

Lucide React SVG icons exclusively. **No emoji as UI chrome** (PR-blocking). Emoji is permitted
only inside *content* — country flags that arrive in scholarship data. Sizes: 16px inline, 18px
nav, 20px buttons, 24px section headers. `strokeWidth` standardized at 1.75 (nav) / 2 (actions).

Key icons in use: `Search` `GraduationCap` `Compass` `Bookmark` `FileText` `Mic` `MapPin`
`Calendar` `CheckCircle` `Check` `AlertTriangle` `Lock` `Sparkles` `Trophy` `ArrowRight`
`ChevronRight` `X` `Plus` `GripVertical` `LayoutDashboard` `Star` `User` `Settings` `LogOut`
`ClipboardCheck` `GaugeCircle` `Database` `ListChecks` `Users` `ScrollText`.

### 1.11 Motion

Micro-interactions 150–300ms, ease-out (cubic-bezier(0.16,1,0.3,1)). Animate only `transform`
and `opacity` — never layout properties. No bounce, no elastic. Onboarding step changes and
feedback-panel reveals use a slide via `transform: translateX`. `prefers-reduced-motion` is
respected globally in `globals.css` (durations forced to 0.01ms) — every animation must degrade
to an instant state. No streaming-text theatre on REST data.

---

## 2. Global Shell & Navigation

### 2.1 AppShell — `components/shell/AppShell.tsx`

```
+--------------------------------------------------------+
| TopBar  (h-16 / 64px, sticky, bg-paper-white,          |
|          border-b 1px --color-border)                  |
+----------+---------------------------------------------+
| Sidebar  |  Main content area                          |
| (w-60 /  |  bg-paper, px-6 py-8 desktop / px-4 py-6     |
|  240px,  |  mobile. max-w content column ~960px,        |
|  sticky, |  centered, varies per route.                 |
|  md+)    |                                             |
+----------+---------------------------------------------+

Mobile (< 768px / md):
  Sidebar hidden (it is md:flex). Replaced by bottom tab bar (section 2.4).
  TopBar shows a hamburger -> full-screen overlay nav.
  Main content px-4 py-6.
```

### 2.2 Sidebar — `components/shell/Sidebar.tsx` *(rewrite — renamed Pakistan nav + 3 new items)*

Current sidebar code hardcodes the previous brand string — rename it to **AidwiseAI**. Current sections are generic
("Apply / For you / Discover / Saved", "Prepare / Documents / Interviews"). The pivot relabels
them and adds the three new student destinations.

```
Header:   AidwiseAI   (font-display text-lg tracking-tight text-ink, links to /feed)

EXPLORE                              showFor: student
  [Home]            My Matches        -> /feed                       (G F)
  [Search]          Find Scholarships -> /dashboard/scholarships/match
  [Compass]         Browse All        -> /discover                   (G D)
  [Bookmark]        Saved             -> /saved                      (G S)

APPLY                                showFor: student
  [LayoutDashboard] Tracker           -> /dashboard/tracker
  [FileText]        SOP Builder        -> /dashboard/documents/sop
  [Mic]             Visa Practice      -> /dashboard/interview

ACCOUNT                              showFor: student
  [User]            Profile            -> /profile
  [Settings]        Settings           -> /settings

UPGRADE  (only when user.plan is free or pro)
  [Star]            Go Elite           -> /upgrade        (text-gold, bg-gold-soft on active)

MENTOR    showFor: mentor   -> /mentor/queue (Review queue)
ADMIN     showFor: admin    -> Overview / Ingestion / Curation / Rec eval / Users / Audit
```

States (unchanged mechanics): active `bg-paper-warm text-ink`; hover `bg-paper-warm text-ink`;
default `text-ink-muted`. Each item `rounded-[12px] px-3 py-2 text-sm`, 18px icon strokeWidth
1.75, optional `kbd` shortcut shown on hover. Keep the existing `hasRole(user, section.showFor)`
filter and `usePathname` active logic.

Sidebar footer *(new)*: avatar initials (32px) + name + email (text-xs ink-subtle), and a ghost
"Sign out" button that turns danger-toned on hover.

**Code map:** `components/shell/Sidebar.tsx` — rewrite (section labels, 3 new links, Upgrade
group, footer). `AGENTS.md` note: read `node_modules/next/dist/docs/` before route work.

### 2.3 TopBar — `components/shell/TopBar.tsx` *(extend)*

```
Left:    Search trigger — pill, h-9, bg-paper-warm, border 1px, 320px wide on desktop.
         "Search scholarships..."  +  kbd "/"  hint.  Press / focuses it anywhere (rule 6).
Center:  empty on student; page title on admin.
Right:   [Bell] (admin only, alert badge)  [Avatar 32px initials]  Name  v  -> dropdown
Dropdown: Name / email -- Profile / Settings -- Sign out.
```

### 2.4 Mobile Bottom Tab Bar *(new)*

```
[Home] My Matches   [Search] Find   [LayoutDashboard] Tracker   [Mic] Visa   [User] Profile

h-15 (60px), bg-paper-white, border-t 1px --color-border, iOS safe-area padding-bottom.
Active tab: text-ink + 2px top border-ink. Inactive: text-ink-subtle. Each tab >=44x44.
```

### 2.5 Demo Mode Banner *(new)*

Shown when `user.plan === 'elite'` and the account is the seeded demo persona. Sticky directly
below TopBar, dismissible (dismissal persisted to `localStorage` key
`grantpath.demo_banner_dismissed`).

```
+---------------------------------------------------------------------+
| [Star]  Demo mode — all Elite features unlocked.                    |
|         In production: Pro PKR 2,499/mo  ·  Elite PKR 7,999/mo  [X]  |
+---------------------------------------------------------------------+
bg-gold-soft, border-b 1px rgba(139,105,20,0.2), text-gold text-sm font-medium, py-2.5 px-6.
[X]: ghost icon button 32x32.
```

**Code map:** `components/shell/TopBar.tsx` extend; new `components/shell/BottomTabs.tsx`,
`components/shell/DemoBanner.tsx`.

---

## 3. Landing Page

**Route:** `/` — `frontend/src/app/page.tsx` *(rewrite)*. Full-width, no sidebar, sections
centered at max-w ~1100px. **Goal:** convert a Pakistani student to signup with one CTA:
"Find My Scholarships →". The page does **not** auto-redirect logged-in users.

Current state: a generic three-pillar landing ("For grad school applicants", "Canada-first")
that hardcodes the previous brand string in code; rename it to AidwiseAI and replace the body below.

### 3.1 Landing Nav

```
+-------------------------------------------------------------------+
| AidwiseAI        How it works   Features   Pricing                |
|                                          [Sign in]  [Find My      |
|                                                      Scholarships]|
+-------------------------------------------------------------------+
bg-paper-white/95 + backdrop-blur, border-b 1px, h-16, sticky.
Logo: font-display weight 700 "AidwiseAI". Nav links text-sm ink-muted hover ink.
Sign in: secondary, size sm. CTA: primary, size sm. Mobile: logo + hamburger overlay.
```

### 3.2 Hero — asymmetric split (text left 55%, preview card right 45%)

Per `impeccable` / `design-taste-frontend`: **no centered hero.** Left-aligned content, right
asset, generous asymmetric whitespace. `min-h` driven by content, not `h-screen`.

```
LEFT (55%)
  Eyebrow badge:  [flag emoji] Built for Pakistani students
                  badge tone=neutral (bg-paper-warm), text-sm
  Headline (font-display, ~44px mobile / ~56px desktop, weight 700, leading-[1.1]):
    "Find fully-funded programs abroad.
     No consultant. No fees."
  Subheadline (text-lg ink-muted, max-w ~440px):
    "AidwiseAI matches Pakistani students to scholarships they actually qualify for,
     based on CGPA, IELTS, field, and target country. Then helps them apply."
  Speed promise (text-sm ink-subtle, mt-2):
    "Get your matches in under 60 seconds."
  CTA group (mt-8, gap-3):
    [Find My Scholarships ->]   Button size lg (primary)
    Already have an account? Sign in   (text-sm link, ink-subtle)
  Social proof strip (mt-10, flex gap-6, text-sm):
    [CheckCircle validated] Free forever, no consultant fees
    [CheckCircle validated] Chevening, Fulbright, DAAD and more
    [CheckCircle validated] Visa interview prep included

RIGHT (45%) — static "Your AI Match Results" preview card (no JS, loads instantly):
  Card: bg-paper-white, border 1px, rounded-[24px], p-6, shadow-soft, max-w ~400px.
  Header row: "Your AI Match Results"  +  "3 of 12 ->"
  3 result rows (bg-paper rounded-[12px] p-3.5):
    [flag] Chevening Scholarship   UK · Fully Funded · Nov 2025      96% match (validated, right)
           [Check validated] CGPA 3.7 qualifies  [Check] IELTS 7.0 meets requirement
    [flag] Fulbright Fellowship    USA · Fully Funded · Feb 2026     91% match
    [flag] DAAD Scholarship        Germany · Fully Funded           87% match
  Lock row (bg-paper-warm, border 1px dashed):
    [Lock] + 9 more matches, 2 closing in 47 days   [Unlock with Pro ->] (gold button, sm)
  Footnote: "Profile: NUST · CS · CGPA 3.7 · IELTS 7.0"  (text-xs ink-subtle)

Mobile (< 640px): single column, preview card hidden, CTA full-width.
```

### 3.3 Stats Bar — full-width, `bg-ink`, py-15

```
   150,000+                62%                    0
   Pakistani students      want to study abroad   dedicated AI platforms
   studying abroad                                for Pakistani students (until now)

3-col grid, centered. Numbers: font-display ~48px weight 700, color paper-white.
Labels: text-sm rgba(255,255,255,0.6), max-w ~160px. 1px rgba(255,255,255,0.1) dividers.
```

### 3.4 Problem Section — 2x2 grid (not a 3-card row)

Heading: "The study abroad process is broken for Pakistani students".
Sub: "Every year, talented students miss life-changing opportunities for the same four reasons."

```
Card 1  Too expensive        Consultants charge PKR 40,000–150,000+. Most give generic
                             advice. One wrong decision costs months.
Card 2  Information chaos     WhatsApp groups, random YouTube videos, outdated blogs.
                             No single source of truth for Pakistani applicants.
Card 3  Visa rejection fear   Pakistan has some of the world's highest student visa refusal
                             rates, yet no platform helps you prepare.
Card 4  Currency reality      With 1 USD = 278+ PKR, every wrong application fee, wrong
                             consultant, and wasted test attempt is expensive.

Card: bg-paper-white, border 1px, rounded-[16px], p-7. Icon 32px in caution-soft tile
(rounded-[12px]). Heading text-base weight 600. Body text-sm ink-muted.
```

### 3.5 How It Works — 4 horizontal steps (vertical on mobile)

Heading: "From profile to visa approval. One platform, every step."

```
01 Build your profile   02 Get matched         03 Track & apply        04 Ace the visa
Fill CGPA, IELTS,       AI matches you to      Kanban board tracks     Practice UK, USA,
target countries,       scholarships you       every application,      Canada, Germany
and field. Under        actually qualify       Pakistan-specific       visa interviews with
3 minutes.              for.                   checklist included.     AI feedback.
[User]   -> LIVE        [GraduationCap] LIVE   [LayoutDashboard] LIVE  [Mic]   -> LIVE

Step number: font-display "01"–"04" in ink-subtle. Dashed 1px connectors between steps.
"LIVE" badge: tone=validated, text-xs.
```

### 3.6 Featured Scholarships — horizontal-scroll card row

Heading: "Top scholarships Pakistani students win".
Sub: "Fully funded. Real deadlines. Open to you."

```
5 fixed-width cards (w-[220px]), horizontal scroll on mobile:
  Chevening (UK) · Fulbright (USA) · DAAD (Germany) · Commonwealth (UK) · HEC Overseas (global)

Card: bg-paper-white, border 1px, rounded-[16px], p-6. Flag emoji 32px. Name text-[15px]
weight 600. "FULLY FUNDED" badge tone=validated. Amount text-sm ink-muted. Deadline label
text-xs ink-subtle / value text-sm (caution if < 60 days). "Min CGPA" text-xs. "Open to PK"
badge tone=validated. [View Details] ghost link, text-sm, generated color.
```

### 3.7 Visa Interview Callout — full-width, `bg-generated-soft`

```
[Mic 40px generated]
"Practice your visa interview before the real one."   font-display ~28px weight 700
"GoScholar lists visa prep as Coming Soon. We built it. UK, USA, Canada, Germany.
 AI feedback on every answer. Red-flag detection. Session summary."   text-[15px] ink-muted, max-w ~540px
[Practice a Visa Interview, Free ->]   Button size lg (primary)
border-y 1px rgba(46,91,154,0.15), content centered.
```

### 3.8 Pricing Teaser — 3-column card row

Heading: "Free to start. Upgrade when you're ready."

```
Explorer (Free)  |  Pro (PKR 2,499/mo)  |  Elite (PKR 7,999/mo)
Pro card highlighted: gold ring + "Most popular" badge (tone=gold).
Under Pro:   "Less than one hour of a consultant's time per month."
Under Elite: "For Pakistani families in the UK or UAE."
[See full pricing ->]  link -> /upgrade
```

### 3.9 Footer — `bg-ink`

```
AidwiseAI
Making study abroad accessible for Pakistani students.
Student-only, we don't take money from universities.

Product            Resources           Company
Find Scholarships  Scholarship Guide   About
Visa Practice      IELTS Tips          Contact
SOP Builder        CGPA Converter      Privacy Policy
Tracker            Test Prep           Terms of Service

-----------------------------------------------------------
Are you a university or school? Partner with us ->  (mailto:partnerships@aidwiseai.pk, text-gold)
(c) 2026 AidwiseAI. All rights reserved.

All text rgba(255,255,255,0.6); logo + name white; column headings rgba(255,255,255,0.4)
text-xs uppercase tracking-[0.1em]; links hover rgba(255,255,255,0.9).
```

**Code map:** `frontend/src/app/page.tsx` — rewrite. New section components live alongside in
`app/(marketing)/_components/` or `components/landing/`. LCP < 1.8s: CSS gradient + SVG only,
no hero raster image. CTA routes to `/signup` when logged out, `/feed` when logged in.

---

## 4. Signup & Login

Both pages **exist and work** (`app/signup/page.tsx`, `app/login/page.tsx`). The pivot is a
visual pass plus copy alignment, not a rebuild.

### 4.1 Signup — `/signup` *(extend)*

Centered card, max-w ~420px, vertically centered, page bg-paper.

```
Card: bg-paper-white, border 1px, rounded-[20px], p-10, shadow-soft.
  [AidwiseAI logo mark]   centered
  "Create your account"           font-display text-2xl weight 700
  "Find fully-funded programs that match your profile."   text-sm ink-muted

  Full name   Input, placeholder "Zara Khan"
  Email       Input, placeholder "zara@example.com", error "Enter a valid email address."
  Password    Input type=password, placeholder "Min. 12 characters",
              helper "At least 12 characters" (text-xs ink-subtle),
              eye / eye-off visibility toggle.
              NOTE: backend Pydantic requires >= 12 chars. Helper + client check must say 12.
  [Create account ->]   Button primary, full-width, size lg

  -------- or --------
  [Google icon] Sign up with Google   secondary, full-width, size md
              (placeholder, "Coming soon" tooltip on hover)

  "Already have an account? Sign in ->"   text-sm centered link -> /login
  Legal: "By creating an account, you agree to our Terms of Service and Privacy Policy."
         text-xs ink-subtle, max-w ~300px.
```

On success: route to `/onboarding`.

### 4.2 Login — `/login` *(extend)*

Same card shell. "Welcome back" / "Sign in to your AidwiseAI account."

```
  Email      Input
  Password   Input type=password; row: "Password" label left, "Forgot password?" link right
  [Sign in ->]   Button primary, full-width, size lg
  Error (below button): caution/danger-soft block, "Invalid email or password. Try again."
  Demo-fill buttons (keep existing): [Student demo] [Admin demo] — prefill the seeded creds.
  "Don't have an account? Sign up ->"  -> /signup
```

Demo creds (seeded): `student@example.com` / `strongpass1`, `admin@example.com` / `strongpass1`,
and the Pakistan persona `zara.khan@example.com` / `ScholarAI-Demo-2026!` (plan=elite).
On success: route to `?next=` param or `/feed`.

**Code map:** `app/signup/page.tsx`, `app/login/page.tsx` — extend (visual + 12-char copy).

---

## 5. Onboarding (5 Steps)

**Route:** `/onboarding` — `app/onboarding/page.tsx` *(rewrite — 4 generic steps → 5 Pakistan steps)*.
Centered card, max-w ~600px, no sidebar. **Goal:** a Pakistan-specific profile in under 3 minutes.

Current state: a 4-step generic wizard (`["You","Academic","Citizenship & language","Goal"]`),
draft autosaved to `localStorage` key `grantpath.onboarding_draft` (debounced 200ms), submitting
to `endpoints.profile.upsert`. The rewrite keeps the autosave mechanism, the `localStorage` key,
the `Field` / `Chip` / `ProgressDots` helpers, and the `profile.upsert` call shape — it extends
the field set and step count.

### 5.1 Backend contract — `StudentProfile` (authoritative, `extra="forbid"`)

Every field below must map to a real `StudentProfile` column. The Pydantic schema **forbids
extra keys**, so the form may not invent `full_name`, `field_tags[]`, or `language_scores[]`.
Known canonical fields (from root `CLAUDE.md`):

```
citizenship_country_code   gpa_value          gpa_scale            target_field (single string)
target_degree_level        target_country_code  language_test_type   language_test_score
target_countries[]         city_of_origin     intake_target        funding_requirement
hec_degree_level           research_publication_count  has_research_publications  degree_subject
```

`full_name` is read from / written to the `User`, not the profile. Before building, confirm the
exact column set against `backend/app/schemas` and `lib/api/types.ts` (hand-synced mirror).
Pakistan-only fields that have **no column** must not be collected (PDPB: no religion / politics
/ biometric — by design).

### 5.2 Progress bar (persistent across steps)

```
TOP OF PAGE (outside card):
  "Step 1 of 5 — About You"                          "~3 min left"  (text-xs ink-subtle, right)
  ProgressDots: 5 dots, active = wide ink pill, done = ink-muted, future = paper-dim
  (reuse the existing ProgressDots helper; extend count 4 -> 5)
```

### 5.3 Card wrapper (all steps)

```
Card: bg-paper-white, border 1px, rounded-[20px], p-10, shadow-soft, max-w ~600px.
  Step eyebrow: "STEP 1 OF 5"  font-mono text-xs uppercase tracking-[0.16em] ink-subtle
  Step title:   font-display text-3xl ink
  Step description: text-[15px] ink-muted, max-w ~440px
  "Draft saved" indicator top-right, text-xs ink-subtle, appears ~2s after a field change.
Footer: [<- Back] ghost (hidden/disabled on Step 1)        [Continue ->] primary
  Continue is always enabled except where a required field is missing (Step 4 only).
  Step 5 Continue label becomes "Find My Scholarships ->".
Step transitions slide via translateX; respects prefers-reduced-motion.
```

### 5.4 Step 1 — About You

"Tell us about yourself" / "We'll use this to personalise your scholarship matches."

```
1. Full name *           Input "Zara Khan"  (writes to User.full_name) — required
2. City of origin        Select: Karachi, Lahore, Islamabad, Rawalpindi, Faisalabad, Peshawar,
                         Quetta, Multan, Sialkot, Hyderabad, Other  -> city_of_origin
3. Pakistani university  Searchable dropdown, 25 pre-loaded: NUST, LUMS, FAST-NUCES, UET Lahore,
                         IBA Karachi, QAU, COMSATS, UCP, NED, UMT, BNU, Air University, GIKI,
                         PIEAS, FCCU, University of Karachi, University of the Punjab, SZABIST,
                         ... + "Other" (free text). Stored on the profile's university field.
4. Degree subject        Input free text "e.g. Computer Science, Electrical Engineering"
                         helper "Your undergraduate major"  -> degree_subject
5. Graduation year       Select 2018..2025 (expected)
```

### 5.5 Step 2 — Academic Record

"Your academic record" / "We check this against scholarship requirements."

```
1. CGPA          two inline controls:  [number 0.0–4.0]  out of  [select scale]
                 scale options: 4.0 (Standard) | 4.0 HEC | 5.0 | 10.0 | 100   -> gpa_value, gpa_scale
                 LIVE CONVERSION (validated-stripe, appears ~300ms debounced after input):
                   [Check] "Your 3.7 CGPA is approximately a 3.7 US GPA."
                           "Equivalent to First Class Honours (UK)."
                 (uses backend utils/cgpa_converter.py logic, surfaced via API or mirrored constants)
2. HEC degree level   radio cards (horizontal): Bachelor's (BS/BE) | Master's (MS/MBA) | MPhil
                      -> hec_degree_level. Default Bachelor's.
3. Research publications   toggle "I have research publications" (off default).
                           ON -> number input "How many peer-reviewed publications?"
                           -> research_publication_count; has_research_publications auto-derives.
```

### 5.6 Step 3 — Test Scores

"Test scores" / "All optional. Add what you have, skip what you don't."

```
1. IELTS Overall   number 0.0–9.0 step 0.5, helper "Leave blank if not taken yet"
                   on fill -> validated-stripe: "7.0 meets the requirement for most UK / Germany /
                   Canada scholarships in our database."
2. TOEFL iBT       number 0–120, helper "Leave blank if not taken yet"
3. GRE             GRE Quant (130–170), GRE Verbal (130–170)
4. GRE waiver      toggle "I need programs that don't require GRE"; ON shows note
                   "We'll filter out GRE-required programs in your matches."
language_test_type / language_test_score carry whichever English test the student reports.
Skip hint: "Not sure about your scores? Update these later from your Profile."
```

### 5.7 Step 4 — Your Goal *(only step with required gates)*

"What's your goal?" / "This is what we rank scholarships against."

```
1. Target degree *      radio cards: MS (Masters) | PhD (Doctorate) | MBA (Business)
                        -> target_degree_level. Required.
2. Target countries *   large flag cards, 4/row desktop / 2/row mobile, multi-select:
                        UK · USA · Canada · Germany · Australia · Ireland · Netherlands
                        -> target_countries[] (and target_country_code = first selected, for the
                        legacy single-value column). Selected: bg-ink/20, 2px ink border, check
                        overlay. Validation: "Select at least one country to continue."
3. Target field(s)      multi-select chips: Computer Science, AI/ML, Data Science / Analytics,
                        Electrical Eng., Business, Engineering, Medicine, Other.
                        -> target_field (joined string, matching current upsert behaviour).
4. Funding requirement  radio cards: Fully funded only | Partial funding OK  -> funding_requirement
5. Target intake        select: Jan 2025, Sep 2025, Jan 2026, Sep 2026, Flexible -> intake_target
Continue disabled until target_degree set AND >=1 target country selected.
```

### 5.8 Step 5 — Financial Context

"A few quick questions" / "This helps us surface relevant support options. All optional."

```
3 toggle rows (full-width, bg-paper-white, border 1px, rounded-[12px], p-4):
  1. "Can you afford application fees?"   sub "Most universities charge $50–150 per application."
  2. "Does your family have savings for a bank statement?"
                                          sub "Required for UK / USA / Canada visa applications."
  3. "Do you need a GRE fee waiver?"      sub "Some universities offer waivers on request."
Toggle: right-aligned 44x24 pill switch. Label text-[15px] weight 500; sub text-sm ink-subtle.
"Skip this step ->" ghost button in the footer. Bottom note: "You can update any of these later
from your Profile." CTA: "Find My Scholarships ->" (Button size lg, full-width).
```

On submit: call `endpoints.profile.upsert(...)`, clear `grantpath.onboarding_draft`, toast
"Profile saved.", `router.replace("/feed")` — mirrors the current submit flow.

**Code map:** `app/onboarding/page.tsx` — rewrite. Keep `STORAGE_KEY`, autosave effect, `Field` /
`Chip` / `ProgressDots`. Extend `Draft` type + `STEPS` to 5. New: searchable university combobox
(`components/ui/combobox.tsx`), flag-card multi-select, CGPA live-conversion call.

---

## 6. Dashboard (Home)

**Route:** `/feed` — `app/(student)/feed/page.tsx` *(extend)*. Role: student. Currently a
recommendations list (`POST /recommendations`, `RecommendationCard`, optimistic save). The pivot
makes it **feature-forward**: an action grid first, recommendations demoted to a secondary block.

### 6.1 Page header

```
"Hi, Zara."                                       font-display text-3xl weight 700
"You have 3 deadlines in the next 60 days."        text-base ink-muted
```

### 6.2 Action Grid — primary UI, 2x2

```
+-----------------------------+  +-----------------------------+
| [GraduationCap]             |  | [Mic]                       |
| Find Scholarships           |  | Practice Visa Interview     |
| Get matched to programmes   |  | UK, USA, Canada, Germany.   |
| you actually qualify for.   |  | AI feedback on every answer.|
|                  [ArrowRight]| |                  [ArrowRight]|
+-----------------------------+  +-----------------------------+
+-----------------------------+  +-----------------------------+
| [FileText]                  |  | [LayoutDashboard]           |
| Write Your SOP              |  | Application Tracker         |
| AI-assisted, Pakistani      |  | Track deadlines and         |
| context, Chevening-ready.   |  | document checklists.        |
|                  [ArrowRight]| |                  [ArrowRight]|
+-----------------------------+  +-----------------------------+

Card: bg-paper-white, border 1px, rounded-[16px], p-6, min-h ~160px. Hover: shadow-soft,
translateY(-2px), 150ms. Icon 24px in paper-warm tile (rounded-[12px], p-2.5). Title text-base
weight 600 mt-3. Description text-sm ink-muted. ArrowRight 18px ink-subtle, bottom-right.
Routes: -> /dashboard/scholarships/match · /dashboard/interview · /dashboard/documents/sop ·
/dashboard/tracker.  Mobile: 1 column.
```

### 6.3 Incomplete Profile Nudge

Shown only when the profile is missing `target_countries` or `gpa_value`. Rendered **above** the
action grid.

```
[AlertTriangle caution]  Complete your profile to get accurate matches
"You're missing IELTS score and target countries."        [Complete profile ->]
bg-caution-soft, border 1px rgba(183,121,31,0.2), rounded-[12px], p-4, text-caution.
```

### 6.4 Recent Matches — secondary block

"Your top matches" (text-lg weight 600). Top 3 from `POST /recommendations` rendered as compact
cards (section 13.2). Below: "See all matches ->" link to `/dashboard/scholarships/match`.

### 6.5 Tracker Summary Widget

Shown only when the user has tracker items; otherwise an empty-state CTA.

```
"Applications in progress" (text-base weight 600)
Stage strip: Researching (2) | Preparing (1) | Applied (0) | Decision (0)   text-sm ink-muted
Near-deadline rows (deadline <= 30 days), danger-toned:
  [AlertTriangle] Chevening (UK)   deadline in 12 days   3 documents missing   [Go to tracker ->]
Empty state: "No applications tracked yet." + "Add scholarships from your matches to start
tracking deadlines." + [Add from matches ->] -> /dashboard/scholarships/match.
```

**Code map:** `app/(student)/feed/page.tsx` — extend (action grid, nudge, tracker widget;
recommendations move down). Action grid renders instant (static), recommendations stream below.

---

## 7. Scholarship Finder

**Route:** `/dashboard/scholarships/match` — *(new page)*. Uses the **existing**
`endpoints.scholarshipMatch.match()` module. Auto-runs the match on load from the saved profile;
the student does not fill a form.

### 7.1 Page header

```
"Scholarships matched to your profile"        font-display text-2xl weight 700
"Based on: NUST · CS · CGPA 3.7 · IELTS 7.0 · UK, Germany · Fully funded"   text-sm ink-subtle
  [Edit profile] ghost link -> /profile

Summary bar (bg-gold-soft, border 1px rgba(139,105,20,0.2), rounded-[12px], p-4, text-gold):
  "4 fully funded scholarships match your profile. 9 more available with Pro, including 2
   closing in 47 days."                                          [Upgrade to Pro ->] gold btn sm
```

### 7.2 Tabs — `components/ui/tabs.tsx` (Radix, exists)

```
[ Eligible (4) ]  [ Partially Eligible (3) ]  [ Stretch (5) ]
Active: text-ink, 2px border-bottom ink, weight 600. Inactive: text-ink-subtle. Counts inline.
The backend match returns eligible / partial / stretch buckets (PRD §5).
```

### 7.3 Match card (Eligible tab)

```
+---------------------------------------------------------------------+
| [flag] Chevening Scholarship                       [FULLY FUNDED]   |
|        UK Foreign, Commonwealth & Development Office                |
| ------------------------------------------------------------------- |
| [validated-stripe + validated-soft bg]                              |
|   [Check] Your 3.7 CGPA from NUST is approximately a 3.7 US GPA.    |
|           Qualifies for programs requiring min 3.0.                 |
| [Calendar] Deadline in 47 days (Nov 2025)        GBP 18,000 / year  |
| [CheckCircle] IELTS 7.0  [CheckCircle] Min CGPA 3.0  [GraduationCap] Masters |
| Match reason (generated-stripe + Sparkles):                         |
|   "Matches your CGPA, IELTS score, CS focus, and UK target."        |
| ------------------------------------------------------------------- |
| [View Details] secondary sm           [+ Add to Tracker] primary sm |
+---------------------------------------------------------------------+
Card: bg-paper-white, border 1px, rounded-[16px], p-6.
Deadline urgency: > 60d ink-muted · 31–60d caution · <= 30d danger + danger left treatment ·
                  <= 14d danger border + danger-soft card tint.
"+ Add to Tracker": optimistic mutation -> button becomes "[Check] Added" (validated, disabled),
calls endpoints.tracker.add(...). Rollback toast on failure.
```

### 7.4 Partially eligible card

Same shape, **caution-stripe** instead of validated:

```
[caution-stripe + caution-soft bg]
  [AlertTriangle] Missing: IELTS score. Add it to qualify fully.   [Update profile ->]
```

### 7.5 Freemium blur — results 4+ on free tier

Use the **existing** `UpgradeWall` overlay mode (`<UpgradeWall detail={...}>{lockedCard}</UpgradeWall>`).
The component blurs `children` (`blur-sm opacity-50`, `pointer-events-none`) and centers the
`WallCard`. `detail.message` and `detail.price` come verbatim from the backend 402
`PlanRequiredDetail` — never write generic "Upgrade to unlock". Example backend message:
"9 more scholarships match your profile, including 2 fully funded ones closing in 47 days."
`featureName="Scholarship matches"`, `showElite={false}`.

### 7.6 Empty state

"Complete your profile to see matches" + [Complete profile ->] -> `/onboarding`.

**Code map:** new `app/(student)/dashboard/scholarships/match/page.tsx`. Endpoint
`lib/api/endpoints/scholarshipMatch.ts` already exists. New `components/scholarship/MatchCard.tsx`.
Reuse `ui/tabs`, `ui/badge`, `ui/button`, `UpgradeWall`. Add a `gold` button variant + badge tone.

---

## 8. Application Tracker (Kanban)

**Route:** `/dashboard/tracker` — *(new page)*. Uses the **existing** `endpoints.tracker` module
(`list / add / patch stage / patch checklist / remove`; free cap = 3 items, PRD §6).

### 8.1 Page header

```
"Application Tracker"                              font-display text-2xl weight 700
"Track every application. Never miss a deadline."  text-base ink-muted
                                                   [+ Add Application] primary, top-right, Plus icon
```

### 8.2 Deadline alert banner

Shown only when any item has deadline <= 30 days **and** checklist < 100%.

```
[AlertTriangle danger] Chevening deadline in 12 days, 3 documents still missing.
                                                  [Go to card ->]  [X]
bg-danger-soft, border 1px rgba(185,74,72,0.2), rounded-[12px], p-3.5, text-danger.
[Go to card ->] smooth-scrolls + flashes the target card. [X] dismisses for the session.
```

### 8.3 Kanban board — 6 columns

```
1 Researching   2 Preparing Documents   3 Applied   4 Interview / Test   5 Decision   6 Accepted

Column header: bg-paper-warm, rounded-[12px 12px 0 0], p-3, font 13px weight 700 uppercase
  tracking-[0.05em] ink. Count: 20x20 circle, bg-ink text-paper text-xs.
Column body: bg-paper, border 1px, border-top none, rounded-[0 0 12px 12px], p-3, min-h ~400px.
  Column 6 (Accepted) header tinted validated-soft.
Mobile: columns are 280px fixed width, horizontal scroll with momentum.
Empty column: dashed border + "Drag cards here", never blank white.
```

### 8.4 Tracker card

```
+-----------------------------------------------+
| [GripVertical drag handle, visible on hover]  |
| [flag] MS Computer Science                    |
|        University of Manchester               |
| --------------------------------------------- |
| [Calendar] 47 days              [Docs] 5 / 13 |
| [progress bar 5/13 filled]                    |
| [Expand checklist v]                          |
+-----------------------------------------------+
Card: bg-paper-white, border 1px, rounded-[12px], p-4, mb-2, cursor grab.
Left treatment by urgency: <=30d danger · 31–60d caution · >60d none.
University text-sm weight 600. Program text-sm ink-muted. Deadline text-xs (urgency colored).
"X / 13 docs" text-xs: validated if 13/13, caution if < 7, danger if < 3.
Progress bar: h-1, bg-paper-dim, fill validated.
```

### 8.5 Checklist expansion

Clicking the card or "Expand checklist" slides down the document checklist:

```
DOCUMENT CHECKLIST (text-xs uppercase ink-subtle header)
  [ ] Academic Transcripts        [ ] Degree Certificate     [ ] IELTS Certificate
  [ ] GRE Score Report            [ ] SOP (Draft)            [ ] SOP (Final)
  [ ] CV / Resume                 [ ] Letter of Recommendation 1 / 2 / 3
  [ ] Bank Statement (proof of funds)
  [highlighted row, caution-soft bg, rounded-[8px]]
     HEC Degree Attestation  [info]   Required for UK and Germany applications
  [ ] Passport Copy               [ ] Application Fee Paid

Checkbox: Lucide Square / CheckSquare (validated when checked). Checked label: ink-subtle +
strikethrough. [info] tooltip on the HEC row: "Many UK and German universities require HEC
attestation of your degree before processing your application."
Notes textarea (2 rows) below the checklist, autosaves on blur.
Checklist toggles are optimistic; PATCH /tracker/{id}/checklist debounced 500ms.
```

### 8.6 Add Application modal — `components/ui/dialog.tsx` (Radix, exists)

```
Add to tracker                                              [X]
  Program name *        Input
  University name *     Input
  Country               Select (flag + name)
  Application deadline  date input
  Scholarship (optional) searchable, pulls from /scholarships
  [Cancel]                                       [Add to Tracker ->]
Modal: bg-paper-white, rounded-[20px], p-8, max-w ~480px, shadow-soft, backdrop rgba(12,17,23,0.3).
Free tier on the 4th item: the modal is replaced by a standalone <UpgradeWall> with the backend
402 message ("You have 4 upcoming deadlines you're not tracking."), featureName="Application tracker".
```

**Code map:** new `app/(student)/dashboard/tracker/page.tsx`. Endpoint `endpoints/tracker.ts`
exists. New: `components/tracker/TrackerBoard.tsx`, `TrackerCard.tsx`, `ChecklistPanel.tsx`,
`AddApplicationDialog.tsx`. New dep: `@hello-pangea/dnd` (React 19-compatible DnD;
`DragDropContext` -> `Droppable` per column -> `Draggable` per card; PATCH stage on drop).

---

## 9. SOP Builder

**Route:** `/dashboard/documents/sop` — *(new page)*. Uses the **existing**
`endpoints.sopBuilder.draft()` module (free = 1 SOP lifetime, Elite = line-by-line feedback,
PRD §7). The draft persists as a `DocumentRecord`, so it also appears in `/documents`.

### 9.1 Layout

```
Desktop: two-panel split
  +-------------------------------+-------------------------------------+
  | INPUT PANEL (40%)             | PREVIEW PANEL (60%)                 |
  | bg-paper, p-8                 | bg-paper-white, p-8 px-10            |
  | form steps 1–4                | generated SOP draft                 |
  +-------------------------------+-------------------------------------+
  Divider: 1px vertical --color-border.
Mobile: tab switcher [Form] [Preview], content stacked.
```

### 9.2 Input panel

```
"SOP Builder"                                               font-display text-xl weight 700
"AI-assisted. Pakistani context. Built for Chevening, DAAD, and Fulbright."   text-sm ink-muted

Scholarship selector (optional):
  "Targeting a scholarship?"  searchable select; options = tracker items, then DB scholarships.
  Selected -> shows scholarship value tags. Helper: "Selecting a scholarship tailors your SOP
  narrative to its values."

Step progress (inside panel): Academic Background o--o Research & Work o--o Why This Program
  o--o Goals & Pakistan   (current highlighted, done with check)

Step 1 Academic Background (pre-filled from profile):
  University background (pre-filled) · Degree and field (pre-filled) · CGPA (pre-filled) ·
  "Any academic achievements or awards?" textarea, placeholder "Dean's List, gold medal..."
Step 2 Research & Work:
  Research experience (textarea, 4 rows, "Leave blank if none, we'll frame coursework instead.")
  Professional / work experience (textarea, 3 rows, "Include internships, freelance projects.")
Step 3 Why This Program / Country:
  "Why this specific program?" (3 rows) · "Why this country?" (3 rows)
Step 4 Goals & Pakistan Context:
  Career goals (3 rows, helper: "For Chevening / HEC, mention intention to return to Pakistan.")
  Challenges overcome (optional, 2 rows) · Gap or weakness to explain (optional, 2 rows)

Generate button (sticky, bottom of panel): [Generate SOP Draft ->] primary, full-width, size lg.
  Loading: label -> "Writing your SOP...", progress bar with milestone labels
  (Structuring -> Drafting -> Refining -> Done), est. 15–25s. NOT a spinner. Right panel shows
  paragraph-block skeletons during generation.
```

### 9.3 Preview panel

```
Empty (no draft yet):
  [FileText 40px ink-subtle]
  "Your SOP draft will appear here. Fill in the form and click Generate SOP Draft."
  bullets: 600–800 words · 6 structured paragraphs · Pakistani academic context included

After generation:
  Action bar: [Copy to clipboard] [Download .txt] [Regenerate] [<- Edit inputs]  (secondary, sm)
  Word count: "743 words · 6 paragraphs" (text-xs ink-subtle, right)
  Draft body: 6 labeled paragraphs. Label = font-mono text-xs uppercase tracking-[0.1em]
    weight 700 ink-subtle, mt-6 mb-2: OPENING / ACADEMIC BACKGROUND / RESEARCH & EXPERIENCE /
    MOTIVATION FOR THIS PROGRAM / CAREER GOALS / CLOSING.
    Paragraph text: IBM Plex Sans 15px, leading-[1.7]. 1px --color-border divider between.

Elite line-by-line feedback (elite plan only): per-paragraph accordion "[+ Feedback v]":
  validated-stripe  "What works well"     ...
  caution-stripe    "What to improve"     ...
  generated-stripe  "Suggested rewrite"   (+ Sparkles)  ...

Disclaimer (caution-stripe, bottom):
  [AlertTriangle] "This draft is AI-generated from your inputs. Personalise it, admissions
  committees can detect generic AI writing. Add specific details only you know."

Validated facts (when a scholarship is selected, validated-stripe + "Verified source" badge):
  [Check] "Scholarship facts used in this SOP"
  "Chevening requires 2 years of work experience. Deadline: November 5, 2025. Award: GBP 18,000."
```

### 9.4 Freemium gate

Free tier, second generation attempt: standalone `<UpgradeWall>` with the backend 402 message
("Want to adapt this SOP for another university? Pro users generate unlimited SOPs."),
`featureName="SOP Builder"`, `showElite={true}`.

**Code map:** new `app/(student)/dashboard/documents/sop/page.tsx`. Endpoint
`endpoints/sopBuilder.ts` exists. New: `components/sop/SopForm.tsx`, `SopPreview.tsx`,
`SopFeedbackAccordion.tsx`, `GenerationProgress.tsx`. Pre-fill from `endpoints.profile.get()`.

---

## 10. Visa Interview Simulator

**Route:** `/dashboard/interview` — *(new page; the existing generic `interviews/` mock-interview
flow stays separate)*. Uses the **existing** `endpoints.visaInterview` module
(`start / answer / summary`; free cuts at Q3, Elite persists transcript as a `DocumentRecord`,
PRD §8). This is the headline differentiator versus GoScholar.

### 10.1 Setup screen

```
"Visa Interview Practice"                                  font-display text-2xl weight 700
"Practice with an AI visa officer. Get feedback on every answer."   text-base ink-muted

STEP 1 — "Which visa are you practising for?"
  Country flag cards (4 across desktop / 2x2 mobile):
    UK Student Visa (20 questions) · USA F-1 Visa (20) · Canada Study Permit (15) ·
    Germany Student Visa (15)
  Card: bg-paper-white, border 2px, rounded-[16px], p-6, w-[180px], centered. Flag 40px.
  Selected: border-ink, bg-paper-warm, 20px check overlay top-right.

STEP 2 — "How do you want to practise?"
  Two mode cards:
    Study Mode  [BookOpen]  full AI feedback after every answer, red-flag detection,
                            ideal answer shown. Best for preparation.
    Exam Mode   [Clock]     no feedback between questions, timer visible, builds endurance.
                            Best for final practice.
  Selected: border-ink 2px, bg-paper-warm.

CTA: [Start Practice Session ->] primary size lg, disabled until country + mode chosen.
Sub: "10 questions · about 15–20 minutes."
```

### 10.2 Interview screen (Q&A)

```
Single column, max-w ~720px, no sidebar distraction.
Top bar: [<- Exit] ghost left · "Question 3 of 10" centered · "05:42" timer (exam mode, font-mono, right)
Progress bar below top bar: h-1.5, bg-paper-dim, fill ink, 30%.

Question card: bg-paper-white, border 1px, rounded-[20px], p-10.
  Category badge (caution-soft, weight 600 12px): Motivation / Finances / Ties to Pakistan /
    Program Knowledge / Future Plans.
  Question text: font-display text-xl weight 600, leading-[1.4].
  Context hint (study mode only, text-sm ink-subtle): "Visa officers want specific numbers and
    confirmed funding sources. Vague answers raise red flags."

Answer area:
  Textarea, min-h ~160px, 15px, border 1px, rounded-[12px], focus border-generated + ring.
    placeholder "Type your answer as you would speak it. Be natural, not rehearsed."
  Character count "0 / no limit" text-xs ink-subtle, right.
  [Submit Answer ->] primary, full-width, size lg, disabled when empty. Loading label
    "Evaluating your answer..." (button text change, not a spinner).
  [<- Previous question] ghost link (study mode, after Q1 only).
```

### 10.3 Feedback panel (study mode only)

Slides in below the question card after submit.

```
Feedback card: bg-paper-white, border 1px, rounded-[16px], p-7, mt-4.
Score meters (3, side by side / stacked mobile): Clarity / Confidence / Relevance.
  Label text-sm weight 600 ink-muted · bar h-2 bg-paper-dim · score text-sm weight 700 right.
  Fill: 4–5 validated · 3–3.9 caution · 1–2.9 danger.
Red flag alerts (danger-stripe, only if red_flags non-empty):
  [AlertTriangle] "Red flag detected" + explanation.
What you did well (validated-stripe) · What to include next time (caution-stripe) ·
  Strong answer includes (generated-stripe + Sparkles).
CTA: [Next Question ->] primary, full-width. Sub: "Question 4 of 10 · Finances".
```

### 10.4 Freemium gate (free tier, after Q3)

Replaces the feedback panel after question 3 with a standalone `<UpgradeWall>`. The backend
attaches a `partial_summary` to the 402 detail — `UpgradeWall`'s `PartialSummary` already renders
`answered` / `average_score` / `red_flag_count`. `featureName="Visa interview"`, `showElite={true}`.
Backend message example: "You got 2 red flags in 3 answers. Questions 4–10 tell you exactly what to fix."

### 10.5 Session summary screen

```
"Session Complete"                                font-display text-2xl weight 700
"UK Student Visa · Study Mode · 10 questions"      text-sm ink-subtle

Radar chart: 4 axes (Clarity · Confidence · Relevance · Red Flag Avoidance). Use a lightweight
  SVG radar component, NOT Chart.js (180KB route budget). recharts is already a dependency and
  is used by interview/RubricRadar — prefer reusing recharts' Radar over a Chart.js add.
Overall score: "3.8 / 5.0" font-display ~36px weight 700 validated · "Good preparation level".

Areas to improve (3 cards): rank + dimension + score + one-line guidance.
Question-by-question table: #, Question, Clarity, Confidence, Relevance, Red Flags.
  Score cells: validated (4–5) / caution (3–3.9) / danger (< 3). Red flag = danger badge w/ count.
Actions: [Practice Again] secondary · [Download Summary] secondary (all plans) ·
  [Download Full Transcript] gold button (Elite only). [<- Back to dashboard] ghost link.
```

**Code map:** new `app/(student)/dashboard/interview/page.tsx`. Endpoint `endpoints/visaInterview.ts`
exists. New: `components/visa/SetupScreen.tsx`, `QuestionCard.tsx`, `FeedbackPanel.tsx`,
`SummaryRadar.tsx` (recharts-based), `SessionSummary.tsx`. Reuse `UpgradeWall`. Sidebar label:
"Visa Practice".

---

## 11. Upgrade Page

**Route:** `/upgrade` — *(new page)*. Uses the **existing** `endpoints.upgrade.pricing()` module
(`?currency=PKR|GBP|EUR|AED|USD`, PRD §0.5). No Stripe, no checkout — waitlist only. The
`UpgradeWall` component already links here with `?plan=pro` / `?plan=elite` query params; the
page reads `plan` to pre-open the matching waitlist accordion.

### 11.1 Header

```
"Find the right plan for you"                     font-display ~36px weight 700, centered
"Start free. Upgrade when you're serious."         text-base ink-muted, centered

Currency switcher (centered): [PKR] [GBP] [EUR] [AED] [USD]
  Active: bg-ink text-paper, rounded-[12px]. Inactive: bg-paper-warm text-ink-muted. h-9.
  Default: PKR (or from billing_country). On click: all prices update instantly (no reload).
```

### 11.2 Pricing cards — 4 columns

```
Explorer (Free Forever) | Pro (PKR 2,499/mo, "Most popular") | Elite (PKR 7,999/mo,
  "For serious applicants") | Institution (Contact us)

Explorer: standard card. Pro: 2px gold ring + shadow-soft + "Most popular" badge (tone=gold).
Elite: standard card + "For serious applicants" badge (tone=generated). Institution: bg-paper-warm,
dashed border, no price.
Feature rows: [Check validated] included · em dash (ink-subtle) not included.
CTAs: Explorer [Start free] · Pro [Get Pro ->] · Elite [Get Elite ->] · Institution [Contact us ->].
Anchor copy under Pro: "2 months of AidwiseAI Pro = less than 1 consultant meeting."
Anchor copy under Elite: "For Pakistani families in the UK or UAE, less than a coffee per week."

Currency-aware prices (JS swaps all):
  PKR  Free | PKR 2,499/mo | PKR 7,999/mo | Custom
  GBP  Free | GBP 6.99/mo  | GBP 19.99/mo | Custom
  EUR  Free | EUR 7.99/mo  | EUR 22.99/mo | Custom
  AED  Free | AED 29/mo    | AED 89/mo    | Custom
  USD  Free | USD 8.99/mo  | USD 24.99/mo | Custom
```

### 11.3 Waitlist form (inline, Pro and Elite)

Clicking "Get Pro ->" / "Get Elite ->" expands an accordion inside the card (no navigation):

```
Join the Pro waitlist
"Payments launching soon. We'll email you first."
Your email   Input "your@email.com"
[Join Pro Waitlist ->]  gold button, full-width
After submit: [Check] "You're on the list! We'll email you when Pro launches." (validated, animated check)
Posts to POST /waitlist with the pre-selected plan.
```

### 11.4 Comparison table

```
Heading "Compare all features". Columns: Feature | Explorer | Pro | Elite | Institution.
Category rows (bg-paper-dim, uppercase, weight 700 ink-subtle):
  SCHOLARSHIP DISCOVERY  matches Top 3 / All / All + priority / All  ...
  SOP BUILDER            drafts 1 lifetime / Unlimited / Unlimited / Unlimited; line feedback — / — / Check / Check
  VISA INTERVIEW         questions Q1–3 / Full 10 / Full 10 / Full 10; transcript — / — / Check / Check
  TRACKER                tracked Max 3 / Unlimited; reminders 30 days / Email / Email+SMS+WhatsApp / Custom
  ELITE EXCLUSIVE        professor email generator, application strategy PDF, 7-day priority alerts
  B2B                    admin dashboard, bulk import, outcomes analytics  — — — Check
Header row bg-paper-warm uppercase weight 600. Alternating row tints. Check = Lucide Check
(validated); em dash (ink-subtle) = not included; Star (Lucide) = Elite only. Pro column gets a
subtle gold tint. Institution tier appears ONLY here, never inside any student-facing UpgradeWall.
```

**Code map:** new `app/upgrade/page.tsx` (public route, outside the student group). Endpoint
`endpoints/upgrade.ts` exists; add a `waitlist` endpoint module if `POST /waitlist` is not yet
wired. New: `components/upgrade/PricingCard.tsx`, `CurrencySwitcher.tsx`, `WaitlistForm.tsx`,
`ComparisonTable.tsx`.

---

## 12. Privacy & Consent UI

The backend exposes consent, legal, data-export, and account-deletion endpoints (PRD §0.6) with
**no frontend surface yet**. This section is new versus the old `DESIGN_SPEC.md`.

### 12.1 Cookie / consent banner

Bottom-anchored bar on first visit, `bg-paper-white`, border-top 1px, `shadow-soft`.

```
"We use essential cookies to keep AidwiseAI working and analytics to improve it. You control
 the rest."     [Manage]  [Reject non-essential]  [Accept all]
Choice persists to localStorage + POST /privacy/consent (logs IP, user-agent, sha256 of doc body).
If the consent document version has changed since the last grant -> the banner re-appears; the
backend returns HTTP 451 on version mismatch elsewhere.
```

### 12.2 Consent screen / legal viewer

`GET /legal/{slug}` renders Terms, Privacy Policy, DPA, etc. as long-form content (max-w 65–75ch,
clear h2 hierarchy). A sticky "I agree, version 1.0" action bar posts to `POST /privacy/consent`.
Surfaces the Pakistan terms: liability cap PKR 1,000 or 6 months fees, LCIA arbitration,
class-action waiver.

### 12.3 Settings -> Privacy panel — extends `/settings`

```
Privacy & data
  Consent status         per-document: granted version + date, [Review] link to the legal viewer.
  Download my data       [Request export ->]  POST /privacy/data-export; status chip
                         (requested / ready / expired). GET /privacy/data-export lists requests.
  Delete my account      [Request deletion ->] opens a Radix Dialog confirmation. Copy states the
                         30-day window. POST /privacy/account-deletion; DELETE cancels within window.
```

Irreversible actions (account deletion) always use a typed-confirm dialog, never a one-click button.

**Code map:** new `components/privacy/ConsentBanner.tsx`, `app/legal/[slug]/page.tsx`,
and a Privacy panel inside `app/(student)/settings/page.tsx` (extend). New endpoint module
`lib/api/endpoints/privacy.ts` if not already present.

---

## 13. Shared Components

### 13.1 UpgradeWall — `components/UpgradeWall/index.tsx` *(exists, do not rebuild)*

```
Props (actual): {
  detail: PlanRequiredDetail     // { message, price, partial_summary } — verbatim from backend 402
  featureName?: string           // eyebrow label, e.g. "Application tracker"
  showElite?: boolean            // secondary "Or get Elite" CTA (SOP + visa interview only)
  children?: React.ReactNode     // the locked feature; rendered blurred behind the wall
  className?: string
}
Two modes:
  standalone (no children) — centered WallCard, for whole gated pages.
  overlay (with children)  — children render blur-sm opacity-50 pointer-events-none, WallCard
                             absolutely centered over them.
WallCard: rounded-[20px], border 1px, bg-paper-white, p-6, inline shadow. Lock icon in
  paper-warm circle; optional featureName eyebrow (font-mono uppercase); detail.message as the
  font-display headline; PartialSummary grid (answered / avg score / red flags) when present;
  primary CTA Link -> /upgrade?plan=pro labelled "Upgrade to Pro — {detail.price} ->";
  optional secondary CTA -> /upgrade?plan=elite; footnote "No consultant. No hidden fees. Cancel anytime."
Rule: NEVER pass a hand-written generic message. Always the API's detail.message.
```

### 13.2 Compact Scholarship Card

```
+---------------------------------------------------------------+
| [flag] Chevening Scholarship                    96% match     |
|        UK · Fully Funded · Nov 2025                           |
|        [Check] CGPA 3.7 qualifies  [Check] IELTS 7.0          |
|                                      [View]  [+ Tracker]      |
+---------------------------------------------------------------+
h ~88px, bg-paper-white, border 1px, rounded-[12px], p-3.5 px-5. Flag 20px. Name text-sm
weight 600. Detail line text-xs ink-subtle. Checks 11px validated. Match % right, text-sm
weight 700 validated. [View] ghost link text-xs generated. [+ Tracker] secondary, sm.
Used in feed Recent Matches and the dashboard tracker widget.
```

### 13.3 Empty states

```
[Icon 48px, paper-dim tile, ink-subtle, rounded-[14px], p-3.5]
"No applications tracked yet."                              text-base weight 600, mt-4
"Add scholarships from your matches to start tracking
 deadlines and documents."                                 text-sm ink-muted, max-w ~320px
[Add from matches ->]                                       primary, size md, mt-6
Never blank white space. Never bare "No data."
```

### 13.4 Skeleton loading — `components/ui/skeleton.tsx` *(exists)*

Shimmer block, base `bg-paper-dim`, gradient sweep 1.5s. Radius matches the element replaced.
**Shown once per route load** — never spinner-per-card; list re-fetches update in place.

### 13.5 Error state

```
"Couldn't load your matches."
[Retry]   secondary button
Never "Network error" / "500" / stack traces. Always pair with an action: Retry / Reload / Back.
```

### 13.6 Toasts — `sonner` *(exists)*

Optimistic-mutation failures roll back and raise a `sonner` toast that says what to do next.
Success toasts are short ("Profile saved.", "Added to tracker.").

---

## 14. Screen Inventory

| Screen | Route | Owns today | Action | Auth |
|--------|-------|-----------|--------|------|
| Landing | `/` | `app/page.tsx` | rewrite | Public |
| Signup | `/signup` | `app/signup/page.tsx` | extend | Public |
| Login | `/login` | `app/login/page.tsx` | extend | Public |
| Onboarding | `/onboarding` | `app/onboarding/page.tsx` | rewrite (4→5 steps) | Auth |
| Dashboard | `/feed` | `app/(student)/feed/page.tsx` | extend (action grid) | Student |
| Scholarship Finder | `/dashboard/scholarships/match` | — | new | Student |
| Browse All | `/discover` | `app/(student)/discover/page.tsx` | keep | Student |
| Scholarship Detail | `/scholarships/[id]` | `app/(student)/scholarships/[id]/page.tsx` | keep | Student |
| Saved | `/saved` | `app/(student)/saved/page.tsx` | keep | Student |
| Application Tracker | `/dashboard/tracker` | — | new | Student |
| SOP Builder | `/dashboard/documents/sop` | — | new | Student |
| Documents list/detail | `/documents`, `/documents/[id]` | exists | keep | Student |
| Visa Interview | `/dashboard/interview` | — | new | Student |
| Interviews (generic) | `/interviews`, `/interviews/[id]` | exists | keep | Student |
| Profile | `/profile` | `app/(student)/profile/page.tsx` | keep (6-card B2B variant) | Student |
| Settings | `/settings` | `app/(student)/settings/page.tsx` | extend (privacy panel) | Student |
| Upgrade | `/upgrade` | — | new | Public |
| Legal viewer | `/legal/[slug]` | — | new | Public |
| Admin / Mentor | `/admin/*`, `/mentor/*` | exists (2 stubs) | keep / finish stubs | Admin / Mentor |

### Already built and reused (do not rebuild)

`lib/api/client.ts`, all 17 `endpoints/*` modules (incl. `tracker`, `scholarshipMatch`,
`sopBuilder`, `visaInterview`, `upgrade`, `reports`), `lib/api/index.ts` barrel,
`components/UpgradeWall`, `lib/auth/AuthProvider` + `RoleGuard`, `ui/button|input|label|card|
badge|skeleton|dialog|tabs|select`, `shell/AppShell|TopBar`, `scholarship/ScholarshipCard|
RecommendationCard|EligibilityMatrix`, `interview/RubricRadar`.

---

## 15. Key Copy Strings

### Brand
- Public display brand everywhere: **AidwiseAI** (exact casing). Never "ScholarAI", never
  "Aidwise AI", never "AidwiseAI AI", never a model name. Internal/repo docs may still say ScholarAI.
- The lowercase `grantpath.*` localStorage key namespace (`grantpath.access_token`,
  `grantpath.onboarding_draft`, etc.) is a code identifier owned by `lib/api/client.ts`, not the
  display brand. Leave it unchanged — renaming it logs every existing user out.

### Hero
- Headline: "Find fully-funded programs abroad. No consultant. No fees."
- Subheadline: "AidwiseAI matches Pakistani students to scholarships they actually qualify for,
  based on CGPA, IELTS, field, and target country."
- Speed promise: "Get your matches in under 60 seconds."
- Primary CTA: "Find My Scholarships →" · Secondary: "Already have an account? Sign in"

### Onboarding CTAs
- Steps 1–4: "Continue →" · Step 5: "Find My Scholarships →" · Back: "← Back" · "Skip this step →"

### Dashboard CTAs
- "Find Scholarships" → `/dashboard/scholarships/match`
- "Practice Visa Interview" → `/dashboard/interview`
- "Write Your SOP" → `/dashboard/documents/sop`
- "Application Tracker" → `/dashboard/tracker`

### Freemium copy (always from the API 402 `detail.message`, examples)
- Finder: "9 more scholarships match your profile, including 2 fully funded ones closing in 47 days."
- SOP: "Want to adapt this SOP for another university? Pro users generate unlimited SOPs."
- Interview: "You got 2 red flags in 3 answers. Questions 4–10 tell you exactly what to fix."
- Tracker: "You have 4 upcoming deadlines you're not tracking."
- Banned generic fallback: "Upgrade to unlock this feature."

### Pricing anchors
- Under Pro: "2 months of AidwiseAI Pro = less than 1 consultant meeting."
- Under Elite: "For Pakistani families in the UK or UAE, less than a coffee per week."
- Pakistan context: "Less than one hour of a consultant's time per month."

### Trust signals
- "Student-only, we don't take money from universities."
- "No hidden fees. Cancel anytime." · "No consultant. No fees."

### Anti-AI-sluggish copy rules (from `frontend/CLAUDE.md`)
- No model names, no "Powered by". No "AI" in nav copy (sidebar reads "SOP Builder", "Visa
  Practice", "My Matches"). No floating chat bubble, no "Ask AI" button. Replace prompt boxes
  with structured forms. One-line caveat per AI block, never long disclaimers. Specific progress
  labels ("Ranking 247 scholarships") not "Thinking...".

---

*End of AidwiseAI Frontend Design Specification v3. Reconciled against the live codebase on
2026-05-15. Supersedes `DESIGN_SPEC.md`. Companion: `Front-upgrade.html` (sprint delta plan).*

---

## 16. Air University Exhibition Sprint — Pre-Launch Frontend Bundle (2026-05-18)

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` or `superpowers:executing-plans`. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Ship the smallest frontend slice that lets a Pakistani Air University student scan a booth QR, redeem the `AIRU2026` invite code, sign up with PDPB-compliant consent + optional Air U cohort fields, see Pro-tier features, and find a `/upgrade` page with a manual payments block — all live on `https://aidwiseai.com` by 2026-05-19 09:00 PKT.

**Architecture:** Six bounded edits to the live `frontend/src/` tree, plus three new components (`ComingSoon`, `TrialBanner`, `PaymentMethods`) and three observability wrappers (`sentry.ts`, `logrocket.ts`, `statsig.ts`). All adopt the Paper-and-Ink token system from §1, shadcn primitives from §1.5–1.8, and the no-emoji / Lucide-only / 44×44-tap rules from §1.10. Status: **all backend contracts already shipped** (see `Air-exhibition-preparations.md` §0.5). Frontend is the last critical path.

**Tech stack:** Next.js 16 App Router · React 19 · Tailwind 4 (`@theme` tokens) · Bun · shadcn/Radix · Lucide · Statsig client SDK · LogRocket · Crisp Chat widget · `@sentry/nextjs`.

### Sprint ordering rationale

Frontend lands **last** — after backend R1–R5 + DigitalOcean + Cloudflare are live. Reasons:
1. Frontend bundle needs the final backend URL (`api.aidwiseai.com`) baked into `NEXT_PUBLIC_API_BASE_URL` at Vercel build time — change after deploy = rebuild.
2. Invite-code redemption depends on Migration 0026 + auth-service patch being live, otherwise the signup form 400s.
3. Mailgun-from-channels.py must be wired before any signup hits the welcome-email path.
4. Sentry frontend DSN + LogRocket + Crisp + Statsig keys are env vars that only exist after the Day-1 Pack claims.

Net: frontend = Day 3 of the revised Air-exhibition timeline (2026-05-18 morning), with Day 4 reserved for dry-run + flyer print.

### File structure

**Create**
- `frontend/src/components/ComingSoon.tsx` — roadmap grid (10 cards, ETA + status pills)
- `frontend/src/components/TrialBanner.tsx` — 7-day countdown banner
- `frontend/src/components/PaymentMethods.tsx` — manual JazzCash/Easypaisa QR + IBAN block
- `frontend/src/lib/observability/sentry.ts` — Sentry init wrapper
- `frontend/src/lib/observability/logrocket.ts` — LogRocket init wrapper
- `frontend/src/lib/observability/statsig.ts` — Statsig client init + typed gate helpers

**Modify**
- `frontend/src/app/globals.css` — add `--color-gold` + `--color-gold-soft` to `@theme` (Gap 1 from §1.1)
- `frontend/src/app/layout.tsx` — replace `GrantPath` metadata; mount Sentry, LogRocket, Crisp, Statsig providers; declare `metadataBase`
- `frontend/src/app/signup/page.tsx` — replace `GrantPath` header link; add invite-code input (auto-fill from `?invite=`); add Air U dropdowns + consent checkbox + marketing-opt-in
- `frontend/src/app/login/page.tsx` — replace `GrantPath` header link only
- `frontend/src/components/shell/Sidebar.tsx` — replace `GrantPath` brand text; mount `<TrialBanner />` above nav
- `frontend/src/app/(student)/settings/page.tsx` — replace `GrantPath` description copy
- `frontend/src/app/page.tsx` — mount `<ComingSoon />` between hero and footer
- `frontend/src/app/upgrade/page.tsx` — mount `<PaymentMethods />` between comparison table and institution mailto
- `frontend/src/lib/api/types.ts` — extend `User` type with `air_uni_uni`/`air_uni_dept`/`air_uni_batch`/`marketing_opt_in`/`redeemed_invite_code` (sync to backend `0026` schema)

**Do NOT touch (per `frontend/CLAUDE.md` lock)**
- `frontend/src/lib/api/client.ts` — `grantpath.access_token` / `grantpath.refresh_token` / `grantpath.access_expires_at` / `grantpath.onboarding_draft` localStorage keys stay (renaming logs every user out)
- `lib/api/endpoints/*` — backend `/auth/register` already accepts new fields per backend R3

### Task 16.1 — Add `--color-gold` token

**File:** Modify `frontend/src/app/globals.css`

- [ ] **Step 1:** In the `@theme` block, append after the `--color-danger-soft` line:

```css
--color-gold:      #8B6914;   /* Premium / Elite tier, demo banner, pricing emphasis */
--color-gold-soft: #F5EDD6;
```

- [ ] **Step 2:** Run `cd frontend && bun run build` — expect 0 errors. (Tailwind 4 `@theme` auto-generates `text-gold`, `bg-gold`, `bg-gold-soft`, `border-gold` utilities.)
- [ ] **Step 3:** Commit: `git commit -am "feat(design): add --color-gold token for premium accents (Gap 1)"`

### Task 16.2 — Brand hotpatch (5 user-facing files)

**Files:** Modify per grep hits 2026-05-16. Skip localStorage keys and `client.ts` header comment per CLAUDE.md lock.

- [ ] **Step 1:** Verify `frontend/src/lib/brand.ts` exists and exports `BRAND`. If absent, create:

```ts
export const BRAND = "AidwiseAI" as const;
export const BRAND_TAGLINE = "Pakistan's AI scholarship co-pilot";
export const PARTNERSHIPS_EMAIL = "partnerships@aidwiseai.com";
export const PAYMENTS_EMAIL = "payments@aidwiseai.com";
export const SUPPORT_EMAIL = "hello@aidwiseai.com";

export const partnershipsMailto = (subject = "Institutional partnership") =>
    `mailto:${PARTNERSHIPS_EMAIL}?subject=${encodeURIComponent(subject)}`;
```

- [ ] **Step 2:** In `frontend/src/app/layout.tsx:29-34`, replace metadata block:

```tsx
import { BRAND } from "@/lib/brand";

export const metadata: Metadata = {
  metadataBase: new URL("https://aidwiseai.com"),
  title: { default: BRAND, template: `%s · ${BRAND}` },
  description: "AI scholarship matching, SOP drafting, and visa-interview practice for Pakistani students.",
  applicationName: BRAND,
};
```

- [ ] **Step 3:** In `frontend/src/app/signup/page.tsx:45`, swap `GrantPath` text for `{BRAND}` + add import.
- [ ] **Step 4:** Same in `frontend/src/app/login/page.tsx:55`.
- [ ] **Step 5:** In `frontend/src/components/shell/Sidebar.tsx:96`, swap for `{BRAND}` + import.
- [ ] **Step 6:** In `frontend/src/app/(student)/settings/page.tsx:70`, replace `"Sign out of GrantPath on this device."` with `` `Sign out of ${BRAND} on this device.` ``.
- [ ] **Step 7:** Re-grep:

```bash
cd frontend && rg -n "GrantPath" src/ | grep -v "client.ts" | grep -v "grantpath\."
# expect empty
```

- [ ] **Step 8:** `bun run lint && bunx --bun tsc --noEmit && bun run build` — expect 0 errors
- [ ] **Step 9:** Commit: `git commit -am "feat(brand): hotpatch GrantPath -> AidwiseAI in 5 user-facing surfaces"`

### Task 16.3 — `ComingSoon` roadmap component

**Files:** Create `frontend/src/components/ComingSoon.tsx`. Modify `frontend/src/app/page.tsx`.

Honors §1 tokens + §1.8 chip styling. ETA tone uses `gold` / `generated` / `validated` / `ink-subtle` semantic colors. 3-col desktop, 1-col mobile.

- [ ] **Step 1:** Create the component (full code in `Air-exhibition-preparations.md` Task 3.6b — copy verbatim, replacing raw `bg-amber-*` / `bg-sky-*` / `bg-violet-*` / `bg-stone-*` classes with token-based equivalents per the `ETA_TONE` map below):

```ts
const ETA_TONE: Record<Eta, string> = {
  "Jun 2026": "bg-gold-soft text-gold ring-gold/20",
  "Q3 2026": "bg-generated-soft text-generated ring-generated/20",
  "Q4 2026": "bg-validated-soft text-validated ring-validated/20",
  "2027": "bg-paper-warm text-ink-subtle ring-border",
};

const STATUS_DOT: Record<Status, string> = {
  "in-design": "bg-ink-subtle",
  "in-dev": "bg-validated",
  planned: "bg-paper-dim",
};
```

Replace generic Tailwind colors (`text-stone-*`, `bg-stone-*`) with `text-ink`, `text-ink-muted`, `text-ink-subtle`, `bg-paper-white`, `bg-paper-warm` per §1.

- [ ] **Step 2:** Mount in `frontend/src/app/page.tsx` after the pricing teaser (§3.8) and before `<Footer />`:

```tsx
import { ComingSoon } from "@/components/ComingSoon";
// ...
<ComingSoon />
```

- [ ] **Step 3:** Smoke `http://localhost:3000/#roadmap` — 10 cards, 3-col desktop, ETA badges color-coded.
- [ ] **Step 4:** Lighthouse check — roadmap section adds <5 KB to bundle.
- [ ] **Step 5:** Commit: `git commit -am "feat(landing): ComingSoon roadmap section (10 pipeline cards)"`

### Task 16.4 — Signup invite-code + Air U + consent v1.0

**File:** Modify `frontend/src/app/signup/page.tsx`

Mandatory consent v1.0 checkbox; marketing-opt-in default off; invite-code input auto-fills from `?invite=` URL param and force-uppercases. Air U fields optional. Form posts to `POST /api/v1/auth/register` (backend R3 ships invite_code + air_uni_* + consent_v + marketing_opt_in support).

- [ ] **Step 1:** Add at top of file:

```tsx
"use client";
import { useSearchParams } from "next/navigation";
import { useState, useEffect } from "react";
import { BRAND } from "@/lib/brand";
```

- [ ] **Step 2:** Inside component:

```tsx
const params = useSearchParams();
const [inviteCode, setInviteCode] = useState("");
const [airUniUni, setAirUniUni] = useState("");
const [airUniDept, setAirUniDept] = useState("");
const [airUniBatch, setAirUniBatch] = useState<number | "">("");
const [consent, setConsent] = useState(false);
const [marketing, setMarketing] = useState(false);

useEffect(() => {
  const q = params.get("invite");
  if (q) setInviteCode(q.toUpperCase());
}, [params]);
```

- [ ] **Step 3:** In submit handler:

```tsx
if (!consent) {
  toast.error("Please accept the data processing terms to continue.");
  return;
}
const payload = {
  email,
  password,
  full_name: fullName,
  invite_code: inviteCode || undefined,
  air_uni_uni: airUniUni || undefined,
  air_uni_dept: airUniDept || undefined,
  air_uni_batch: airUniBatch || undefined,
  consent_v: "v1.0",
  marketing_opt_in: marketing,
};
await registerUser(payload);
```

- [ ] **Step 4:** Insert into JSX above submit button:

```tsx
<div className="space-y-1.5">
  <Label htmlFor="invite-code">Invite code (optional)</Label>
  <Input
    id="invite-code"
    value={inviteCode}
    onChange={(e) => setInviteCode(e.target.value.toUpperCase())}
    placeholder="AIRU2026"
    autoComplete="off"
  />
</div>

<fieldset className="space-y-3 rounded-lg border border-border bg-paper-warm/40 p-4">
  <legend className="px-2 text-xs uppercase tracking-wider text-ink-subtle">
    About you (optional — helps us personalise)
  </legend>
  <Input placeholder="University (e.g. Air University)"
         value={airUniUni} onChange={(e) => setAirUniUni(e.target.value)} />
  <Input placeholder="Department (e.g. CS, EE, BBA)"
         value={airUniDept} onChange={(e) => setAirUniDept(e.target.value)} />
  <Input type="number" min={2018} max={2030}
         placeholder="Batch year (e.g. 2023)"
         value={airUniBatch}
         onChange={(e) => setAirUniBatch(e.target.value ? Number(e.target.value) : "")} />
</fieldset>

<label className="flex gap-3 text-sm text-ink-muted">
  <input type="checkbox" required checked={consent}
         onChange={(e) => setConsent(e.target.checked)}
         className="mt-0.5 h-4 w-4 accent-ink" />
  <span>
    I agree to {BRAND}&apos;s{" "}
    <Link href="/legal/trial-tnc-v1.0" target="_blank" className="underline">
      data processing &amp; trial terms (v1.0)
    </Link>.
  </span>
</label>

<label className="flex gap-3 text-sm text-ink-muted">
  <input type="checkbox" checked={marketing}
         onChange={(e) => setMarketing(e.target.checked)}
         className="mt-0.5 h-4 w-4 accent-ink" />
  <span>I&apos;m OK with {BRAND} quoting my anonymised feedback in marketing.</span>
</label>
```

- [ ] **Step 5:** Tap-target audit: shadcn `Input` defaults to 44px height — confirm in DevTools.
- [ ] **Step 6:** `bun run lint && bunx --bun tsc --noEmit && bun run build` — 0 errors
- [ ] **Step 7:** Smoke `http://localhost:3000/signup?invite=AIRU2026` → field pre-filled, consent blocks submit, success returns Pro user.
- [ ] **Step 8:** Commit: `git commit -am "feat(signup): invite code + Air U cohort + consent v1.0 + marketing opt-in"`

### Task 16.5 — `TrialBanner` countdown in sidebar

**Files:** Create `frontend/src/components/TrialBanner.tsx`. Modify `Sidebar.tsx`.

Visible only when `plan_expires_at` is within 7 days. Uses `--color-gold-soft` per §1.1 Gap 1.

- [ ] **Step 1:** Create the component:

```tsx
"use client";
import Link from "next/link";
import { differenceInDays, parseISO } from "date-fns";

export function TrialBanner({ expiresAt }: { expiresAt: string | null }) {
  if (!expiresAt) return null;
  const days = differenceInDays(parseISO(expiresAt), new Date());
  if (days < 0 || days > 7) return null;
  return (
    <div className="mx-3 mb-4 rounded-lg border border-gold/20 bg-gold-soft px-3 py-2.5 text-xs leading-relaxed text-ink">
      <p className="font-medium">
        Pro trial ends in <span className="text-gold">{days} {days === 1 ? "day" : "days"}</span>.
      </p>
      <Link href="/upgrade" className="mt-1 inline-block font-medium text-gold underline">
        Upgrade to keep your matches →
      </Link>
    </div>
  );
}
```

- [ ] **Step 2:** In `Sidebar.tsx`, mount `<TrialBanner expiresAt={user?.plan_expires_at ?? null} />` above the primary nav `<ul>`. Pull `user` from existing `useAuth()` context.
- [ ] **Step 3:** `bun run build` — 0 errors
- [ ] **Step 4:** Smoke: Pro user with `plan_expires_at` 5 days out → banner visible with "5 days" + gold tint.
- [ ] **Step 5:** Commit: `git commit -am "feat(sidebar): trial-expiry countdown banner (7-day window, gold)"`

### Task 16.6 — `PaymentMethods` block on upgrade page

**Files:** Create `frontend/src/components/PaymentMethods.tsx`. Modify `frontend/src/app/upgrade/page.tsx`.

V1 manual payment block — mailto + JazzCash QR + Easypaisa QR + IBAN. Placeholders must be replaced before deploy (Task 16.10 Gate 2).

- [ ] **Step 1:** Create the component:

```tsx
import { PAYMENTS_EMAIL } from "@/lib/brand";

interface Props { userEmail?: string }

export function PaymentMethods({ userEmail }: Props) {
  const subject = encodeURIComponent(`Upgrade to Pro — ${userEmail ?? ""}`.trim());
  const body = encodeURIComponent(
    "Hi AidwiseAI team,\n\nI just transferred PKR 2,999. Reference attached.\n\nThanks."
  );
  return (
    <section className="mt-10 rounded-xl border border-border bg-paper-white p-6">
      <h3 className="font-display text-lg text-ink">Pay manually (Beta)</h3>
      <p className="mt-2 text-sm leading-relaxed text-ink-muted">
        One-click checkout via Safepay (JazzCash, Easypaisa, Visa, Mastercard, PayPak, RAAST)
        arrives in June 2026. Until then, transfer the amount and email proof to{" "}
        <a href={`mailto:${PAYMENTS_EMAIL}`} className="text-generated underline">{PAYMENTS_EMAIL}</a>.
        We activate within 4 hours.
      </p>

      <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-3">
        <article className="rounded-lg border border-border bg-paper-warm/50 p-4">
          <p className="text-xs uppercase tracking-wider text-ink-subtle">JazzCash</p>
          <p className="mt-1 font-mono text-sm text-ink">0300-XXXXXXX</p>
          <p className="mt-1 text-xs text-ink-subtle">Account title: <em>{"<your name>"}</em></p>
        </article>
        <article className="rounded-lg border border-border bg-paper-warm/50 p-4">
          <p className="text-xs uppercase tracking-wider text-ink-subtle">Easypaisa</p>
          <p className="mt-1 font-mono text-sm text-ink">0345-XXXXXXX</p>
        </article>
        <article className="rounded-lg border border-border bg-paper-warm/50 p-4">
          <p className="text-xs uppercase tracking-wider text-ink-subtle">Bank / RAAST</p>
          <p className="mt-1 font-mono text-sm text-ink">PKxx XXXX XXXX XXXX XXXX</p>
          <p className="mt-1 text-xs text-ink-subtle">Meezan / Alfalah / HBL</p>
        </article>
      </div>

      <a
        href={`mailto:${PAYMENTS_EMAIL}?subject=${subject}&body=${body}`}
        className="mt-5 inline-flex h-11 items-center rounded-md bg-ink px-5 text-sm font-medium text-paper-white hover:bg-ink-strong"
      >
        Email payment proof
      </a>
    </section>
  );
}
```

- [ ] **Step 2:** Mount in `upgrade/page.tsx` after `COMPARISON_ROWS` and before institution mailto: `<PaymentMethods userEmail={user?.email} />`
- [ ] **Step 3:** Add comment `// TODO(2026-05-18 pre-deploy): replace 0300-XXXXXXX, 0345-XXXXXXX, IBAN with real values` above the import.
- [ ] **Step 4:** `bun run build` — 0 errors
- [ ] **Step 5:** Commit: `git commit -am "feat(upgrade): manual payment block (JazzCash/Easypaisa/IBAN) — v1 pre-Safepay"`

### Task 16.7 — Sentry frontend init

**Files:** Create `frontend/src/lib/observability/sentry.ts`. Modify `layout.tsx`.

- [ ] **Step 1:** `cd frontend && bun add @sentry/nextjs`
- [ ] **Step 2:** Create wrapper:

```ts
import * as Sentry from "@sentry/nextjs";

export function initSentry() {
  if (typeof window === "undefined") return;
  if (!process.env.NEXT_PUBLIC_SENTRY_DSN) return;
  Sentry.init({
    dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
    environment: process.env.NEXT_PUBLIC_SENTRY_ENV ?? "production",
    tracesSampleRate: 0.1,
    replaysSessionSampleRate: 0,
    replaysOnErrorSampleRate: 1.0,
  });
}
```

- [ ] **Step 3:** Call `initSentry()` once from a `<Providers />` client component imported in `layout.tsx`.
- [ ] **Step 4:** Set `NEXT_PUBLIC_SENTRY_DSN` env in Vercel.
- [ ] **Step 5:** Trigger a deliberate error and confirm Sentry receives it.
- [ ] **Step 6:** Commit: `git commit -am "feat(observability): wire Sentry frontend SDK"`

### Task 16.8 — Statsig client SDK

**Files:** Create `frontend/src/lib/observability/statsig.ts`. Modify `layout.tsx`.

- [ ] **Step 1:** `bun add statsig-react`
- [ ] **Step 2:** Wrap providers tree with `<StatsigProvider sdkKey={process.env.NEXT_PUBLIC_STATSIG_CLIENT_KEY!} user={{ userID: user?.id ?? "anon" }} waitForInitialization>`
- [ ] **Step 3:** Helper file:

```ts
import { useGate, useExperiment } from "statsig-react";

export const useKimiModelGate = () => useGate("kimi_model_eval").value;
export const useTrialBannerExperiment = () => useExperiment("trial_banner_copy_v2");
export const useAirUCohort = () => useGate("cohort_au2026").value;
```

- [ ] **Step 4:** Create the three gates in Statsig dashboard, `enabled=false` default-off.
- [ ] **Step 5:** Commit: `git commit -am "feat(observability): Statsig client SDK + 3 starter gates"`

### Task 16.9 — LogRocket + Crisp widget

**Files:** Create `frontend/src/lib/observability/logrocket.ts`. Modify `layout.tsx`.

- [ ] **Step 1:** `bun add logrocket`
- [ ] **Step 2:** Create wrapper:

```ts
import LogRocket from "logrocket";

export function initLogRocket() {
  if (typeof window === "undefined") return;
  if (process.env.NODE_ENV !== "production") return;
  if (!process.env.NEXT_PUBLIC_LOGROCKET_APP_ID) return;
  LogRocket.init(process.env.NEXT_PUBLIC_LOGROCKET_APP_ID);
}
```

- [ ] **Step 3:** Call `initLogRocket()` next to `initSentry()` in `<Providers>`.
- [ ] **Step 4:** Mount Crisp `<Script>` in `layout.tsx` body after `<Providers>`:

```tsx
<Script id="crisp" strategy="afterInteractive">{`
  window.$crisp=[];window.CRISP_WEBSITE_ID="${process.env.NEXT_PUBLIC_CRISP_ID}";
  (function(){var d=document,s=d.createElement("script");s.src="https://client.crisp.chat/l.js";s.async=1;d.getElementsByTagName("head")[0].appendChild(s);})();
`}</Script>
```

- [ ] **Step 5:** Lighthouse — confirm LCP impact <100ms (Crisp loads after-interactive).
- [ ] **Step 6:** Commit: `git commit -am "feat(observability): LogRocket session replay + Crisp chat widget"`

### Task 16.10 — Pre-deploy gate

Run in order. Every gate must pass before Vercel deploy.

- [ ] **Gate 1:** `cd frontend && rg -n "GrantPath" src/ | grep -v "client.ts" | grep -v "grantpath\."` → **empty**
- [ ] **Gate 2:** `rg -n "0300-XXXXXXX|0345-XXXXXXX|PKxx XXXX" src/components/PaymentMethods.tsx` → **empty** (real values substituted)
- [ ] **Gate 3:** `bun run lint` → **0 warnings**
- [ ] **Gate 4:** `bunx --bun tsc --noEmit` → **0 errors**
- [ ] **Gate 5:** `bun run build` → **0 errors**; Lighthouse `--preset=desktop` shows JS ≤ 200 KB gzip on `/`
- [ ] **Gate 6:** Local Vercel preview via `vercel dev` — manual smoke `/signup?invite=AIRU2026` → `/feed` → `/tracker` → `/documents/sop` → `/upgrade`. Invite pre-fills, consent required, Pro user created, all 4 routes render, payment block visible.
- [ ] **Gate 7:** Sentry dashboard receives 1 test event from `vercel dev`.
- [ ] **Gate 8:** Statsig dashboard shows new `userID` from logged-in preview session.
- [ ] **Gate 9:** Commit: `git commit -am "chore(frontend): exhibition sprint complete, gates green"`

### Task 16.11 — Vercel deploy

- [ ] **Step 1:** Vercel → Import Project → repo → root `frontend`
- [ ] **Step 2:** Framework Next.js. Build cmd `bun run build`. Install `bun install`.
- [ ] **Step 3:** Env vars:

```
NEXT_PUBLIC_API_BASE_URL=https://api.aidwiseai.com/api/v1
NEXT_PUBLIC_BRAND=AidwiseAI
NEXT_PUBLIC_SENTRY_DSN=<frontend dsn from Pack claim>
NEXT_PUBLIC_SENTRY_ENV=production
NEXT_PUBLIC_STATSIG_CLIENT_KEY=<client key>
NEXT_PUBLIC_LOGROCKET_APP_ID=<logrocket app id>
NEXT_PUBLIC_CRISP_ID=<crisp website id>
```

- [ ] **Step 4:** Add custom domain `aidwiseai.com` + `www.aidwiseai.com` per `Air-exhibition-preparations.md` deploy section.
- [ ] **Step 5:** Smoke `https://aidwiseai.com/signup?invite=AIRU2026` redeems against live `api.aidwiseai.com` → Pro user created.

### Self-Review

- [x] **Spec coverage** — Every frontend-touching locked decision from `Air-exhibition-preparations.md` §0 (brand, invite-UX, consent, trial banner, manual payment, Coming Soon, observability) has a numbered task.
- [x] **Token discipline** — No inline hex; all colors via `--color-*` including the new `--color-gold` from Task 16.1.
- [x] **shadcn over Radix** — Form controls reuse `components/ui/*` per §1.5–1.6.
- [x] **Lucide-only icons** — No emoji-as-UI; ETA badges use shaped chips with colored dots.
- [x] **Accessibility** — Consent is `required`; tap targets ≥44×44 via shadcn defaults; gold-on-paper contrast >7:1.
- [x] **Performance budget** — LogRocket + Crisp after-interactive; Statsig waits init only on first render; ComingSoon is static markup.
- [x] **No backend touch** — Endpoints already exist; frontend consumes existing `auth/register`, `/upgrade/pricing`, `/scholarships/match`.

---

*End of §16. Companion: `Air-exhibition-preparations.md` (backend + ops). Sprint window: 2026-05-18 morning → 2026-05-19 09:00 PKT deadline. Frontend lands LAST after backend R1–R5 + DigitalOcean + Mailgun + Cloudflare are live.*

---

## 17. Frontend Gap Backlog (post-PR-#87, 2026-05-17)

Frontend-side items pulled from `CLAUDE.md` "Open work" + "Backend gap audit" + outstanding launch-prep punchlist. §16 covers the Air-Uni sprint; §17 captures everything else that touches `frontend/`. Items ordered by launch criticality.

### Inventory

| # | Item | Surface | Blocks May-19? | Effort |
|---|---|---|---:|---:|
| 17.1 | Playwright smoke selectors stale post-S87 — re-point `data-testid` to rebuilt UI | `tests/e2e/playwright/` | No | 1–2 d |
| 17.2 | Remove `continue-on-error: true` on `browser-smoke` step in `.github/workflows/ci.yml:198` | CI | No (cleanup) | 5 min after 17.1 |
| 17.3 | Consent UI surface: cookie banner + `/settings/privacy` panel + data-export + 30-day deletion request | `(student)/settings/privacy/page.tsx` (new), `components/CookieBanner.tsx` (new) | **Yes** (PDPB hard requirement at signup per launch plan §0) | 4–6 hrs |
| 17.4 | Booth-specific landing: `/booth/air-university` with cohort copy + QR-target signup CTA | `app/booth/air-university/page.tsx` (new) | Recommended | 1 hr |
| 17.5 | Trial-expired empty state — once cron flips a Pro user to free, surface in-app banner explaining lock + upgrade CTA | `components/TrialExpiredBanner.tsx` (new), mounted in `(student)/layout.tsx` | No (Week 5+) | 1 hr |
| 17.6 | `Sentry` route-change instrumentation + 5xx ErrorBoundary | `app/error.tsx`, `lib/observability/sentry.ts` | No | 30 min |
| 17.7 | Vercel `NEXT_PUBLIC_API_BASE_URL` env wired to `https://api.aidwiseai.com/api/v1` post-DO custom-domain mapping | Vercel dashboard | **Yes** | 2 min |
| 17.8 | Frontend Mailgun-from preview — register flow shows "Check your email at X" using `BRAND_DISPLAY_NAME` not hardcoded "AidwiseAI" | `signup/page.tsx`, `verify/page.tsx` | No | 15 min |
| 17.9 | Frontend integration tests for invite-redeem path (Vitest + MSW + RTL) — no `*.test.*` under `frontend/src` today per CLAUDE.md | `frontend/src/**/__tests__/` (new) | No | 4 hrs |
| 17.10 | `IMPLEMENTATION_STATUS_REPORT.md` + `frontend/README.md` refresh for Pakistan pivot + S87 + Q1 retier | docs | No | 30 min |

### Task 17.1 — Re-point Playwright smoke selectors

Smoke suite was built against pre-greenfield UI; S87 rewrote `(student)/*` so every `data-testid="..."` selector resolves to nothing → CI marks pass under `continue-on-error: true` (CLAUDE.md hard warning).

**Files:** `tests/e2e/playwright/run_smoke_suite.py` + `tests/e2e/playwright/specs/*.spec.ts`

- [ ] **Step 1:** Run `python tests/e2e/playwright/run_smoke_suite.py --list-failures` against local dev → capture every missing selector.
- [ ] **Step 2:** Add canonical `data-testid` attributes to S87 components:
  - `(student)/scholarships/page.tsx` → `data-testid="match-card"`, `match-unlock-cta`, `match-blurred-card`
  - `(student)/tracker/page.tsx` → `kanban-column-{stage}`, `tracker-card-{id}`, `tracker-add-btn`
  - `(student)/documents/sop/page.tsx` → `sop-input`, `sop-generated-panel`, `sop-feedback-panel`
  - `(student)/interviews/visa/page.tsx` → `visa-question`, `visa-answer-input`, `visa-rubric-radar`
  - `signup/page.tsx` → `signup-invite-code`, `signup-consent`, `signup-submit`
  - `upgrade/page.tsx` → `upgrade-tier-{plan}`, `upgrade-currency-{code}`, `upgrade-cta`
- [ ] **Step 3:** Update `specs/student_happy_path.spec.ts` to use new selectors.
- [ ] **Step 4:** Local run: `python tests/e2e/playwright/run_smoke_suite.py` → all green.
- [ ] **Step 5:** Commit: `test(smoke): re-point selectors to S87 rebuilt UI`

### Task 17.2 — Remove browser-smoke CI flag

**File:** `.github/workflows/ci.yml:198`

- [ ] **Step 1:** Confirm 17.1 landed and `browser-smoke` job is genuinely green (check log, not just status badge).
- [ ] **Step 2:** Delete `continue-on-error: true` line + the TODO marker comment at `:192`.
- [ ] **Step 3:** Push, watch CI fail on a deliberate selector break (sanity-check the gate now actually gates).
- [ ] **Step 4:** Revert sanity break.
- [ ] **Step 5:** Commit: `ci: remove browser-smoke continue-on-error (selectors re-pointed in S88)`

### Task 17.3 — Consent UI + cookie banner + privacy panel

PDPB v1.0 is enforced at signup backend-side (Task 16.4 covers consent checkbox). Missing: post-signup management surface + cookie banner for anonymous traffic + data-export + deletion request UX.

**Files:** Create `components/CookieBanner.tsx`, `app/(student)/settings/privacy/page.tsx`. Modify `app/layout.tsx`.

- [ ] **Step 1:** Cookie banner (cookie-less analytics-grade per PDPB §0.6 trust boundary):

```tsx
"use client";
import { useEffect, useState } from "react";
import { BRAND } from "@/lib/brand";

const COOKIE_KEY = "aidwiseai.cookie_consent";

export function CookieBanner() {
  const [shown, setShown] = useState(false);
  useEffect(() => {
    if (typeof window !== "undefined" && !localStorage.getItem(COOKIE_KEY)) setShown(true);
  }, []);
  if (!shown) return null;
  const accept = () => { localStorage.setItem(COOKIE_KEY, "v1.0"); setShown(false); };
  const reject = () => { localStorage.setItem(COOKIE_KEY, "rejected"); setShown(false); };
  return (
    <div role="dialog" aria-label="Cookie consent"
         className="fixed bottom-4 left-4 right-4 z-50 mx-auto max-w-2xl rounded-xl border border-border bg-paper-white p-4 shadow-lg sm:p-5">
      <p className="text-sm text-ink">
        {BRAND} uses essential cookies for auth + a privacy-respecting analytics ping.
        No third-party trackers. See our{" "}
        <a href="/legal/privacy-v1.0" className="underline">Privacy Policy</a>.
      </p>
      <div className="mt-3 flex gap-3">
        <button onClick={accept} className="h-10 rounded-md bg-ink px-4 text-sm text-paper-white">Accept</button>
        <button onClick={reject} className="h-10 rounded-md border border-border px-4 text-sm text-ink">Essential only</button>
      </div>
    </div>
  );
}
```

- [ ] **Step 2:** Mount `<CookieBanner />` in `app/layout.tsx` body, after `<Providers>`.
- [ ] **Step 3:** Privacy panel — consumes backend `POST/GET /api/v1/privacy/consent`, `POST/GET /api/v1/privacy/data-export`, `POST/DELETE /api/v1/privacy/account-deletion` (shipped per CLAUDE.md "New endpoints").

```tsx
// app/(student)/settings/privacy/page.tsx
"use client";
import { useEffect, useState } from "react";
import { privacyApi } from "@/lib/api/endpoints/privacy";

export default function PrivacyPanel() {
  const [consents, setConsents] = useState([]);
  const [exportStatus, setExportStatus] = useState<string | null>(null);
  const [delPending, setDelPending] = useState(false);

  useEffect(() => { privacyApi.listConsents().then(setConsents); }, []);

  const requestExport = async () => {
    const r = await privacyApi.requestExport();
    setExportStatus(`Queued — we'll email a download link to your inbox within 7 days. Request id: ${r.id}`);
  };
  const requestDelete = async () => {
    if (!confirm("Permanently delete your account in 30 days? You can cancel anytime in this panel before then.")) return;
    await privacyApi.requestDeletion();
    setDelPending(true);
  };
  const cancelDelete = async () => { await privacyApi.cancelDeletion(); setDelPending(false); };

  return (
    <section className="space-y-8 p-6">
      <header>
        <h1 className="font-display text-2xl text-ink">Privacy & data</h1>
        <p className="mt-1 text-sm text-ink-muted">PDPB v1.0 compliant. Latest grant wins; we keep a 7-year audit log.</p>
      </header>

      <article>
        <h2 className="text-lg text-ink">Active consents</h2>
        <ul className="mt-3 space-y-2 text-sm">
          {consents.map(c => (
            <li key={c.id} className="flex justify-between rounded-md border border-border p-3">
              <span>{c.doc_slug} <span className="text-ink-subtle">v{c.version}</span></span>
              <time className="text-ink-subtle">{new Date(c.granted_at).toLocaleDateString()}</time>
            </li>
          ))}
        </ul>
      </article>

      <article>
        <h2 className="text-lg text-ink">Data export</h2>
        <p className="mt-1 text-sm text-ink-muted">Download everything we store about you (JSON + CSV).</p>
        <button onClick={requestExport} className="mt-3 h-11 rounded-md bg-ink px-5 text-sm text-paper-white">Request export</button>
        {exportStatus && <p className="mt-2 text-sm text-validated">{exportStatus}</p>}
      </article>

      <article>
        <h2 className="text-lg text-ink">Delete account</h2>
        <p className="mt-1 text-sm text-ink-muted">30-day grace period. Cancel anytime before deletion.</p>
        {delPending ? (
          <button onClick={cancelDelete} className="mt-3 h-11 rounded-md border border-danger px-5 text-sm text-danger">
            Cancel pending deletion
          </button>
        ) : (
          <button onClick={requestDelete} className="mt-3 h-11 rounded-md border border-danger px-5 text-sm text-danger">
            Request deletion
          </button>
        )}
      </article>
    </section>
  );
}
```

- [ ] **Step 4:** Create `lib/api/endpoints/privacy.ts` thin wrapper around the four endpoints if not present.
- [ ] **Step 5:** Add sidebar link "Privacy & data" under existing Settings section.
- [ ] **Step 6:** Smoke: signup → settings/privacy → request export → see queued; request deletion → see cancel button; cancel.
- [ ] **Step 7:** `bun run lint && bunx --bun tsc --noEmit && bun run build` → 0 errors.
- [ ] **Step 8:** Commit: `feat(privacy): cookie banner + /settings/privacy panel (consent, export, deletion)`

### Task 17.4 — Booth-specific landing `/booth/air-university`

QR posters point to `aidwiseai.com/signup?invite=AIRU2026` per `scripts/generate_qr_flyers.py`. Add interstitial `aidwiseai.com/booth/air-university` for in-person walk-by traffic that wants context before signup.

**File:** Create `app/booth/air-university/page.tsx`

- [ ] **Step 1:** Static server component, no auth required, ~80 lines:

```tsx
import Link from "next/link";
import { BRAND } from "@/lib/brand";

export const metadata = {
  title: `Air University × ${BRAND}`,
  description: "Free 30-day Pro trial for Air University students — exhibition launch May 19, 2026.",
};

export default function Page() {
  return (
    <main className="mx-auto max-w-3xl px-6 py-16">
      <p className="text-xs uppercase tracking-wider text-ink-subtle">Exhibition · May 19, 2026</p>
      <h1 className="mt-2 font-display text-4xl text-ink">Welcome, Air University student.</h1>
      <p className="mt-4 text-lg text-ink-muted">
        We&apos;re giving the first 100 Air U students a free 30-day Pro trial of {BRAND} —
        AI-powered scholarship matching, SOP drafting, and visa-interview practice tuned for Pakistani applicants.
      </p>

      <section className="mt-10 grid gap-4 sm:grid-cols-2">
        {[
          ["Scholarship matching", "Find Chevening, Fulbright, DAAD, HEC scholarships you actually qualify for."],
          ["SOP builder", "Draft a personal statement in 10 minutes — Pakistan context built-in."],
          ["Visa interview practice", "70 real questions for UK/US/CA/DE consulates, with rubric feedback."],
          ["Application tracker", "Kanban for deadlines + HEC attestation checklist."],
        ].map(([title, body]) => (
          <article key={title} className="rounded-xl border border-border bg-paper-white p-5">
            <h3 className="font-display text-lg text-ink">{title}</h3>
            <p className="mt-1 text-sm text-ink-muted">{body}</p>
          </article>
        ))}
      </section>

      <div className="mt-10 rounded-xl border border-gold/20 bg-gold-soft p-6">
        <p className="text-sm text-ink">Use code <code className="font-mono text-gold">AIRU2026</code> at signup.</p>
        <Link
          href="/signup?invite=AIRU2026"
          className="mt-4 inline-flex h-12 items-center rounded-md bg-ink px-6 text-sm font-medium text-paper-white">
          Claim my 30-day Pro trial →
        </Link>
        <p className="mt-3 text-xs text-ink-subtle">
          100 redemptions · May 19 09:00 → May 26 23:59 PKT · No card required.
        </p>
      </div>
    </main>
  );
}
```

- [ ] **Step 2:** `bun run build` → 0 errors.
- [ ] **Step 3:** Optionally regenerate QR flyers to point at `/booth/air-university` instead of `/signup?invite=AIRU2026` if the booth team wants the interstitial.
- [ ] **Step 4:** Commit: `feat(booth): /booth/air-university landing for QR walk-by traffic`

### Task 17.5 — Trial-expired in-app banner

`expire_trial_plans` cron flips `plan = free` daily at 02:00 UTC. Users get email, but in-app needs a visible reason for sudden lock.

**File:** Create `components/TrialExpiredBanner.tsx`. Mount in `(student)/layout.tsx`.

- [ ] **Step 1:** Visible when `user.plan === "free"` AND `user.redeemed_invite_code !== null` (i.e. previously redeemed, now expired):

```tsx
"use client";
import Link from "next/link";
import { useAuth } from "@/lib/auth/context";

export function TrialExpiredBanner() {
  const { user } = useAuth();
  if (!user || user.plan !== "free" || !user.redeemed_invite_code) return null;
  return (
    <div className="border-b border-gold/30 bg-gold-soft px-6 py-2.5 text-sm text-ink">
      Your Pro trial has ended. Upgrade to keep your matches, tracker, and SOPs.{" "}
      <Link href="/upgrade" className="font-medium text-gold underline">See plans →</Link>
    </div>
  );
}
```

- [ ] **Step 2:** Mount above `<Sidebar />` in `(student)/layout.tsx`.
- [ ] **Step 3:** Smoke (manual SQL flip): `UPDATE users SET plan='free' WHERE email='zara.khan@example.com';` → reload → banner shows.
- [ ] **Step 4:** Commit: `feat(trial): in-app banner when redeemed trial has expired`

### Task 17.6 — Sentry route-change + error boundary

**Files:** `app/error.tsx` (new), augment `lib/observability/sentry.ts`.

- [ ] **Step 1:** Add `app/error.tsx` (Next.js convention — catches segment errors):

```tsx
"use client";
import * as Sentry from "@sentry/nextjs";
import { useEffect } from "react";

export default function Error({ error, reset }: { error: Error & { digest?: string }, reset: () => void }) {
  useEffect(() => { Sentry.captureException(error); }, [error]);
  return (
    <main className="mx-auto max-w-xl p-10 text-center">
      <h1 className="font-display text-2xl text-ink">Something broke.</h1>
      <p className="mt-2 text-sm text-ink-muted">We&apos;ve been notified. Try again, or refresh.</p>
      <button onClick={reset} className="mt-6 h-11 rounded-md bg-ink px-5 text-sm text-paper-white">Try again</button>
    </main>
  );
}
```

- [ ] **Step 2:** Sentry router instrumentation lives in `@sentry/nextjs` auto-instrumentation when `Sentry.init()` runs in client.
- [ ] **Step 3:** Trigger a deliberate `throw` in a page → confirm event in Sentry dashboard.
- [ ] **Step 4:** Commit: `feat(observability): Sentry root error boundary + auto route instrumentation`

### Task 17.7 — Vercel env wired to live API base

- [ ] **Step 1:** Once DO custom domain `api.aidwiseai.com` resolves (post-Task 16.11 + Cloudflare DNS), set Vercel env `NEXT_PUBLIC_API_BASE_URL=https://api.aidwiseai.com/api/v1` for `Production` scope.
- [ ] **Step 2:** Redeploy `main` on Vercel.
- [ ] **Step 3:** Browser smoke: `https://aidwiseai.com/signup` → network tab confirms `XHR` hits `api.aidwiseai.com` not `localhost:8000`.
- [ ] **Step 4:** No commit (env-only).

### Task 17.8 — Brand-aware email-from copy

**Files:** `app/signup/page.tsx`, `app/verify/page.tsx` if it exists.

- [ ] **Step 1:** Import `BRAND` from `@/lib/brand`.
- [ ] **Step 2:** Replace hardcoded "AidwiseAI" strings in the post-signup "Check your email" panel with `{BRAND}`.
- [ ] **Step 3:** Commit (or fold into Task 16.2 brand-hotpatch commit).

### Task 17.9 — Frontend integration tests (Vitest + MSW + RTL)

CLAUDE.md note: "Frontend tests: none yet (no `*.test.*` under `frontend/src`). Coverage relies on Playwright smoke at `tests/e2e/playwright/`." Add at least the invite-redeem path.

**Files:** `frontend/vitest.config.ts` (new), `frontend/src/app/signup/__tests__/page.test.tsx` (new), `frontend/src/test/msw-server.ts` (new).

- [ ] **Step 1:** `cd frontend && bun add -d vitest @vitejs/plugin-react @testing-library/react @testing-library/jest-dom msw jsdom`
- [ ] **Step 2:** `vitest.config.ts`:

```ts
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  test: { environment: "jsdom", setupFiles: ["./src/test/setup.ts"], globals: true },
  resolve: { alias: { "@": path.resolve(__dirname, "src") } },
});
```

- [ ] **Step 3:** Add MSW handler for `POST /api/v1/auth/register` returning `{ access_token, refresh_token, user: { plan: "pro" } }` when payload `invite_code === "AIRU2026"`.
- [ ] **Step 4:** Test cases for `signup/page.tsx`:
  - Renders invite-code field
  - URL `?invite=AIRU2026` pre-fills field
  - Submit without consent → toast error
  - Submit with consent + invite → Pro user, push to `/feed`
- [ ] **Step 5:** Add to `package.json`: `"test": "vitest run", "test:watch": "vitest"`.
- [ ] **Step 6:** Wire to CI in `.github/workflows/ci.yml` `frontend-sanity` job after `bun run build`: `bun run test`.
- [ ] **Step 7:** Commit: `test(frontend): vitest + RTL + MSW infra; invite-redeem path covered`

### Task 17.10 — Docs refresh

**Files:** `docs/scholarai/IMPLEMENTATION_STATUS_REPORT.md`, `frontend/README.md`.

- [ ] **Step 1:** Refresh `IMPLEMENTATION_STATUS_REPORT.md` to reflect: Pakistan pivot complete, Q1 retier shipped, Air-Uni trial launched, alembic head `20260516_0026`, 454+ tests passing.
- [ ] **Step 2:** Update `frontend/README.md` with Pakistan routes, S87 components, new endpoint modules, Vitest commands, BRAND import convention.
- [ ] **Step 3:** Run `python scripts/docs_governance_check.py` → 0 failures.
- [ ] **Step 4:** Commit: `docs: refresh implementation status + frontend README for Pakistan pivot + S87`

### Sprint sequencing

Hard launch-blockers first (in §16's window 2026-05-18):
1. Task 17.3 (consent UI) — PDPB hard requirement
2. Task 17.4 (booth landing) — recommended for in-person walk-by
3. Task 17.7 (Vercel env wired) — trivial after DO custom domain

Post-launch (S88 cycle):
4. Task 17.1 → 17.2 (smoke re-point + CI flag removal)
5. Task 17.6 (Sentry error boundary)
6. Task 17.5 (trial-expired banner) — first wave hits Week 5
7. Task 17.8 (brand copy nit) — fold into 16.2 if not yet committed
8. Task 17.9 (vitest infra) — quality investment
9. Task 17.10 (docs refresh) — hygiene

### Self-Review

- [x] Every CLAUDE.md "Open work" frontend item mapped to a task here.
- [x] Token discipline preserved — all colors via `--color-*`, including `--color-gold` from Task 16.1.
- [x] No backend touches — all consent + privacy endpoints already shipped per S87 backend.
- [x] PDPB §0 + trust-boundary §0.6 honored — privacy panel reads only consent/export/deletion APIs, not B2B tables.
- [x] Accessibility — all interactive controls 44×44; banner uses `role="dialog"`; error boundary client-only.
- [x] Tap-target audit — `h-11` (44px) on every primary CTA in 17.3, 17.4, 17.5, 17.6.

---

*End of §17. Backlog snapshot taken 2026-05-17 03:53 PKT after Air-exhibition gap audit. §16 = booth-day critical path; §17 = everything else frontend.*

