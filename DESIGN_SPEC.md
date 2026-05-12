# ScholarAI Pakistan — Complete Design Specification
> Prototype-ready spec for every screen, component, copy, and interaction.
> Target: Pakistani MS/PhD applicants. Competitor to beat: GoScholar.ai.
> Brand: **ScholarAI Pakistan** (not GrantPath — fix this everywhere).

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
12. [Shared Components](#12-shared-components)
13. [Screen Inventory](#13-screen-inventory)

---

## 1. Design System

### 1.1 Color Palette

```
-- Backgrounds --
--paper:         #F7F5F0   (primary background — warm off-white)
--paper-warm:    #F1EDE4   (hover states, section backgrounds)
--paper-dim:     #E7E1D5   (borders, dividers on white)
--paper-white:   #FFFDF9   (card backgrounds, input backgrounds)

-- Ink (Text) --
--ink:           #0C1117   (primary text — near-black navy)
--ink-strong:    #1B2633   (headings, emphasis)
--ink-muted:     #334155   (body text, secondary text)
--ink-subtle:    #64748B   (labels, captions, placeholders)

-- Semantic --
--validated:     #426B5A   (verified facts, success, eligibility confirmed)
--validated-soft:#DDE9E2   (validated background tint)
--caution:       #B7791F   (warnings, partial eligibility, amber alerts)
--caution-soft:  #F4E7CF   (caution background tint)
--danger:        #B94A48   (errors, red flags, deadlines < 14 days)
--danger-soft:   #F4D8D6   (danger background tint)
--generated:     #2E5B9A   (AI-generated content, links, info)
--generated-soft:#DCE6F4   (generated background tint)
--gold:          #8B6914   (Premium/Elite tier, pricing, demo banner)
--gold-soft:     #F5EDD6   (gold background tint)

-- Borders & Rings --
--border:        rgba(12,17,23,0.08)   (all card/input borders)
--ring:          rgba(46,91,154,0.32)  (focus ring — blue)
```

### 1.2 Typography

```
Display font:   Sora       — weights 500, 600, 700  (all headings, hero text)
Body font:      IBM Plex Sans — weights 400, 500, 600 (all body, UI text)
Mono font:      IBM Plex Mono — weights 400, 500     (data, route labels, code)

Type scale:
--text-xs:    11px / line-height 1.4
--text-sm:    13px / line-height 1.5
--text-base:  15px / line-height 1.6  ← default body
--text-md:    17px / line-height 1.5
--text-lg:    20px / line-height 1.4
--text-xl:    24px / line-height 1.3
--text-2xl:   30px / line-height 1.25
--text-3xl:   38px / line-height 1.2
--text-4xl:   48px / line-height 1.15
--text-hero:  56px / line-height 1.1  (landing hero only)
```

### 1.3 Spacing & Radius

```
Spacing scale: 4, 8, 12, 16, 20, 24, 32, 40, 48, 64, 80, 96px

Border radius:
--radius-sm:    8px    (badges, chips, small buttons)
--radius-input: 10px   (inputs, selects)
--radius-btn:   10px   (buttons)
--radius-card:  16px   (cards)
--radius-panel: 20px   (panels, modals, large cards)
--radius-hero:  24px   (hero card, large display elements)
```

### 1.4 Shadows

```
--shadow-quiet: 0 2px 8px rgba(12,17,23,0.04)    (inactive cards)
--shadow-soft:  0 8px 24px rgba(12,17,23,0.07)   (hover cards, modals)
--shadow-lifted:0 16px 48px rgba(12,17,23,0.10)  (active panels, dropdowns)
```

### 1.5 Buttons

**Primary** — `bg: #0C1117 (ink)`, `text: #FFFDF9`, `radius: 10px`, `height: 44px`, `padding: 0 20px`
- Hover: `bg: #1B2633` + `shadow-soft`
- Active: `bg: #0C1117` scale(0.98)
- Disabled: `opacity: 0.4`, `cursor: not-allowed`

**Secondary** — `bg: paper-white`, `border: 1px solid border-color`, `text: ink`, `height: 44px`
- Hover: `bg: paper-warm`

**Ghost** — `bg: transparent`, `text: ink-muted`, `no border`
- Hover: `bg: paper-warm`

**Validated** — `bg: validated`, `text: white`, `height: 44px`

**Danger** — `bg: danger`, `text: white`, `height: 44px`

**Gold/Premium** — `bg: gold`, `text: white`, `height: 44px` (used on upgrade CTAs)

**Icon Button** — `44×44px`, `radius: 10px`, uses ghost or secondary style

### 1.6 Form Inputs

```
Height:         44px
Background:     paper-white
Border:         1px solid --border
Border-radius:  10px
Padding:        0 14px
Font:           15px IBM Plex Sans
Color:          ink
Placeholder:    ink-subtle

Focus:   border-color: generated, box-shadow: 0 0 0 3px --ring
Error:   border-color: danger, bg: danger-soft (10% tint)
Valid:   border-color: validated (optional)
```

### 1.7 Cards

```
Background:    paper-white
Border:        1px solid --border
Border-radius: 16px
Padding:       24px
Shadow:        shadow-quiet

Hover (interactive cards):
  shadow: shadow-soft
  border-color: rgba(12,17,23,0.14)
  transform: translateY(-1px)
  transition: 150ms ease
```

### 1.8 Badges & Chips

```
Padding:  2px 10px
Radius:   99px (pill)
Font:     11.5px, weight 600, uppercase, letter-spacing 0.04em

Variants:
  neutral:   bg paper-warm,    text ink-muted
  validated: bg validated-soft, text validated
  caution:   bg caution-soft,  text caution
  danger:    bg danger-soft,   text danger
  info:      bg generated-soft, text generated
  gold:      bg gold-soft,     text gold
```

### 1.9 Left-Border Stripes (Content Partitioning)

Used to distinguish validated facts vs AI-generated content:

```
.validated-stripe:
  border-left: 3px solid validated (#426B5A)
  background: validated-soft (#DDE9E2)
  padding: 12px 16px
  border-radius: 0 10px 10px 0

.generated-stripe:
  border-left: 3px solid generated (#2E5B9A)
  background: generated-soft (#DCE6F4)
  padding: 12px 16px
  border-radius: 0 10px 10px 0
  // Always shows Sparkles icon (Lucide) + "AI-generated" label

.caution-stripe:
  border-left: 3px solid caution (#B7791F)
  background: caution-soft (#F4E7CF)
  padding: 12px 16px
  border-radius: 0 10px 10px 0
```

### 1.10 Icons

Use **Lucide** icons only. No emoji in UI chrome. Size: 16px (inline), 20px (buttons), 24px (section headers).

Key icons used:
- `Search` — search bar
- `GraduationCap` — scholarships, programs
- `MapPin` — country/location
- `Calendar` — deadlines
- `CheckCircle` — eligibility confirmed
- `AlertTriangle` — warnings, red flags
- `Lock` — gated/freemium content
- `Sparkles` — AI-generated content
- `FileText` — documents, SOP
- `Mic` — interview practice
- `Trophy` — scholarship awards
- `ArrowRight` — CTAs, navigation
- `ChevronRight` — secondary nav
- `X` — close, dismiss
- `Plus` — add item
- `Grip` — drag handle (kanban)

---

## 2. Global Shell & Navigation

### 2.1 AppShell Layout

```
┌──────────────────────────────────────────────────────┐
│ TopBar (height: 56px, sticky, bg: paper-white,       │
│         border-bottom: 1px solid --border)           │
├──────────┬───────────────────────────────────────────┤
│ Sidebar  │  Main Content Area                        │
│ (240px,  │  (bg: paper, padding: 32px 40px)          │
│  sticky) │  max-width: 960px, margin: 0 auto         │
│          │                                           │
│          │                                           │
└──────────┴───────────────────────────────────────────┘

Mobile (< 768px):
- Sidebar hidden, replaced by bottom tab bar (5 tabs)
- TopBar shows hamburger icon → full-screen overlay nav
- Main content: padding 20px 16px
```

### 2.2 Sidebar

**Header (top of sidebar):**
```
[SA logo mark — 28px, bg ink, rounded 8px] ScholarAI Pakistan
                                            (14px, font-display, weight 700)
```

**Navigation sections (student role):**

```
EXPLORE
  [GraduationCap]  My Matches          → /feed
  [Search]         Find Scholarships   → /dashboard/scholarships/match
  [BookOpen]       Browse All          → /discover

APPLICATIONS
  [LayoutDashboard] Tracker            → /dashboard/tracker
  [FileText]        SOP Builder        → /dashboard/documents/sop
  [Mic]             Visa Practice      → /dashboard/interview

ACCOUNT
  [User]            Profile            → /profile
  [Settings]        Settings           → /settings

UPGRADE (only for free/pro tier)
  [Star]            Go Elite           → /upgrade
                    (gold color, gold-soft bg)
```

Active state: `bg: paper-warm`, `border-left: 2px solid ink`, `text: ink (bold 600)`
Hover state: `bg: paper-warm`, `text: ink`
Default: `text: ink-muted`

**Footer of sidebar:**
```
[Avatar initials 32px]  Zara Khan
                        student@example.com (11px, ink-subtle)
[LogOut icon]  Sign out (ghost button, danger color on hover)
```

### 2.3 TopBar

```
Left:    [Search icon]  Search scholarships...  (press / to focus)
                        Input: 320px wide, height 36px, radius 99px
                        bg: paper-warm, border: 1px solid --border

Center:  (empty on student, page title on admin)

Right:   [Bell icon - admin only with alert badge]
         [Avatar 32px circle with initials]  Name (14px) ↓ dropdown
```

**Avatar dropdown:**
```
Zara Khan
student@example.com
──────────────────
Profile
Settings
──────────────────
Sign out
```

### 2.4 Mobile Bottom Tab Bar

```
[Home]  [Search]  [Tracker]  [Interview]  [Profile]
 Feed    Match     Tracker    Visa Prep    Profile

Active tab: ink color + 2px top border
Inactive: ink-subtle
Height: 60px, bg: paper-white, border-top: 1px solid --border
Safe area padding bottom for iOS notch
```

### 2.5 Demo Mode Banner

Shown when `user.plan === 'elite'` AND demo mode. **Gold color. Sticky below TopBar.**

```
┌─────────────────────────────────────────────────────────────────────┐
│ ★  Demo mode — all Elite features unlocked.                         │
│    In production: Pro PKR 2,499/mo · Elite PKR 7,999/mo             │
│                                              [×] dismiss            │
└─────────────────────────────────────────────────────────────────────┘

Style:
  bg: gold-soft (#F5EDD6)
  border-bottom: 1px solid rgba(139,105,20,0.2)
  text: gold (#8B6914), font-size: 13px, weight 500
  padding: 10px 24px
  [×] button: ghost, 32×32px, icon-only
```

---

## 3. Landing Page

**Route:** `/`  
**Layout:** Full-width, no sidebar. Max-width sections: 1100px centered.  
**Goal:** Convert Pakistani students to signup. Single CTA: "Find My Scholarships →"

---

### 3.1 Navigation Bar (Landing)

```
┌──────────────────────────────────────────────────────────────────┐
│ [SA]  ScholarAI Pakistan      How it works  Features  Pricing    │
│                                                    [Sign in]     │
│                                         [Find My Scholarships →] │
└──────────────────────────────────────────────────────────────────┘

Style:
  bg: paper-white/95 with backdrop-blur
  border-bottom: 1px solid --border
  height: 64px
  sticky on scroll
  Logo: 32px mark + "ScholarAI Pakistan" in font-display weight 700

Nav links: 14px, ink-muted, hover: ink
Sign in: secondary button, height 36px
CTA button: primary button (ink), height 36px, "Find My Scholarships →"

Mobile: logo + hamburger only. Hamburger → full-screen overlay.
```

---

### 3.2 Hero Section

**Layout:** 2-column on desktop (text left, preview card right). Single column on mobile.

```
─────────────────────────────────────────────────────────────
LEFT COLUMN (55%)

  Eyebrow tag:
  ┌────────────────────────────────┐
  │ 🇵🇰  Built for Pakistani students │  ← badge: paper-warm bg, ink text, 13px
  └────────────────────────────────┘

  Headline (font-display, 52px, weight 700, ink, line-height 1.1):
  "Find fully-funded
  programs abroad.
  No consultant.
  No fees."

  Subheadline (18px, ink-muted, max-width 440px, line-height 1.6):
  "ScholarAI matches Pakistani students to scholarships
  they actually qualify for — based on CGPA, IELTS,
  field, and target country. Then helps them apply."

  Speed promise (14px, ink-subtle, margin-top: 8px):
  "Get your matches in under 60 seconds."

  CTA Group (margin-top: 32px, gap: 12px, flex-row):
  ┌──────────────────────────────────┐
  │  Find My Scholarships →          │  ← Primary button, height 52px, font-size 16px
  └──────────────────────────────────┘
  Already have an account? Sign in   ← 13px link, ink-subtle

  Social proof strip (margin-top: 40px, flex-row, gap: 24px):
  [CheckCircle green]  Free forever — no consultant fees
  [CheckCircle green]  Chevening, Fulbright, DAAD and more
  [CheckCircle green]  Visa interview prep included

─────────────────────────────────────────────────────────────
RIGHT COLUMN (45%)

  Hero Preview Card (static, no JS required):
  ┌────────────────────────────────────────────┐
  │ Your AI Match Results          3 of 12 →   │
  │ ─────────────────────────────────────────  │
  │                                            │
  │ ┌──────────────────────────────────────┐   │
  │ │ 🇬🇧  Chevening Scholarship            │   │
  │ │     UK · Fully Funded · Nov 2025    │   │
  │ │                           96% match │   │
  │ │ ✓ CGPA 3.7 qualifies               │   │
  │ │ ✓ IELTS 7.0 meets requirement      │   │
  │ └──────────────────────────────────────┘   │
  │                                            │
  │ ┌──────────────────────────────────────┐   │
  │ │ 🇺🇸  Fulbright Fellowship             │   │
  │ │     USA · Fully Funded · Feb 2026   │   │
  │ │                           91% match │   │
  │ └──────────────────────────────────────┘   │
  │                                            │
  │ ┌──────────────────────────────────────┐   │
  │ │ 🇩🇪  DAAD Scholarship                 │   │
  │ │     Germany · Fully Funded          │   │
  │ │                           87% match │   │
  │ └──────────────────────────────────────┘   │
  │                                            │
  │ ┌──────────────────────────────────────┐   │
  │ │ 🔒  + 9 more matches including       │   │  ← blur/lock card
  │ │     2 closing in 47 days            │   │
  │ │     [Unlock with Pro →]             │   │
  │ └──────────────────────────────────────┘   │
  │                                            │
  │ Profile: NUST · CS · CGPA 3.7 · IELTS 7.0 │
  └────────────────────────────────────────────┘

  Card style:
    bg: paper-white
    border: 1px solid --border
    border-radius: 20px
    padding: 24px
    shadow: shadow-lifted
    max-width: 400px
    Each result card: 
      bg: paper, radius: 12px, padding: 14px 16px
      Match % in validated-green (bold, right-aligned)
      Country flag emoji + name (14px, weight 600)
      Details line: 12px, ink-subtle
      Checkmarks in validated color (✓)
    Lock card:
      bg: paper-warm
      border: 1px dashed --border
      Lock icon (Lucide) + text blurred
      [Unlock with Pro →] gold button, height 32px
```

---

### 3.3 Stats Bar

**Full-width section, bg: ink (#0C1117), padding: 60px 40px**

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│    150,000+              62%              0                      │
│  Pakistani students   want to study    dedicated AI platforms    │
│  studying abroad      abroad           for Pakistani students    │
│                                        (until now)               │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘

Style:
  3-column grid, centered
  Numbers: 48px, font-display, weight 700, color white
  Labels: 14px, color rgba(255,255,255,0.6), max-width 160px, centered
  Divider lines between columns: 1px rgba(255,255,255,0.1)
```

---

### 3.4 Problem Section

**Layout:** Section heading + 4-card grid  
**Heading:** "The study abroad process is broken for Pakistani students"  
**Subheading:** "Every year, talented students miss life-changing opportunities because of the same four problems."

```
┌────────────────────────────────────────────────────────────────┐
│  CARD 1                    CARD 2                              │
│  💸 Too Expensive           🌀 Information Chaos               │
│                                                                │
│  Consultants charge         WhatsApp groups, random            │
│  PKR 40,000–150,000+.       YouTube videos, outdated           │
│  Most give generic          blogs. No single source            │
│  advice. One wrong          of truth for Pakistani             │
│  decision costs months.     applicants.                        │
│                                                                │
│  CARD 3                    CARD 4                              │
│  ❌ Visa Rejection Fear      💱 Currency Reality               │
│                                                                │
│  Pakistan has some of       With 1 USD = 278+ PKR,             │
│  the world's highest        every wrong application            │
│  student visa refusal       fee, wrong consultant,             │
│  rates — yet no platform    and wasted test attempt            │
│  helps you prepare.         is expensive.                      │
└────────────────────────────────────────────────────────────────┘

Card style:
  bg: paper-white
  border: 1px solid --border
  border-radius: 16px
  padding: 28px
  Icon: 32px, caution-soft bg, caution color, radius 10px
  Heading: 16px, weight 600, ink, margin-top 16px
  Body: 14px, ink-muted, line-height 1.6
```

---

### 3.5 How It Works Section

**Heading:** "From profile to visa approval — one platform, every step."  
**4 horizontal steps (desktop) / vertical cards (mobile)**

```
STEP 1                   STEP 2                   STEP 3                  STEP 4
Build Your Profile        Get Matched              Track & Apply           Ace the Visa

Fill your CGPA, IELTS,    AI matches you to        Kanban board tracks     Practice UK, USA,
target countries, and     scholarships and          every application.      Canada, Germany
field of study.           universities you          Pakistan-specific       visa interviews
Takes under 3 minutes.    actually qualify for.     checklist included.     with AI feedback.

[Profile icon]            [GraduationCap icon]      [LayoutDashboard]       [Mic icon]
                          → LIVE                    → LIVE                  → LIVE

Step number: large serif "01" "02" "03" "04" in ink-subtle
Connector lines between steps: 1px dashed, ink-subtle / paper-dim
Status badge: "LIVE" in validated-soft/validated color, 10px
```

---

### 3.6 Featured Scholarships Section

**Heading:** "Top scholarships Pakistani students win"  
**Subheading:** "These are fully funded. Real deadlines. Available to you."

**5-column scrollable card row (horizontal scroll on mobile)**

```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ 🇬🇧               │  │ 🇺🇸               │  │ 🇩🇪               │
│ Chevening       │  │ Fulbright       │  │ DAAD            │
│ Scholarship     │  │ Fellowship      │  │ Scholarship     │
│                 │  │                 │  │                 │
│ FULLY FUNDED    │  │ FULLY FUNDED    │  │ FULLY FUNDED    │
│ ~£18,000/year   │  │ ~$35,000/year   │  │ €934/month      │
│                 │  │                 │  │                 │
│ Deadline        │  │ Deadline        │  │ Deadline        │
│ November 2025   │  │ February 2026   │  │ October 2025    │
│                 │  │                 │  │                 │
│ Min CGPA: 3.0   │  │ Min CGPA: 3.0   │  │ Min CGPA: 3.2   │
│ Open to 🇵🇰      │  │ Open to 🇵🇰      │  │ Open to 🇵🇰      │
│                 │  │                 │  │                 │
│ [View Details]  │  │ [View Details]  │  │ [View Details]  │
└─────────────────┘  └─────────────────┘  └─────────────────┘

Also: Commonwealth (🇬🇧) + HEC Overseas (🌍)

Card style:
  bg: paper-white
  border: 1px solid --border
  border-radius: 16px
  padding: 24px 20px
  width: 220px (fixed, horizontal scroll row)
  Country flag: 32px emoji at top
  Name: 15px, weight 600, ink
  FULLY FUNDED badge: validated-soft, validated color
  Amount: 14px, ink-muted
  Deadline label: 12px, ink-subtle; value: 13px, caution if < 60 days
  Min CGPA: 12px, ink-subtle
  "Open to PK" badge: small, validated-soft
  [View Details]: ghost link, 13px, generated color
```

---

### 3.7 Visa Interview Callout

**Full-width section, bg: generated-soft, border-top/bottom: 1px solid rgba(46,91,154,0.15)**

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  [Mic icon 40px, generated color]                                   │
│                                                                     │
│  Practice your visa interview before the real one.                  │
│  (28px, font-display, weight 700, ink)                              │
│                                                                     │
│  GoScholar lists visa prep as "Coming Soon."                        │
│  We built it. UK, USA, Canada, Germany. AI feedback on every        │
│  answer. Red flag detection. Session summary.                       │
│  (15px, ink-muted, max-width 540px, centered)                       │
│                                                                     │
│  [Practice a Visa Interview — Free →]                               │
│  (Primary button, height 48px)                                      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

### 3.8 Pricing Teaser

**Heading:** "Free to start. Upgrade when you're ready."

```
3-column card row: Explorer (Free) | Pro (PKR 2,499/mo) | Elite (PKR 7,999/mo)

Pro card highlighted: gold ring, "Most popular" badge (gold)

Under Pro: "Less than one hour of a consultant's time per month."
Under Elite: "For Pakistani families in the UK or UAE."

[See full pricing →]  link at bottom → /upgrade
```

---

### 3.9 Footer

```
┌────────────────────────────────────────────────────────────────────┐
│                                                                    │
│ [SA Logo]  ScholarAI Pakistan                                      │
│            Making study abroad accessible for Pakistani students.  │
│            Student-only — we don't take money from universities.   │
│                                                                    │
│ Product          Resources           Company                       │
│ Find Scholarships  Scholarship Guide  About                        │
│ Visa Practice      IELTS Tips         Contact                      │
│ SOP Builder        CGPA Converter     Privacy Policy               │
│ Tracker            Test Prep          Terms of Service             │
│                                                                    │
│ ─────────────────────────────────────────────────────────────────  │
│ Are you a university or school? Partner with us →                  │
│ (mailto:partnerships@scholarai.pk)                                 │
│                                                                    │
│ © 2026 ScholarAI Pakistan. All rights reserved.                    │
└────────────────────────────────────────────────────────────────────┘

Style:
  bg: ink (#0C1117)
  All text: rgba(255,255,255,0.6)
  Logo + company name: white
  Column headings: rgba(255,255,255,0.4), 11px, uppercase, letter-spacing 0.1em
  Links: hover rgba(255,255,255,0.9)
  "Partner with us" link: gold color, hover gold lighter
  Divider: 1px rgba(255,255,255,0.08)
```

---

## 4. Signup & Login

### 4.1 Signup Page

**Route:** `/signup`  
**Layout:** Centered single-column card, max-width 420px, vertically centered on page.

```
─────────────────────────────────────────────────────
PAGE BACKGROUND: paper (#F7F5F0)

CARD:
  bg: paper-white
  border: 1px solid --border
  border-radius: 20px
  padding: 40px
  shadow: shadow-lifted

HEADER:
  [SA logo 32px]  centered
  "Create your account"  — 24px, font-display, weight 700, ink, centered
  "Find fully-funded programs that match your profile."
  — 14px, ink-muted, centered, margin-top: 8px

FORM:
  Full name
    Label: "Full name"
    Input: placeholder "Zara Khan"

  Email address
    Label: "Email"
    Input: placeholder "zara@example.com"
    Error state: "Enter a valid email address."

  Password
    Label: "Password"
    Input: type password, placeholder "Min. 8 characters"
    Helper: "At least 8 characters" (12px, ink-subtle)
    Toggle visibility icon (eye/eye-off Lucide)

  [Create account →]  primary button, full-width, height 48px

  Divider: ─────── or ───────

  Sign in with Google (secondary button, full-width, height 44px)
  [Google icon]  Sign up with Google
  (Note: placeholder only — shows "Coming soon" tooltip on hover for FYP)

FOOTER:
  "Already have an account? Sign in →"  13px, centered, link → /login

LEGAL:
  "By creating an account, you agree to our Terms of Service and Privacy Policy."
  11px, ink-subtle, centered, max-width 300px

─────────────────────────────────────────────────────
```

### 4.2 Login Page

**Route:** `/login`

Same card layout as signup. Contents:

```
HEADER:
  [SA logo 32px]  centered
  "Welcome back"  — 24px, font-display, weight 700
  "Sign in to your ScholarAI account."  — 14px, ink-muted

FORM:
  Email address
    Input: placeholder "your@email.com"

  Password
    Input: type password
    Row: "Password" label LEFT | "Forgot password?" link RIGHT (13px, generated)

  [Sign in →]  primary button, full-width, height 48px

  Error state (shown below button):
    danger-soft bg, danger border, danger text
    "Invalid email or password. Try again."

FOOTER:
  "Don't have an account? Sign up →"  13px, centered, link → /signup
```

---

## 5. Onboarding (5 Steps)

**Route:** `/onboarding`  
**Layout:** Centered card, max-width 600px. No sidebar.  
**Goal:** Collect Pakistani-specific profile in under 3 minutes.

### 5.1 Progress Bar (persistent across all steps)

```
TOP OF PAGE (outside card):

Step 1 of 5 — About You               ~3 min left
●──────────────────────────────────  (20% filled)

Progress bar: h 4px, bg paper-dim, filled section bg ink
Step labels: optional, shown on desktop only
Time estimate: 12px, ink-subtle, right-aligned
Step dots: 5 dots, active = ink filled circle, done = ink with checkmark, future = paper-dim
```

### 5.2 Card Wrapper (all steps)

```
CARD:
  bg: paper-white
  border: 1px solid --border
  border-radius: 20px
  padding: 40px 48px
  shadow: shadow-soft
  max-width: 600px, centered

STEP HEADER:
  Step label: "Step 1 of 5" — 11px, uppercase, letter-spacing 0.08em, ink-subtle
  Step title: 26px, font-display, weight 700, ink
  Step description: 15px, ink-muted, max-width 440px

NAVIGATION FOOTER (bottom of card):
  [← Back]  ghost button, left               [Continue →]  primary button, right
  Back: disabled (opacity 0) on Step 1
  Continue disabled only if required field missing (Step 4 only: degree + countries)
  On Step 5: Continue label → "Find My Scholarships →"
```

---

### Step 1: About You

**Title:** "Tell us about yourself"  
**Description:** "We'll use this to personalise your scholarship matches."

```
FIELDS:

1. Full name *
   Input, placeholder: "Zara Khan"
   Required

2. City of origin
   Select dropdown options:
   Karachi, Lahore, Islamabad, Rawalpindi, Faisalabad, Peshawar,
   Quetta, Multan, Sialkot, Hyderabad, Other
   Placeholder: "Select your city"

3. Pakistani university
   Searchable dropdown (type to filter):
   Pre-loaded list:
   - NUST — National University of Sciences and Technology
   - LUMS — Lahore University of Management Sciences
   - FAST-NUCES (all campuses)
   - UET Lahore — University of Engineering and Technology
   - IBA Karachi — Institute of Business Administration
   - QAU — Quaid-i-Azam University
   - COMSATS University
   - UCP — University of Central Punjab
   - NED University
   - UMT — University of Management and Technology
   - BNU — Beaconhouse National University
   - Air University
   - GIKI — Ghulam Ishaq Khan Institute
   - PIEAS — Pakistan Institute of Engineering and Applied Sciences
   - Forman Christian College University
   - University of Karachi
   - University of the Punjab
   - SZABIST
   - Other (free text)
   Placeholder: "Search your university..."
   If "Other" selected: text input appears below

4. Degree subject
   Input (free text), placeholder: "e.g. Computer Science, Data Science, Electrical Engineering"
   Helper text: "Your undergraduate major or specialisation"

5. Graduation year
   Select: 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025 (expected)
   Placeholder: "Select year"

AUTOSAVE INDICATOR (top-right of card):
  "Draft saved" — 11px, ink-subtle, shows 2s after any field change
```

---

### Step 2: Academic Record

**Title:** "Your academic record"  
**Description:** "We use this to check your eligibility against scholarship requirements."

```
FIELDS:

1. CGPA
   Two inline inputs:
   [_3.7_]  out of  [_4.0_]
   Left: number input, 0.0–4.0, placeholder "3.7"
   Right: select — 4.0 (Standard) | 4.0 HEC | 5.0 | 10.0 | 100
   Default right: "4.0 (Standard)"

   LIVE CONVERSION (appears 300ms after CGPA input, below the fields):
   ┌───────────────────────────────────────────────────────┐
   │  ✓  Your 3.7 CGPA is approximately a 3.7 US GPA       │  ← validated-stripe
   │     Equivalent to First Class Honours (UK)            │
   └───────────────────────────────────────────────────────┘
   (Only shows for 4.0 scale inputs)

2. HEC degree level
   Radio cards (3 options, horizontal):
   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
   │  Bachelor's  │  │   Master's   │  │    MPhil     │
   │    (BS/BE)   │  │    (MS/MBA)  │  │              │
   └──────────────┘  └──────────────┘  └──────────────┘
   Active: ink border 2px, ink bg (subtle), checkmark icon
   Default: Bachelor's

3. Research publications
   Toggle switch: "I have research publications"
   Off by default.
   When ON: reveals number input
   "How many peer-reviewed publications?"
   Input: number, min 0, placeholder "1"
   Helper: "Include conference papers and journal articles."

LAYOUT NOTE:
  CGPA row: 2 inputs side by side (inline)
  Full-width fields otherwise
  Live conversion card: full-width, below CGPA inputs
```

---

### Step 3: Test Scores

**Title:** "Test scores"  
**Description:** "All optional — add what you have. If you haven't taken a test yet, skip it."

```
FIELDS:

1. IELTS Overall Score
   Number input, range 0.0–9.0, step 0.5, placeholder "7.0"
   Helper: "Leave blank if not taken yet"
   Below input (when filled): 
   ┌──────────────────────────────────────────────────────────┐
   │  ✓  7.0 meets the requirement for most UK/Germany/Canada │
   │     scholarships in our database.                        │
   └──────────────────────────────────────────────────────────┘
   (validated-stripe, 12px)

2. TOEFL iBT Score
   Number input, range 0–120, placeholder "100"
   Helper: "Leave blank if not taken yet"

3. GRE (optional section header)

   GRE Quant
   Number input, range 130–170, placeholder "162"

   GRE Verbal
   Number input, range 130–170, placeholder "155"

4. GRE waiver toggle
   "I need programs that don't require GRE"
   Toggle switch, OFF by default
   When ON: shows note "We'll filter out GRE-required programs in your matches."

SKIP HINT (below all fields):
  "Not sure about your scores? You can update these later from your Profile."
  12px, ink-subtle, with link to /profile
```

---

### Step 4: Your Goal

**Title:** "What's your goal?"  
**Description:** "This is what we rank scholarships against. Choose as many countries and fields as apply."

```
FIELDS:

1. Target degree *  (required)
   Radio cards (3 options):
   ┌───────────┐  ┌───────────┐  ┌───────────┐
   │    MS     │  │    PhD    │  │    MBA    │
   │  Masters  │  │ Doctorate │  │  Business │
   └───────────┘  └───────────┘  └───────────┘

2. Target countries *  (required, multi-select)
   LARGE FLAG CARDS — 4 per row on desktop, 2 per row on mobile
   
   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
   │    🇬🇧    │  │    🇺🇸    │  │    🇨🇦    │  │    🇩🇪    │
   │    UK    │  │   USA    │  │  Canada  │  │ Germany  │
   └──────────┘  └──────────┘  └──────────┘  └──────────┘
   ┌──────────┐  ┌──────────┐  ┌──────────┐
   │    🇦🇺    │  │    🇮🇪    │  │    🇳🇱    │
   │Australia │  │ Ireland  │  │Netherlands│
   └──────────┘  └──────────┘  └──────────┘
   
   Selected state: ink background (20% opacity), ink border 2px, checkmark overlay
   Unselected: paper-white, --border
   Card: 100×80px, centered flag (32px emoji), country name (12px, weight 600)
   Validation: "Select at least one country to continue."

3. Target field(s)  (multi-select chip group)
   ┌──────────────┐ ┌──────────┐ ┌──────────────────┐ ┌────────────┐
   │ Computer     │ │  AI/ML   │ │  Data Science /  │ │  Electrical│
   │ Science      │ │          │ │  Analytics       │ │  Eng.      │
   └──────────────┘ └──────────┘ └──────────────────┘ └────────────┘
   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
   │ Business │ │Engineering│ │ Medicine │ │  Other   │
   └──────────┘ └──────────┘ └──────────┘ └──────────┘
   
   Chip style: height 36px, padding 0 14px, radius 99px
   Selected: bg ink, text paper-white
   Unselected: bg paper-warm, border --border, text ink-muted

4. Funding requirement
   Radio cards (2 options):
   ┌──────────────────────────┐   ┌──────────────────────────┐
   │  Fully funded only       │   │  Partial funding OK       │
   │  I need full scholarship │   │  I can contribute some   │
   └──────────────────────────┘   └──────────────────────────┘

5. Target intake
   Select dropdown:
   January 2025, September 2025, January 2026, September 2026, Flexible
   Placeholder: "When do you want to start?"
```

---

### Step 5: Financial Context

**Title:** "A few quick questions"  
**Description:** "This helps us surface relevant support options. All optional."

```
FIELDS (3 toggle rows):

1. ─────────────────────────────────────────────────────────
   Can you afford application fees?                [Toggle]
   "Most universities charge $50–150 per application."
   ─────────────────────────────────────────────────────────

2. ─────────────────────────────────────────────────────────
   Does your family have savings for a bank statement?  [Toggle]
   "Required for UK/USA/Canada visa applications."
   ─────────────────────────────────────────────────────────

3. ─────────────────────────────────────────────────────────
   Do you need a GRE fee waiver?               [Toggle]
   "Some universities offer waivers on request."
   ─────────────────────────────────────────────────────────

Toggle style:
  Row: full-width, bg paper-white, border 1px solid --border, radius 12px
  padding: 16px 20px
  Label: 15px, weight 500, ink
  Sub-label: 13px, ink-subtle, margin-top 2px
  Toggle: right-aligned, 44×24px pill switch

SKIP BUTTON:
  "Skip this step →" — ghost button, right of navigation footer, 13px

BOTTOM NOTE:
  "You can update any of these later from your Profile."
  12px, ink-subtle, centered

CTA BUTTON TEXT (overrides "Continue →"):
  "Find My Scholarships →"
  Primary button, height 52px, font-size 16px, full-width
```

---

## 6. Dashboard (Home)

**Route:** `/feed`  
**Role:** student

### 6.1 Page Header

```
"Hi, Zara."   — 32px, font-display, weight 700, ink
"You have 3 deadlines in the next 60 days."  — 16px, ink-muted
```

### 6.2 Action Grid (Primary UI)

**2×2 grid. Each card navigates to a key feature.**

```
┌─────────────────────────────┐  ┌─────────────────────────────┐
│                             │  │                             │
│  [GraduationCap 24px]       │  │  [Mic 24px]                 │
│                             │  │                             │
│  Find Scholarships          │  │  Practice Visa Interview    │
│  Get matched to programmes  │  │  UK, USA, Canada, Germany.  │
│  you actually qualify for.  │  │  AI feedback on every       │
│                             │  │  answer.                    │
│              [ArrowRight →] │  │              [ArrowRight →] │
└─────────────────────────────┘  └─────────────────────────────┘

┌─────────────────────────────┐  ┌─────────────────────────────┐
│                             │  │                             │
│  [FileText 24px]            │  │  [LayoutDashboard 24px]     │
│                             │  │                             │
│  Write Your SOP             │  │  Application Tracker        │
│  AI-assisted, Pakistani     │  │  Track deadlines and        │
│  context, Chevening-ready.  │  │  document checklists.       │
│                             │  │                             │
│              [ArrowRight →] │  │              [ArrowRight →] │
└─────────────────────────────┘  └─────────────────────────────┘

Card style:
  bg: paper-white
  border: 1px solid --border
  border-radius: 16px
  padding: 24px
  min-height: 160px
  hover: shadow-soft, translateY(-2px), transition 150ms
  Icon: 24px, in rounded bg (10px radius, paper-warm), padding 10px
  Title: 16px, weight 600, ink, margin-top 12px
  Description: 13px, ink-muted, margin-top 4px, line-height 1.5
  [ArrowRight]: 18px, ink-subtle, bottom-right aligned

Mobile: 1-column, full-width cards
```

---

### 6.3 Incomplete Profile Nudge

**Show only if:** profile is missing `target_countries` or `cgpa_value`

```
┌───────────────────────────────────────────────────────────────┐
│  [AlertCircle caution-color]                                  │
│  Complete your profile to get accurate matches                │
│  "You're missing IELTS score and target countries."           │
│                              [Complete profile →]             │
└───────────────────────────────────────────────────────────────┘

Style:
  bg: caution-soft
  border: 1px solid rgba(183,121,31,0.2)
  border-radius: 12px
  padding: 16px 20px
  text: caution
  CTA: ghost button, caution color
  Shown ABOVE action grid
```

---

### 6.4 Recent Matches

**Heading:** "Your top matches" (18px, weight 600)  
**Show top 3 from** `POST /recommendations`

Each match card (compact):

```
┌────────────────────────────────────────────────────────────┐
│ 🇬🇧  Chevening Scholarship                  96% match       │
│      UK · Fully Funded · Deadline: Nov 2025               │
│      ✓ CGPA 3.7 qualifies  ✓ IELTS 7.0 meets req.        │
│                                    [View] [+ Tracker]     │
└────────────────────────────────────────────────────────────┘

Style:
  bg: paper-white, border --border, radius 12px, padding 16px 20px
  Match %: right-aligned, validated color, 15px weight 700
  Country flag + name: 14px weight 600
  Details row: 12px ink-subtle
  Checkmarks: validated color, 12px
  [View]: ghost link button, 12px
  [+ Tracker]: secondary button, 12px, height 32px
```

**Below cards:**  
`[See all matches →]` link → `/dashboard/scholarships/match`

---

### 6.5 Tracker Summary Widget

**Show only if:** user has tracker items. Otherwise show CTA.

```
Heading: "Applications in progress" (16px, weight 600)

Horizontal stage count strip:
  Researching (2) | Preparing (1) | Applied (0) | Decision (0)
  Each: 13px, weight 500, ink-muted, "|" divider

Below strip: list of items with deadline within 30 days
┌────────────────────────────────────────────────────────────┐
│ ⚠ Chevening (UK)                      deadline in 12 days  │
│   3 documents still missing            [Go to tracker →]   │
└────────────────────────────────────────────────────────────┘

  Color: danger text, danger-soft bg, radius 10px, padding 12px 16px

[Go to tracker →]  link → /dashboard/tracker

Empty state (no tracker items):
  "No applications tracked yet."
  "Add scholarships from your matches to start tracking deadlines."
  [Add from matches →]  ghost CTA → /dashboard/scholarships/match
```

---

## 7. Scholarship Finder

**Route:** `/dashboard/scholarships/match`  
**Method:** Auto-runs `POST /scholarships/match` on page load from user profile.

### 7.1 Page Header

```
"Scholarships matched to your profile"  — 28px, font-display, weight 700

Subline: "Based on: NUST · CS · CGPA 3.7 · IELTS 7.0 · UK, Germany · Fully funded"
  13px, ink-subtle
  [Edit profile] — ghost link, 13px → /profile

Summary bar (full-width, bg paper-white, border, radius 12px, padding 16px 20px):
  ┌───────────────────────────────────────────────────────────────┐
  │  4 fully funded scholarships match your profile.              │
  │  9 more matches available with Pro — including 2 closing      │
  │  in 47 days.                          [Upgrade to Pro →]      │
  └───────────────────────────────────────────────────────────────┘
  bg: gold-soft, border: rgba(139,105,20,0.2), text: gold
  [Upgrade to Pro →]: gold button, height 32px
```

### 7.2 Tabs

```
[  Eligible (4)  ]  [  Partially Eligible (3)  ]  [  Stretch (5)  ]

Tab style:
  Active: ink text, 2px border-bottom ink, weight 600
  Inactive: ink-subtle
  Count in parentheses: badge style, neutral
  Tab bar: border-bottom 1px --border
```

### 7.3 Match Card (Eligible Tab)

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  🇬🇧  Chevening Scholarship                    [FULLY FUNDED]       │
│       UK Foreign Commonwealth & Development Office                 │
│                                                                     │
│  ──────────────────────────────────────────────────────────────     │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ ✓  Your 3.7 CGPA from NUST is equivalent to a 3.7 US GPA.  │    │  ← validated-stripe
│  │    Qualifies for programs requiring min 3.0.                │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  [Calendar]  Deadline in 47 days  (Nov 2025)    [£18,000/year]      │
│  [CheckCircle]  IELTS 7.0 ✓   [CheckCircle]  Min CGPA 3.0 ✓       │
│  [GraduationCap]  Masters   [Globe]  All fields                     │
│                                                                     │
│  Match reason:                                                      │
│  "Matches your CGPA, IELTS score, CS focus, and UK target."         │
│  (13px, ink-muted)                                                  │
│                                                                     │
│  ────────────────────────────────────────────────────────────────   │
│  [View Details]  (secondary btn, h 36px)    [+ Add to Tracker]      │
│                              (primary btn, h 36px)                  │
└─────────────────────────────────────────────────────────────────────┘

Card style:
  bg: paper-white
  border: 1px solid --border
  border-radius: 16px
  padding: 24px
  
Deadline urgency colors:
  > 60 days: deadline text ink-muted (neutral)
  31–60 days: deadline text caution (#B7791F)
  ≤ 30 days: deadline text danger (#B94A48), left border 3px danger
  ≤ 14 days: red border + danger-soft background tint on card

"+ Add to Tracker" button:
  When clicked: button transforms to "✓ Added" (validated color, disabled)
  Optimistic update — no reload needed
```

### 7.4 Partially Eligible Card

Same as above, but with a caution stripe instead of validated:

```
┌─────────────────────────────────────────────────────────────────┐
│ ⚠  Missing: IELTS score.                                        │  ← caution-stripe
│    Add your IELTS score to qualify fully. [Update profile →]    │
└─────────────────────────────────────────────────────────────────┘
```

### 7.5 Freemium Blur (Results 4+ for free tier)

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  [BLURRED CONTENT — css: blur(5px) + overlay]                       │
│  🔒  University of Manchester Scholarship                           │  ← visible through blur
│      UK · Fully Funded                                              │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  [Lock icon 20px]                                           │    │  ← overlay card, centered
│  │                                                             │    │
│  │  9 more matches — including 2 fully funded                  │    │
│  │  closing in 47 days.                                        │    │
│  │                                                             │    │
│  │  [Upgrade to Pro — PKR 2,499/mo →]  (gold button)          │    │
│  │  No consultant fees. Cancel anytime.                        │    │  ← 12px, ink-subtle
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

Overlay:
  Position: absolute, inset 0
  bg: rgba(247,245,240,0.85)
  backdrop-filter: blur(5px)
  display: flex, align-items: center, justify-content: center
  
Inner card:
  bg: paper-white
  border: 1px solid gold-soft
  border-radius: 14px
  padding: 24px
  text-align: center
  max-width: 360px
  Lock icon: 28px, gold color
  Heading: 16px, weight 600, ink
  Body: 13px, ink-muted
  Gold button: full-width, height 44px
```

---

## 8. Application Tracker (Kanban)

**Route:** `/dashboard/tracker`

### 8.1 Page Header

```
"Application Tracker"  — 28px, font-display, weight 700

"Track every application. Never miss a deadline."  — 16px, ink-muted

[+ Add Application]  primary button, top-right, height 40px, Plus icon
```

### 8.2 Deadline Alert Banner

**Show only when:** any item has deadline ≤ 30 days AND checklist < 100%

```
┌────────────────────────────────────────────────────────────────────┐
│ [AlertTriangle danger-color]  Chevening deadline in 12 days —      │
│ 3 documents still missing.              [Go to card →]  [×]        │
└────────────────────────────────────────────────────────────────────┘

Style:
  bg: danger-soft
  border: 1px solid rgba(185,74,72,0.2)
  border-radius: 12px
  padding: 14px 20px
  margin-bottom: 24px
  text: danger (#B94A48), 14px, weight 500
  [Go to card →]: danger ghost button
  [×]: 28px icon button, dismiss for session
```

### 8.3 Kanban Board

**6 columns. Horizontal scroll on mobile (columns: 280px fixed width).**

```
COLUMN STRUCTURE (each column):

┌──────────────────────────────────────┐
│ Researching              [count: 2]  │   ← Column header
│ ─────────────────────────────────── │
│                                      │
│  [CARD]                              │
│  [CARD]                              │
│                                      │
│  + Add here (dashed ghost button)    │
└──────────────────────────────────────┘

Column header style:
  bg: paper-warm
  border-radius: 12px 12px 0 0
  padding: 12px 16px
  font: 13px, weight 700, ink, uppercase, letter-spacing 0.05em
  Count: 20×20px circle, bg ink, text white, 11px, radius 99px

Column body:
  bg: paper (#F7F5F0)
  border: 1px solid --border
  border-top: none
  border-radius: 0 0 12px 12px
  padding: 12px
  min-height: 400px
  overflow-y: auto

Columns (left to right):
  1. Researching
  2. Preparing Documents
  3. Applied
  4. Interview / Test
  5. Decision
  6. Accepted (bg: validated-soft tint on column header)
```

### 8.4 Tracker Card

```
┌───────────────────────────────────────────────┐
│  [Grip icon — drag handle, left edge]         │
│                                               │
│  🇬🇧  MS Computer Science                     │
│       University of Manchester                │
│                                               │
│  ────────────────────────────────────────     │
│  [Calendar]  47 days         [Docs] 5 / 13    │
│                                               │
│  [Progress bar: 5/13 filled]                  │
│                                               │
│  [Expand checklist ∨]                         │
└───────────────────────────────────────────────┘

Card style:
  bg: paper-white
  border: 1px solid --border
  border-radius: 12px
  padding: 16px
  margin-bottom: 8px
  cursor: grab (drag handle)
  
  Left border urgency:
    ≤ 14 days: 3px solid danger
    15–30 days: 3px solid danger (lighter)
    31–60 days: 3px solid caution
    > 60 days: no colored border
    
  University name: 14px, weight 600, ink
  Program: 13px, ink-muted
  Country flag + name: inline, 12px
  Deadline: 12px, color matches urgency
  "X / 13 docs": 12px, validated if 13/13, caution if <7, danger if <3
  Progress bar: h 4px, bg paper-dim, filled = validated
  
  Drag handle: [Grip] icon, left side, 16px, ink-subtle, only visible on hover
```

### 8.5 Checklist Expansion

Clicking `[Expand checklist ∨]` or clicking the card:

```
EXPANDED (below card body, animated slide-down):

Document Checklist (12px header, ink-subtle, uppercase):

  [ ] Academic Transcripts
  [ ] Degree Certificate
  [ ] IELTS Certificate
  [ ] GRE Score Report
  [ ] Statement of Purpose (Draft)
  [ ] Statement of Purpose (Final)
  [ ] CV / Resume
  [ ] Letter of Recommendation 1
  [ ] Letter of Recommendation 2
  [ ] Letter of Recommendation 3
  [ ] Bank Statement (proof of funds)
  ┌────────────────────────────────────────────────────────┐
  │ HEC Degree Attestation  [ⓘ]                           │  ← highlighted row
  │ Required for UK and Germany applications               │
  └────────────────────────────────────────────────────────┘
  [ ] Passport Copy
  [ ] Application Fee Paid

Checkbox style:
  Lucide `Square` (unchecked) / `CheckSquare` (checked, validated color)
  Label: 13px, ink-muted. Checked: ink-subtle + strikethrough
  HEC row: bg caution-soft, border-radius 8px, padding 8px 12px, caution text
  [ⓘ] tooltip: "Many UK and German universities require HEC attestation of your degree before processing your application."

Notes input (below checklist):
  "Add a note..." — textarea, 2 rows, 13px, placeholder style
  Auto-saves on blur
```

### 8.6 Add Application Modal

Triggered by `[+ Add Application]` or column-level `+ Add here`.

```
┌──────────────────────────────────────────────────────┐
│  Add to tracker                               [×]    │
│  ────────────────────────────────────────────────    │
│                                                      │
│  Program name *                                      │
│  [MS Computer Science                           ]    │
│                                                      │
│  University name *                                   │
│  [University of Manchester                      ]    │
│                                                      │
│  Country                                             │
│  [🇬🇧 United Kingdom ▼                          ]    │
│                                                      │
│  Application deadline                                │
│  [📅  Nov 7, 2025                               ]    │
│                                                      │
│  Scholarship (optional)                              │
│  [Search scholarships...                        ]    │
│  Pulls from /scholarships list                       │
│                                                      │
│  ────────────────────────────────────────────────    │
│  [Cancel]                   [Add to Tracker →]       │
└──────────────────────────────────────────────────────┘

Modal style:
  bg: paper-white
  border-radius: 20px
  padding: 32px
  max-width: 480px
  shadow: shadow-lifted
  backdrop: rgba(12,17,23,0.3)
```

---

## 9. SOP Builder

**Route:** `/dashboard/documents/sop`

### 9.1 Layout

```
DESKTOP: Two-panel split
┌───────────────────────────────┬─────────────────────────────────────┐
│  INPUT PANEL (40%)            │  PREVIEW PANEL (60%)                │
│  Form steps 1–4               │  Generated SOP draft                │
│  bg: paper                    │  bg: paper-white                    │
│  padding: 32px                │  padding: 32px 40px                 │
└───────────────────────────────┴─────────────────────────────────────┘

MOBILE: Tab switcher at top
  [Form] [Preview]
  Tab content stacked below

DIVIDER: 1px vertical line, --border color
```

### 9.2 Input Panel

**Header:**
```
"SOP Builder"  — 22px, font-display, weight 700
"AI-assisted. Pakistani context. Built for Chevening, DAAD, and Fulbright."
— 13px, ink-muted
```

**Scholarship selector:**
```
Targeting a scholarship?  (optional)
[Select or search a scholarship ▼]
Options pull from user's tracker items, then from database
If selected: shows scholarship tags below (Chevening values, DAAD focus, etc.)
Helper: "Selecting a scholarship tailors your SOP narrative to its values."
```

**Step progress inside form panel:**
```
● Academic Background  ●── Research & Work  ──●── Why This Program  ──●── Goals & Pakistan
(current step highlighted, previous steps with checkmark)
```

**Step 1: Academic Background** (pre-filled from profile)
```
Your university background
[NUST — National University of Sciences and Technology    ] ← pre-filled

Degree and field
[BS Computer Science                                       ] ← pre-filled

CGPA
[3.7 / 4.0                                                ] ← pre-filled

Any academic achievements or awards?
[                                                          ]
placeholder: "e.g. Dean's List, gold medal, top 5 in class..."
```

**Step 2: Research & Work Experience**
```
Research experience
[                                                          ]
placeholder: "Describe any thesis, research projects, or publications.
Leave blank if none — we'll frame coursework instead."
rows: 4

Professional/work experience
[                                                          ]
placeholder: "e.g. Software Engineer at X for 2 years, intern at Y..."
rows: 3
Helper: "Include internships, part-time work, and freelance projects."
```

**Step 3: Why This Program / Country**
```
Why this specific program?
[                                                          ]
placeholder: "What draws you to this field, program structure, or faculty?"
rows: 3

Why this country?
[                                                          ]
placeholder: "Germany's tuition-free public universities and STEM research culture..."
rows: 3
```

**Step 4: Goals & Pakistan Context**
```
Career goals after your degree
[                                                          ]
placeholder: "I aim to return to Pakistan and contribute to the tech sector by..."
rows: 3
Helper: "For government scholarships (Chevening, HEC), mention intention to return to Pakistan."

Challenges you've overcome (optional)
[                                                          ]
placeholder: "e.g. First-generation university student, limited resources..."
rows: 2

Gap or weakness to explain? (optional)
[                                                          ]
placeholder: "Any academic gap, low grade period, or test score below average..."
rows: 2
```

**Generate Button (bottom of form panel, sticky):**
```
[Generate SOP Draft →]  primary button, full-width, height 52px, font-size 16px

Loading state:
  Button text changes to "Writing your SOP..."
  Progress bar appears below button:
  ██████████░░░░░░  Structuring your background...
  (animated, with 4 milestone labels: Structuring → Drafting → Refining → Done)
  Estimated 15–25 seconds
  
  Right panel shows skeleton/shimmer for paragraph blocks during generation
```

---

### 9.3 Preview Panel

**Header (when no draft yet):**
```
┌──────────────────────────────────────────────────────────────────┐
│  [FileText icon 40px, ink-subtle]                                │
│                                                                  │
│  Your SOP draft will appear here.                                │
│  Fill in the form and click "Generate SOP Draft →"               │
│                                                                  │
│  ● 600–800 words                                                 │
│  ● 6 structured paragraphs                                       │
│  ● Pakistani academic context included                           │
└──────────────────────────────────────────────────────────────────┘
```

**Header (after generation):**
```
Action bar (above the draft):
  [Copy to clipboard]  [Download .txt]  [Regenerate]  [← Edit inputs]
  Secondary buttons, height 36px, gap 8px

Word count: "743 words · 6 paragraphs" — 12px, ink-subtle, right-aligned
```

**Draft Content (after generation):**

Each paragraph has a label above it:

```
OPENING PARAGRAPH
─────────────────────────────────────────────────────────
[Paragraph text, 15px, ink, line-height 1.7]
─────────────────────────────────────────────────────────

ACADEMIC BACKGROUND
─────────────────────────────────────────────────────────
[Paragraph text...]
─────────────────────────────────────────────────────────

RESEARCH & EXPERIENCE
─────────────────────────────────────────────────────────
[Paragraph text...]
─────────────────────────────────────────────────────────

MOTIVATION FOR THIS PROGRAM
─────────────────────────────────────────────────────────
[Paragraph text...]
─────────────────────────────────────────────────────────

CAREER GOALS
─────────────────────────────────────────────────────────
[Paragraph text...]
─────────────────────────────────────────────────────────

CLOSING
─────────────────────────────────────────────────────────
[Paragraph text...]
─────────────────────────────────────────────────────────

Paragraph label style:
  11px, uppercase, letter-spacing 0.1em, weight 700, ink-subtle
  margin-bottom: 8px, margin-top: 24px
  
Paragraph text:
  Font: IBM Plex Sans, 15px, ink, line-height 1.7
  
Divider between paragraphs:
  1px, --border
```

**Elite Line-by-Line Feedback Panel** (for elite plan users only):

Appears as an accordion below each paragraph when expanded:

```
[+ Feedback for this paragraph ∨]

When expanded:
  ┌──────────────────────────────────────────────────────────┐
  │ What works well                                          │  ← validated-stripe
  │ "Strong opening that immediately establishes your        │
  │  technical background and Pakistani academic context."   │
  └──────────────────────────────────────────────────────────┘
  
  ┌──────────────────────────────────────────────────────────┐
  │ What to improve                                          │  ← caution-stripe
  │ "The second sentence is generic — 'passion for CS'       │
  │  appears in thousands of SOPs."                          │
  └──────────────────────────────────────────────────────────┘
  
  ┌──────────────────────────────────────────────────────────┐
  │ Suggested rewrite                                        │  ← generated-stripe (+ Sparkles)
  │ "Replace 'passion for computer science' with a specific  │
  │  project, result, or insight that sparked your interest."│
  └──────────────────────────────────────────────────────────┘
```

**Disclaimer (bottom of preview panel):**

```
┌──────────────────────────────────────────────────────────────────┐
│ ⚠  This draft is AI-generated based on your inputs.              │  ← caution-stripe
│    Personalise it — admissions committees can detect generic AI  │
│    writing. Add specific details only you know.                  │
└──────────────────────────────────────────────────────────────────┘
```

**Validated Facts Section (when scholarship selected):**

```
┌──────────────────────────────────────────────────────────────────┐
│ ✓  Scholarship facts used in this SOP          [Verified source] │  ← validated-stripe
│    Chevening requires 2 years of work experience                 │
│    Deadline: November 5, 2025 · Award: £18,000 + extras          │
└──────────────────────────────────────────────────────────────────┘
```

---

## 10. Visa Interview Simulator

**Route:** `/dashboard/interview`

---

### 10.1 Setup Screen

```
PAGE HEADER:
"Visa Interview Practice"  — 28px, font-display, weight 700
"Practice with an AI visa officer. Get feedback on every answer."  — 16px, ink-muted

STEP 1: Select your target country

Heading: "Which visa are you practising for?"  — 18px, weight 600

COUNTRY FLAG CARDS (2×2 grid on mobile, 4 across on desktop):

┌──────────────────┐  ┌──────────────────┐
│                  │  │                  │
│       🇬🇧         │  │       🇺🇸         │
│                  │  │                  │
│   United Kingdom │  │   United States  │
│   Student Visa   │  │     F-1 Visa     │
│                  │  │                  │
│  20 questions    │  │  20 questions    │
└──────────────────┘  └──────────────────┘

┌──────────────────┐  ┌──────────────────┐
│                  │  │                  │
│       🇨🇦         │  │       🇩🇪         │
│                  │  │                  │
│     Canada       │  │    Germany       │
│   Study Permit   │  │  Student Visa    │
│                  │  │                  │
│  15 questions    │  │  15 questions    │
└──────────────────┘  └──────────────────┘

Card style:
  bg: paper-white
  border: 2px solid --border
  border-radius: 16px
  padding: 24px
  width: 180px (desktop), full-width col (mobile)
  text-align: center
  Flag: 40px emoji
  Country: 15px, weight 600, ink, margin-top 10px
  Visa type: 12px, ink-muted
  Question count: 12px, ink-subtle, margin-top 4px

  Selected state:
    border: 2px solid ink
    bg: paper-warm
    Checkmark overlay: 20px circle, ink bg, white checkmark, top-right

─────────────────────────────────────────────────────────────────────

STEP 2: Select your mode

Heading: "How do you want to practise?"  — 18px, weight 600

TWO MODE CARDS (side by side):

┌───────────────────────────────┐  ┌───────────────────────────────┐
│  [BookOpen icon 32px]         │  │  [Clock icon 32px]            │
│                               │  │                               │
│  Study Mode                   │  │  Exam Mode                    │
│                               │  │                               │
│  See detailed feedback after  │  │  No feedback between          │
│  every answer. Understand     │  │  questions. Simulates the     │
│  red flags in real-time.      │  │  real interview experience.   │
│  Best for preparation.        │  │  Best for final practice.     │
│                               │  │                               │
│  ● Full AI feedback           │  │  ○ Summary only at end        │
│  ● Red flag detection         │  │  ○ Timer visible              │
│  ● Ideal answer shown         │  │  ○ Builds mental endurance    │
└───────────────────────────────┘  └───────────────────────────────┘

Selected: ink border 2px, paper-warm bg
Icon: 32px, in rounded bg 10px, color matches mode (blue/amber)

─────────────────────────────────────────────────────────────────────

CTA:
  [Start Practice Session →]  primary button, height 52px, font-size 16px
  Disabled until both country and mode selected
  Below: "10 questions · Takes about 15–20 minutes · No login required to restart"
  12px, ink-subtle, centered
```

---

### 10.2 Interview Screen (Q&A)

```
LAYOUT:
  Single column, max-width 720px, centered
  No sidebar distractions — full focus mode

─────────────────────────────────────────────────────────────────────

TOP BAR:
  [←  Exit]  ghost button, top-left
  Progress:  "Question 3 of 10"  centered, 14px, weight 500
  Timer (exam mode only):  "05:42"  top-right, monospace, 14px, ink-subtle
  
  Progress bar (below top bar):
  ████████████░░░░░░░░░░░░░░░░░  30%
  h: 6px, bg paper-dim, filled: ink

─────────────────────────────────────────────────────────────────────

QUESTION CARD:
  bg: paper-white
  border: 1px solid --border
  border-radius: 20px
  padding: 40px

  Category badge (top of card):
  ┌──────────────────┐
  │  💰  Finances    │  ← caution-soft bg, caution text, 12px, weight 600
  └──────────────────┘
  (categories: Motivation / Finances / Ties to Pakistan / Program Knowledge / Future Plans)

  Question text:
  "How will you fund your studies in the UK?"
  — 22px, font-display, weight 600, ink, line-height 1.4
  margin-top: 16px

  Context hint (study mode only, below question):
  "Visa officers want specific numbers and confirmed funding sources. 
   Vague answers raise red flags."
  — 13px, ink-subtle, margin-top: 8px

─────────────────────────────────────────────────────────────────────

ANSWER AREA:
  Textarea:
    placeholder: "Type your answer as you would speak it. Be natural, not rehearsed."
    min-height: 160px
    font: 15px IBM Plex Sans, ink
    border: 1px solid --border, radius 12px
    focus border: generated, ring shadow
    margin-top: 24px
    resize: vertical

  Character count: "0 / no limit"  — 12px, ink-subtle, right below textarea, right-aligned

  [Submit Answer →]  primary button, full-width, height 52px
    Disabled when textarea empty
    Loading state: "Evaluating your answer..." (button text change, progress dots)
    
  [← Previous question]  ghost link, 12px, left-aligned below button
  (Shows only after first question; in study mode only)
```

---

### 10.3 Feedback Panel (Study Mode Only)

Slides in below the question card after submission. Card expands, then feedback appears.

```
FEEDBACK CARD (replaces submit button area, animates in):
  bg: paper-white
  border: 1px solid --border
  border-radius: 16px
  padding: 28px
  margin-top: 16px

SCORE METERS:
  3 horizontal bars side by side (or stacked on mobile)
  
  Clarity        ████████░░  4/5
  Confidence     ██████░░░░  3/5  
  Relevance      █████████░  4.5/5
  
  Each meter:
    Label: 13px, weight 600, ink-muted
    Bar: h 8px, bg paper-dim, filled = generated
    Score: "4/5" — 14px, weight 700, right-aligned
    Bar fill color: 
      4–5: validated (#426B5A)
      3–3.9: caution (#B7791F)
      1–2.9: danger (#B94A48)

RED FLAG ALERTS (if any):
  ┌──────────────────────────────────────────────────────────┐
  │ ⚠  Red flag detected                                     │  ← danger-stripe
  │    "You mentioned wanting to stay in the UK after        │
  │     graduation. This signals immigration intent to a     │
  │     visa officer — always clarify your return plan."     │
  └──────────────────────────────────────────────────────────┘
  (Only shown if red_flags array is non-empty)

WHAT WAS GOOD:
  ┌──────────────────────────────────────────────────────────┐
  │ ✓  What you did well                                     │  ← validated-stripe
  │    "You clearly stated the funding source (family        │
  │     savings) and gave a specific amount. This builds     │
  │     credibility with the visa officer."                  │
  └──────────────────────────────────────────────────────────┘

WHAT TO ADD:
  ┌──────────────────────────────────────────────────────────┐
  │ ⚠  What to include next time                            │  ← caution-stripe
  │    "Missing: confirmation that funds are in a UK-        │
  │     accessible account. Mention bank name and that       │
  │     statements are available if requested."              │
  └──────────────────────────────────────────────────────────┘

IDEAL ANSWER SUMMARY:
  ┌──────────────────────────────────────────────────────────┐
  │ ✦  Strong answer includes                               │  ← generated-stripe + Sparkles icon
  │    "Specific total amount (tuition + living), source     │
  │     (scholarship + family savings), confirmation funds   │
  │     are accessible, no mention of working while          │
  │     studying in the UK."                                 │
  └──────────────────────────────────────────────────────────┘

CTA (bottom of feedback card):
  [Next Question →]  primary button, full-width, height 48px
  
  Below: "Question 4 of 10 · Finances"  — 12px, ink-subtle, centered
```

---

### 10.4 Freemium Gate (Free Tier, After Q3)

Replaces the feedback panel after question 3:

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  [Lock icon 28px, gold color]                                       │
│                                                                     │
│  You got 2 red flags in your first 3 answers.                       │  ← 20px, weight 700
│  Questions 4–10 expose the weakest parts of your answers.           │  ← 14px, ink-muted
│                                                                     │
│  Your partial result:                                               │
│  Clarity: 3.5/5   Confidence: 2.8/5   Relevance: 4.0/5            │
│                                                                     │
│  [Upgrade to Pro — PKR 2,499/mo →]  gold button, full-width        │
│  [Or go Elite for full session transcript]  ghost link, gold        │
│                                                                     │
│  No consultant fees. Less than one meeting. Cancel anytime.         │
│  12px, ink-subtle, centered                                         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

### 10.5 Session Summary Screen

Shown after all 10 questions answered (or after free gate if elite).

```
PAGE HEADING:
"Session Complete"  — 28px, font-display, weight 700
"UK Student Visa · Study Mode · 10 questions"  — 14px, ink-subtle

─────────────────────────────────────────────────────────────────────

RADAR CHART (SVG, no external library):
  4 axes: Clarity · Confidence · Relevance · Red Flag Avoidance
  Filled area: generated (#2E5B9A) at 30% opacity
  Axis lines: --border
  Axis labels: 12px, ink-muted
  Data points: 6px circles, generated fill
  Size: 280×280px, centered

Overall score below chart:
  "3.8 / 5.0"  — 36px, font-display, weight 700, validated color
  "Good preparation level"  — 14px, ink-muted

─────────────────────────────────────────────────────────────────────

AREAS TO IMPROVE (3 top weaknesses):
  Heading: "Focus on these before your interview"  — 16px, weight 600

  ┌────────────────────────────────────────────────────────────┐
  │  1.  Funding explanation                 Confidence: 2.8  │
  │      "Provide specific amounts and accessible account     │
  │       confirmation. Vague funding answers are a top       │
  │       reason for student visa refusals."                  │
  └────────────────────────────────────────────────────────────┘
  
  (Same card for items 2 and 3)

─────────────────────────────────────────────────────────────────────

QUESTION-BY-QUESTION TABLE:
  Heading: "All 10 questions"  — 16px, weight 600

  ┌───┬─────────────────────────────────┬──────────┬──────────┬──────────┬────────────┐
  │ # │ Question                         │ Clarity  │ Conf.    │ Relev.   │ Red Flags  │
  ├───┼─────────────────────────────────┼──────────┼──────────┼──────────┼────────────┤
  │ 1 │ Why do you want to study in UK? │   4/5    │   3/5    │   4/5    │   None     │
  │ 2 │ How will you fund your studies? │   3/5    │   2/5    │   3/5    │ ⚠ 1 flag  │
  │...│                                 │          │          │          │            │
  └───┴─────────────────────────────────┴──────────┴──────────┴──────────┴────────────┘

  Score cell color: validated (4–5), caution (3–3.9), danger (<3)
  Red flag: danger badge with count

─────────────────────────────────────────────────────────────────────

ACTIONS:
  [Practice Again]  secondary button
  [Download Summary]  secondary button (all plans — downloads PDF summary)
  [Download Full Transcript]  gold button (Elite only — detailed transcript)
  
  Below: [← Back to dashboard]  ghost link
```

---

## 11. Upgrade Page

**Route:** `/upgrade`  
**Layout:** Full-width, no sidebar. Max-width 1000px.

### 11.1 Header

```
"Find the right plan for you"  — 36px, font-display, weight 700, centered

"Start free. Upgrade when you're serious."  — 16px, ink-muted, centered

CURRENCY SWITCHER (centered, below heading):
  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐
  │  PKR │ │  GBP │ │  EUR │ │  AED │ │  USD │
  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘

  Active: bg ink, text white, radius 8px
  Inactive: bg paper-warm, text ink-muted
  Height: 36px, padding: 0 16px
  Default: PKR for Pakistan users (from billing_country)
  
  On click: all prices on page update instantly (JS, no reload)
```

### 11.2 Pricing Cards

**4-column grid. Pro card is wider or has highlighted ring.**

```
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│                  │ │  [MOST POPULAR]  │ │                  │ │                  │
│   Explorer       │ │     Pro          │ │     Elite        │ │  Institution     │
│                  │ │ ★                │ │ For serious      │ │                  │
│   Free           │ │ PKR 2,499/mo    │ │ PKR 7,999/mo    │ │ Contact us       │
│   Forever        │ │                  │ │                  │ │                  │
│   ─────────────  │ │  ─────────────  │ │  ─────────────  │ │  ─────────────   │
│ ✓ 3 matches      │ │ ✓ All matches   │ │ ✓ All Pro feat. │ │ ✓ Seat licence   │
│ ✓ Browse all     │ │ ✓ Unlimited SOP │ │ ✓ Line feedback │ │ ✓ Admin portal   │
│ ✓ 1 SOP draft   │ │ ✓ Full interview │ │ ✓ Transcript    │ │ ✓ Bulk import    │
│ ✓ 3 Q interview │ │ ✓ Unlimited track│ │ ✓ Prof emails   │ │ ✓ Outcomes dash  │
│ ✗ Tracker limit │ │ ✓ Email alerts  │ │ ✓ Strategy PDF  │ │ ✓ White-label    │
│ ✗ No alerts     │ │                  │ │ ✓ SMS + WhatsApp│ │                  │
│                  │ │                  │ │ ✓ Priority match│ │                  │
│                  │ │                  │ │                  │ │                  │
│ [Start free]     │ │ [Get Pro →]      │ │ [Get Elite →]   │ │ [Contact us →]   │
└──────────────────┘ └──────────────────┘ └──────────────────┘ └──────────────────┘

Under Pro CTA:
"2 months of ScholarAI Pro = less than 1 consultant meeting."
11px, ink-subtle, centered, italic

Under Elite CTA:
"For Pakistani families in the UK or UAE — less than a coffee per week."
11px, ink-subtle, centered, italic

CARD STYLES:
  Explorer: standard card, paper-white, --border
  Pro: gold border (2px, gold color), shadow-soft, 
       "MOST POPULAR" badge: gold-soft bg, gold text, top center
  Elite: standard card, paper-white, --border, 
         "For serious applicants" badge: generated-soft, generated text
  Institution: standard card, paper-warm, dashed border

Checkmarks: ✓ = validated color, ✗ = ink-subtle

CURRENCY-AWARE PRICING (JS updates all):
  PKR: Free | PKR 2,499/mo | PKR 7,999/mo | Custom
  GBP: Free | £6.99/mo    | £19.99/mo    | Custom
  EUR: Free | €7.99/mo    | €22.99/mo    | Custom
  AED: Free | AED 29/mo   | AED 89/mo    | Custom
  USD: Free | $8.99/mo    | $24.99/mo    | Custom
```

### 11.3 Waitlist Form (Inline, Pro and Elite)

When "Get Pro →" or "Get Elite →" is clicked:

```
CARD EXPANDS to show inline form (accordion, no page navigation):

  ┌──────────────────────────────────────────────────────────┐
  │                                                          │
  │  Join the Pro waitlist                                   │
  │  "Payments launching soon. We'll email you first."       │
  │  13px, ink-muted                                         │
  │                                                          │
  │  Your email                                              │
  │  [                                                  ]    │
  │  placeholder: "your@email.com"                           │
  │                                                          │
  │  [Join Pro Waitlist →]  gold button, full-width          │
  │                                                          │
  │  After submit:                                           │
  │  ✓ You're on the list!                                   │
  │    We'll email you when Pro launches.                    │
  │    (validated color, animated checkmark)                 │
  │                                                          │
  └──────────────────────────────────────────────────────────┘
```

### 11.4 Comparison Table

Below pricing cards:

```
Heading: "Compare all features"  — 22px, weight 600

TABLE:
  Feature column (left) | Explorer | Pro | Elite | Institution

Feature rows:
  SCHOLARSHIP DISCOVERY
    Scholarship matches       Top 3 | All | All + priority | All
    University matches        Top 3 | 30+ | 30+ + visa rate | All
    Pakistani context         ✓ | ✓ | ✓ | ✓
    CGPA conversion           ✓ | ✓ | ✓ | ✓

  SOP BUILDER
    SOP drafts                1 lifetime | Unlimited | Unlimited | Unlimited
    Line-by-line feedback     — | — | ✓ | ✓

  VISA INTERVIEW
    Practice questions        Q 1–3 | Full 10 | Full 10 | Full 10
    Session transcript        — | — | ✓ | ✓

  TRACKER
    Applications tracked      Max 3 | Unlimited | Unlimited | Unlimited
    Deadline reminders        30 days | Email | Email+SMS+WhatsApp | Custom

  ELITE EXCLUSIVE
    Professor email generator — | — | ✓ | ✓
    Application strategy PDF  — | — | ✓ | ✓
    Priority alerts (7 days)  — | — | ✓ | ✓

  B2B
    Admin dashboard           — | — | — | ✓
    Bulk student import       — | — | — | ✓
    Outcomes analytics        — | — | — | ✓

TABLE STYLE:
  Header row: bg paper-warm, 12px uppercase, weight 600, letter-spacing 0.06em
  Alternating rows: paper-white / paper (#F7F5F0)
  ✓ = CheckCircle (validated color)
  — = em dash (ink-subtle)
  Category rows (SCHOLARSHIP DISCOVERY etc.): bg paper-dim, 11px, uppercase, weight 700, ink-subtle
  Column widths: feature 40%, others equal split
  First cell: 14px, weight 500, ink
  Pro column: gold top/bottom border on each cell (subtle gold tint bg)
```

---

## 12. Shared Components

### 12.1 UpgradeWall Component

Used across: Scholarship Finder (blur), Tracker (4th item), SOP Builder (2nd generation), Interview (Q3+).

```
PROPS:
  message: string  (from API 402 response — specific, never generic)
  price: string    (from API — currency-correct: "PKR 2,499/month")
  featureName: string
  showElite: boolean  (true for SOP + Interview, false for Tracker + Matcher)

LAYOUT:
  ┌──────────────────────────────────────────────────────────────────┐
  │                                                                  │
  │  [Lock icon 24px, gold color]                                    │
  │                                                                  │
  │  {message}                                                       │
  │  15px, weight 600, ink, max-width 400px                          │
  │                                                                  │
  │  [Upgrade to Pro — {price} →]                                    │
  │  gold button, width: fit-content, height 44px                    │
  │                                                                  │
  │  {showElite && "Or get Elite for full AI feedback"}              │
  │  generated-color ghost link, 13px                                │
  │                                                                  │
  │  "No consultant. No hidden fees. Cancel anytime."                │
  │  11px, ink-subtle, centered                                      │
  │                                                                  │
  └──────────────────────────────────────────────────────────────────┘

NEVER show generic text like "Upgrade to unlock this feature."
ALWAYS use the `message` prop from the API 402 response.

Example messages (from API):
  Matcher:   "9 more scholarships match your profile — including 2 fully funded ones closing in 47 days."
  SOP:       "Want to adapt this SOP for DAAD Germany? Pro users generate unlimited SOPs."
  Interview: "You got 2 red flags in 3 answers. Questions 4–10 will tell you exactly what to fix."
  Tracker:   "You have 4 upcoming deadlines you're not tracking."

Style:
  bg: paper-white
  border: 1px solid gold-soft
  border-radius: 16px
  padding: 28px
  max-width: 400px
  text-align: center
  shadow: shadow-soft
```

### 12.2 Scholarship Card (Compact, used in Feed + Dashboard widgets)

```
┌───────────────────────────────────────────────────────────────┐
│  🇬🇧  Chevening Scholarship                   96% match        │
│       UK · Fully Funded · Nov 2025                           │
│       ✓ CGPA 3.7 qualifies  ✓ IELTS 7.0 ✓                   │
│                                    [View]  [+ Tracker]       │
└───────────────────────────────────────────────────────────────┘

Height: 88px
bg: paper-white, border --border, radius 12px, padding: 14px 20px
Flag: 20px emoji
Name: 14px, weight 600, ink
Detail line: 12px, ink-subtle
Checkmarks: 11px, validated color, ✓ icon
Match %: right-aligned, 14px weight 700, validated color
[View]: ghost link, 12px, generated color
[+ Tracker]: secondary button, height 28px, 11px
```

### 12.3 Empty States

Pattern for all empty states:

```
CENTERED CONTENT (icon + text + CTA):

  [Icon: 48px, paper-dim bg, ink-subtle color, radius 14px, padding 14px]

  "No applications tracked yet."
  16px, weight 600, ink, margin-top: 16px

  "Add scholarships from your matches to start tracking deadlines and documents."
  14px, ink-muted, max-width: 320px, centered, line-height: 1.6, margin-top: 8px

  [Add from matches →]  primary button, height 44px, margin-top: 24px

NEVER use blank white space. NEVER just show "No data."
```

### 12.4 Skeleton Loading

Used while data loads. Shows once per route load — never repeats mid-session.

```
Skeleton style:
  bg: linear-gradient(90deg, paper-dim 25%, paper-warm 50%, paper-dim 75%)
  background-size: 200% 100%
  animation: shimmer 1.5s infinite
  border-radius: matches the element it replaces

Skeleton for scholarship card: 88px height block
Skeleton for full page: 3–4 card-height blocks
Skeleton for text: 3 lines at 60%, 80%, 40% width
```

### 12.5 Error State

```
"Couldn't load your matches."

[Retry]  secondary button

Never show: "Network error", "500", or technical language.
Always include an action: [Retry] / [Reload] / [Back to home]
```

---

## 13. Screen Inventory

| Screen | Route | Auth | Notes |
|--------|-------|------|-------|
| Landing Page | `/` | Public | Pakistan-focused, no sidebar |
| Signup | `/signup` | Public | Centered card |
| Login | `/login` | Public | Centered card |
| Onboarding | `/onboarding` | Auth | 5 steps, no sidebar |
| Dashboard | `/feed` | Student | Action grid, matches, tracker widget |
| Scholarship Finder | `/dashboard/scholarships/match` | Student | Match tabs, blur gate |
| Scholarship Detail | `/scholarships/[id]` | Student | Full details, apply CTA |
| Browse All | `/discover` | Student | Search + filters |
| Saved | `/saved` | Student | Kanban: saved/in-progress/applied |
| Application Tracker | `/dashboard/tracker` | Student | 6-col kanban, checklists |
| SOP Builder | `/dashboard/documents/sop` | Student | Two-panel, Pakistan context |
| Documents List | `/documents` | Student | List of generated SOPs |
| Visa Interview | `/dashboard/interview` | Student | Setup → Q&A → Summary |
| Profile | `/profile` | Student | Full profile editor |
| Settings | `/settings` | Student | Account settings |
| Upgrade Page | `/upgrade` | Public | Pricing, currency switcher, waitlist |
| Admin Overview | `/admin` | Admin | KPI dashboard |
| Ingestion | `/admin/ingestion` | Admin | Scholarship ingestion runs |
| Curation | `/admin/curation` | Admin | raw → validated → published |

---

## Key Copy Strings Reference

### Hero Copy
- Headline: **"Find fully-funded programs abroad. No consultant. No fees."**
- Subheadline: "ScholarAI matches Pakistani students to scholarships they actually qualify for — based on CGPA, IELTS, field, and target country."
- Speed promise: "Get your matches in under 60 seconds."
- Primary CTA: **"Find My Scholarships →"**
- Secondary: "Already have an account? Sign in"

### Onboarding CTAs
- Steps 1–4: **"Continue →"**
- Step 5: **"Find My Scholarships →"**
- Back: **"← Back"**
- Skip: "Skip this step →"

### Dashboard CTAs
- "Find Scholarships" → `/dashboard/scholarships/match`
- "Practice Visa Interview" → `/dashboard/interview`
- "Write Your SOP" → `/dashboard/documents/sop`
- "Application Tracker" → `/dashboard/tracker`

### Freemium Copy
- Matcher lock: "9 more matches — including 2 fully funded closing in 47 days."
- SOP lock: "Want to adapt this SOP for another university? Pro generates unlimited SOPs."
- Interview lock: "You got 2 red flags in 3 answers. Questions 4–10 tell you exactly what to fix."
- Tracker lock: "You have 4 upcoming deadlines you're not tracking."
- Generic fallback (avoid): ~~"Upgrade to unlock this feature."~~

### Pricing Anchors
- Under Pro: **"2 months of ScholarAI Pro = less than 1 consultant meeting."**
- Under Elite: **"For Pakistani families in the UK or UAE — less than a coffee per week."**
- Pakistan context: "Less than one hour of a consultant's time per month."

### Trust Signals
- "Student-only — we don't take money from universities."
- "No hidden fees. Cancel anytime."
- "No consultant. No fees."

---

*End of Design Specification — ScholarAI Pakistan v2.0*
