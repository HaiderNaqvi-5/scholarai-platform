# Stitch Prompt Pack — AidwiseAI Scholarship Platform

Project: `12360728925682002511` (AidwiseAI Scholarship Platform)
Design system asset: `04fe1ca1330940ab97ca88c06a3b2c8f` ("Academic Intelligence")
Spec source: `Front-upgrade.md`

## Why this pack exists
Stitch MCP timed out on most edits during this session (Pro model throttled, Flash inconsistent). These prompts are ready-to-paste into the Stitch UI at https://labs.google.com/stitch — open the project, select the target screen, paste the prompt, run with Gemini 3.1 Pro or 3 Flash. Each prompt is self-contained and pre-aligned with `Front-upgrade.md` plus the project's "Academic Intelligence" design system.

## Status from this session
| Screen | Action | Status |
|---|---|---|
| Onboarding Step 2 | Step indicator 2/5, HEC scale, validated-stripe CGPA conversion, Lucide icons | ✅ landed as `92c5dd95` |
| Dashboard Mobile | 5-tab bar (My Matches/Find/Tracker/Visa/Profile), Lucide, action grid, tracker widget | ✅ landed as `917fb861` |
| Application Tracker | 6-column Kanban incl. Accepted, 14-item checklist with HEC highlight, Lucide, deadline banner | ✅ landed as `3a45980d` |

All others: use prompts below.

---

## Global rules applied to every prompt
- Brand string must read **AidwiseAI** (single word, exact casing). Replace any "GrantPath" / "ScholarAI" / "Aidwise AI".
- Icons: Lucide React SVG only — replace every Material Symbol. stroke-width 1.75 for nav, 2 for actions, stroke="currentColor", fill="none".
- Fonts (Google Fonts CDN): Sora 500/600/700 for headings; IBM Plex Sans 400/500/600 for body; IBM Plex Mono 400/500 for mono labels/eyebrows.
- Palette: paper #F7F5F0, paper-warm #F1EDE4, paper-dim #E7E1D5, paper-white #FFFDF9, ink #0C1117, ink-strong #1B2633, ink-muted #334155, ink-subtle #64748B, validated #426B5A + soft #DDE9E2, generated #2E5B9A + soft #DCE6F4, caution #B7791F + soft #F4E7CF, danger #B94A48 + soft #F4D8D6, gold #8B6914 + soft #F5EDD6. Border rgba(12,17,23,0.08), ring rgba(46,91,154,0.32). No #000 / pure #FFF.
- Radii: 12px buttons/inputs/chips, 16px cards, 20px panels/modals, 24px hero.
- Semantic left-border stripes (PR-blocking):
  - validated-stripe: 3px solid #426B5A + bg #DDE9E2 + Lucide Check icon. For verified facts.
  - generated-stripe: 3px solid #2E5B9A + bg #DCE6F4 + Lucide Sparkles icon. For AI-generated content.
  - caution-stripe: 3px solid #B7791F + bg #F4E7CF + Lucide AlertTriangle icon. For warnings.
- Footer copyright "© 2026 AidwiseAI". Replace "© 2024" if present.
- 44×44 minimum tap targets.

---

## 1. Landing — Desktop (EDIT screen `c64af699a85444f294e998e17f5005dd`)
```
Convert the Landing hero to an ASYMMETRIC SPLIT (left 55% / right 45%), never centered.

LEFT 55%:
- Eyebrow pill (bg #F1EDE4 rounded-full px-3 py-1 text-sm): "🇵🇰 Built for Pakistani students"
- Headline Sora 700 56px desktop / 44px mobile, leading 1.1: "Find fully-funded programs abroad.\nNo consultant. No fees."
- Subhead 18px #334155 max-w 440px: "AidwiseAI matches Pakistani students to scholarships they actually qualify for, based on CGPA, IELTS, field, and target country."
- Speed promise text-sm #64748B: "Get your matches in under 60 seconds."
- CTA: primary lg button "Find My Scholarships →" + link "Already have an account? Sign in"
- Social proof — 3 rows, each prefixed with Lucide CheckCircle 16px #426B5A: "Free forever, no consultant fees" · "Chevening, Fulbright, DAAD and more" · "Visa interview prep included". NOT a 3-stat metric trio.

RIGHT 45% preview card (bg #FFFDF9 1px border rounded 24px p-6 shadow-soft max-w 400px):
- Header: "Your AI Match Results · 3 of 12 →"
- 3 rows bg #F7F5F0 rounded 12px p-3.5:
  - 🇬🇧 Chevening Scholarship · UK · Fully Funded · Nov 2025 · 96% match
    Nested validated-stripe block: Lucide Check + "CGPA 3.7 qualifies" + "IELTS 7.0 meets requirement"
  - 🇺🇸 Fulbright Fellowship · USA · Fully Funded · Feb 2026 · 91% match
  - 🇩🇪 DAAD Scholarship · Germany · Fully Funded · 87% match
- Lock row bg #F1EDE4 1px dashed: Lucide Lock + "9 more matches, 2 closing in 47 days" + gold sm button "Unlock with Pro →"
- Footnote text-xs #64748B: "Profile: NUST · CS · CGPA 3.7 · IELTS 7.0"

Keep all other landing sections intact (Stats Bar, Problem 2×2, How It Works 4 steps, Featured Scholarships, Visa Callout, Pricing Teaser, Footer). Replace ALL Material Symbols with Lucide React SVG. Fonts Sora/IBM Plex Sans/Mono via Google Fonts. Footer "© 2026 AidwiseAI" + mailto `partnerships@aidwiseai.pk` text-gold.
```

---

## 2. Landing — Mobile (EDIT screen `d39544aed48e4ec0968d2b92efbba931`)
```
Replace hero copy with the AidwiseAI v3 spec headline: "Find fully-funded programs abroad. No consultant. No fees." (Sora 700 44px leading 1.1). Subhead 16px #334155: "AidwiseAI matches Pakistani students to scholarships they actually qualify for, based on CGPA, IELTS, field, and target country." Speed promise text-sm #64748B: "Get your matches in under 60 seconds." Primary lg "Find My Scholarships →" full-width + secondary link "Already have an account? Sign in".

Social proof — 3 rows, each with Lucide CheckCircle 16px #426B5A: "Free forever, no consultant fees" · "Chevening, Fulbright, DAAD and more" · "Visa interview prep included". NOT metric tiles.

Preview card stacks below CTA, full-width: bg #FFFDF9 rounded 24px p-6 shadow-soft, 3 result rows + lock row with gold "Unlock with Pro →" button.

Top sticky nav: hamburger left, "AidwiseAI" wordmark center, ghost "Sign in" right.

Replace ALL Material icons with Lucide React SVG. Brand exactly "AidwiseAI". Fonts Sora/IBM Plex Sans/Mono via Google Fonts. Footer "© 2026 AidwiseAI" + mailto `partnerships@aidwiseai.pk`.
```

---

## 3. Onboarding Step 1 (EDIT screen `bc248c2d7c4d498a97f72afe863d64c8`)
```
Update step indicator to "Step 1 of 5 — About You" with 5 ProgressDots (dot 1 active wide-pill #0C1117, dots 2/3/4/5 future #E7E1D5). Step eyebrow inside card "STEP 1 OF 5" IBM Plex Mono uppercase tracking-[0.16em] #64748B. Add "~3 min left" text-xs #64748B top-right outside card.

Card shell bg #FFFDF9 1px border rounded 20px p-10 shadow-soft max-w 600px on page bg #F7F5F0.

Title Sora 600 30px: "Tell us about yourself". Subtitle IBM Plex Sans 15px #334155: "We'll use this to personalise your scholarship matches."

5 fields in order:
1. "Full name *" Input placeholder "Zara Khan" (required)
2. "City of origin" Select with Lucide MapPin prefix; options: Karachi, Lahore, Islamabad, Rawalpindi, Faisalabad, Peshawar, Quetta, Multan, Sialkot, Hyderabad, Other
3. "Pakistani university" Searchable combobox (Lucide Search inside trigger); options: NUST, LUMS, FAST-NUCES, UET Lahore, IBA Karachi, QAU, COMSATS, UCP, NED, UMT, BNU, Air University, GIKI, PIEAS, FCCU, University of Karachi, University of the Punjab, SZABIST + "Other"
4. "Degree subject" Input free text placeholder "e.g. Computer Science, Electrical Engineering", helper "Your undergraduate major"
5. "Graduation year" Select 2018–2025

"Draft saved" indicator top-right inside card: Lucide Check 12px #426B5A + "Draft saved" text-xs #64748B.

Footer: ghost "← Back" (DISABLED on Step 1) left + primary "Continue →" right. No Skip button.

Replace ALL Material icons with Lucide React SVG. Fonts Sora/IBM Plex Sans/Mono via Google Fonts. Brand "AidwiseAI". Footer "© 2026 AidwiseAI".
```

---

## 4. Onboarding Step 3 — Test Scores (NEW — generate via mcp__stitch__generate_screen_from_text, deviceType DESKTOP, designSystem `assets/04fe1ca1330940ab97ca88c06a3b2c8f`)
```
AidwiseAI onboarding Step 3 of 5 — Test Scores. Page bg #F7F5F0, no sidebar.

Top of page outside card: "Step 3 of 5 — Test Scores" Sora 600 + "~2 min left" text-xs #64748B right. ProgressDots row: dots 1+2 done (filled #334155), dot 3 active (wide pill #0C1117), dots 4/5 future (#E7E1D5).

Card bg #FFFDF9 1px border rounded 20px p-10 shadow-soft max-w 600px:
- Step eyebrow "STEP 3 OF 5" IBM Plex Mono uppercase tracking-[0.16em] #64748B
- Title Sora 600 30px: "Test scores"
- Subtitle IBM Plex Sans 15px #334155: "All optional. Add what you have, skip what you don't."

Fields:
1. "IELTS Overall" number input 0.0–9.0 step 0.5, helper text-xs #64748B "Leave blank if not taken yet". On fill, show a validated-stripe block (border-left 3px #426B5A bg #DDE9E2 rounded 12px p-3.5 mt-2): Lucide Check 16px + "7.0 meets the requirement for most UK / Germany / Canada scholarships in our database."
2. "TOEFL iBT" number input 0–120, helper "Leave blank if not taken yet"
3. "GRE Quant" + "GRE Verbal" two number inputs side-by-side (130–170 each)
4. Toggle row "I need programs that don't require GRE" — 44x24 pill switch. When ON, show caution-stripe note (border-left 3px #B7791F bg #F4E7CF p-3): Lucide AlertTriangle + "We'll filter out GRE-required programs in your matches."

Skip hint at bottom: text-xs #64748B "Not sure about your scores? Update these later from your Profile."

Footer: ghost "← Back" left + primary "Continue →" right + ghost "Skip this step →" between them.

"Draft saved" indicator top-right inside card: Lucide Check 12px #426B5A + "Draft saved" text-xs #64748B.

Lucide React SVG icons only. Fonts Sora/IBM Plex Sans/Mono via Google Fonts. Brand exactly "AidwiseAI". Footer "© 2026 AidwiseAI".
```

---

## 5. Onboarding Step 4 — Your Goal (NEW — generate via generate_screen_from_text, DESKTOP)
```
AidwiseAI onboarding Step 4 of 5 — Your Goal. Page bg #F7F5F0.

Top outside card: "Step 4 of 5 — Your Goal" Sora 600 + "~1 min left" text-xs #64748B. ProgressDots: dots 1/2/3 done, dot 4 active wide pill, dot 5 future.

Card bg #FFFDF9 1px border rounded 20px p-10 shadow-soft max-w 600px:
- Step eyebrow "STEP 4 OF 5" IBM Plex Mono uppercase tracking-[0.16em] #64748B
- Title Sora 600 30px: "What's your goal?"
- Subtitle 15px #334155: "This is what we rank scholarships against."

Fields:
1. "Target degree *" — 3 radio cards horizontal: MS (Masters) | PhD (Doctorate) | MBA (Business). Selected: 2px border #0C1117, bg #F1EDE4. Required.
2. "Target countries *" — flag cards grid 4-across desktop / 2-across mobile, multi-select: 🇬🇧 UK · 🇺🇸 USA · 🇨🇦 Canada · 🇩🇪 Germany · 🇦🇺 Australia · 🇮🇪 Ireland · 🇳🇱 Netherlands. Selected: 2px ink border + bg #F1EDE4 + Lucide Check 20px overlay top-right. Validation hint #B94A48: "Select at least one country to continue."
3. "Target field(s)" — chip multi-select h-10 rounded-full px-4: Computer Science, AI/ML, Data Science / Analytics, Electrical Eng., Business, Engineering, Medicine, Other. Active chip: bg #0C1117 text #FFFDF9. Inactive: 1px border bg #FFFDF9.
4. "Funding requirement" — 2 radio cards: Fully funded only | Partial funding OK
5. "Target intake" — Select: Jan 2025, Sep 2025, Jan 2026, Sep 2026, Flexible

Footer: ghost "← Back" left + primary "Continue →" right. Continue disabled until target_degree set AND ≥1 target country chosen.

"Draft saved" indicator top-right inside card with Lucide Check.

Lucide icons only. Sora/IBM Plex Sans/Mono via Google Fonts. Brand "AidwiseAI". Footer "© 2026 AidwiseAI".
```

---

## 6. Onboarding Step 5 — Financial Context (NEW — generate via generate_screen_from_text, DESKTOP)
```
AidwiseAI onboarding Step 5 of 5 — Financial Context. Page bg #F7F5F0.

Top outside card: "Step 5 of 5 — Financial Context" Sora 600 + "almost done" text-xs #426B5A. ProgressDots: dots 1/2/3/4 done, dot 5 active wide pill.

Card bg #FFFDF9 1px border rounded 20px p-10 shadow-soft max-w 600px:
- Step eyebrow "STEP 5 OF 5" IBM Plex Mono uppercase tracking-[0.16em] #64748B
- Title Sora 600 30px: "A few quick questions"
- Subtitle 15px #334155: "This helps us surface relevant support options. All optional."

3 toggle rows, each bg #FFFDF9 1px border rounded 12px p-4:
1. "Can you afford application fees?" — sub text-sm #64748B "Most universities charge $50–150 per application." + 44×24 pill switch right.
2. "Does your family have savings for a bank statement?" — sub "Required for UK / USA / Canada visa applications." + toggle.
3. "Do you need a GRE fee waiver?" — sub "Some universities offer waivers on request." + toggle.

Bottom note text-xs #64748B: "You can update any of these later from your Profile."

Footer: ghost "← Back" left + ghost "Skip this step →" + primary lg full-width "Find My Scholarships →" (Lucide ArrowRight).

"Draft saved" indicator top-right with Lucide Check.

Lucide icons only. Sora/IBM Plex Sans/Mono via Google Fonts. Brand "AidwiseAI". Footer "© 2026 AidwiseAI".
```

---

## 7. Signup — Desktop (NEW — generate via generate_screen_from_text, DESKTOP)
```
AidwiseAI signup page (/signup). Public route, no sidebar. Page bg #F7F5F0.

Top sticky brand bar h-16 bg #FFFDF9/95 backdrop-blur, border-bottom 1px rgba(12,17,23,0.08): "AidwiseAI" wordmark Sora 700 left + nav links "How it works · Features · Pricing" text-sm #334155 + ghost sm "Sign in" right.

Centered card vertically: bg #FFFDF9 1px border rounded 20px p-10 shadow-soft max-w 420px.

Inside card:
- AidwiseAI wordmark centered Sora 700 24px #0C1117
- "Create your account" Sora 700 24px centered
- "Find fully-funded programs that match your profile." IBM Plex Sans 14px #334155 centered

Form (Label above input, gap 8px between rows):
- "Full name" input placeholder "Zara Khan"
- "Email" input placeholder "zara@example.com" — show error state text-xs #B94A48 "Enter a valid email address."
- "Password" input type=password placeholder "Min. 12 characters", Lucide Eye / EyeOff inside right of input. Helper text-xs #64748B below: "At least 12 characters" (NOTE: backend Pydantic requires ≥12 — must read 12, not 8).
- Primary lg full-width button "Create account →" bg #0C1117 text #FFFDF9 rounded 12px h-12

Divider "or": 1px #E7E1D5 lines either side, "or" text-xs #64748B center.

Secondary full-width md button with Lucide Chrome icon "Sign up with Google" (greyed, "Coming soon" tooltip on hover).

Centered link text-sm "Already have an account? Sign in →" — link color #2E5B9A.

Legal footnote text-xs #64748B max-w 300px centered: "By creating an account, you agree to our Terms of Service and Privacy Policy."

Bottom footer: "© 2026 AidwiseAI" centered text-xs #64748B.

Lucide icons only. Sora/IBM Plex via Google Fonts. Focus-visible ring 2px #2E5B9A. Tap targets ≥44×44.
```

---

## 8. Login — Desktop (NEW — generate via generate_screen_from_text, DESKTOP)
```
AidwiseAI login page (/login). Public route, no sidebar. Page bg #F7F5F0.

Top sticky brand bar identical to signup with "AidwiseAI" wordmark.

Centered card: bg #FFFDF9 1px border rounded 20px p-10 shadow-soft max-w 420px.

Card contents:
- AidwiseAI wordmark centered Sora 700 24px
- "Welcome back" Sora 700 24px centered
- "Sign in to your AidwiseAI account." IBM Plex Sans 14px #334155 centered

Form:
- "Email" input placeholder "you@example.com"
- Row above password: "Password" label LEFT + "Forgot password?" link RIGHT (text-xs #2E5B9A)
- "Password" input type=password with Lucide Eye / EyeOff toggle inside
- Primary lg full-width button "Sign in →" bg #0C1117 text #FFFDF9

Error block (caution-stripe — border-left 3px #B94A48 bg #F4D8D6 rounded 12px p-3 between button and the demo row): Lucide AlertTriangle 16px #B94A48 + "Invalid email or password. Try again."

Demo-fill row: two secondary sm buttons inline — "Student demo" prefills student@example.com / strongpass1; "Admin demo" prefills admin@example.com / strongpass1. Helper text-xs #64748B above row: "Tap to prefill seeded demo credentials."

Centered link "Don't have an account? Sign up →" — link color #2E5B9A.

Bottom footer: "© 2026 AidwiseAI" centered text-xs #64748B.

Lucide icons only. Sora/IBM Plex via Google Fonts. Tap targets ≥44×44.
```

---

## 9. Dashboard — Desktop (EDIT screen `721e9473dc584e6084b8a0bf5e3d8107`)
```
Refine Dashboard /feed.

Sticky Demo Mode Banner directly under TopBar (Elite users): bg #F5EDD6 border-bottom 1px rgba(139,105,20,0.2) text #8B6914 text-sm py-2.5 px-6. Content: Lucide Star + "Demo mode — all Elite features unlocked." + "In production: Pro PKR 2,499/mo · Elite PKR 7,999/mo" + Lucide X dismiss 32×32 ghost.

Header: "Hi, Zara." Sora 700 30px + "You have 3 deadlines in the next 60 days." text-base #334155.

Incomplete Profile Nudge above action grid (only when missing target_countries or gpa_value): caution-stripe — border-left 3px #B7791F bg #F4E7CF 1px border rgba(183,121,31,0.2) rounded 12px p-4 text #B7791F. Lucide AlertTriangle + "Complete your profile to get accurate matches" + sub "You're missing IELTS score and target countries." + right ghost "Complete profile →".

Action Grid 2×2 cards bg #FFFDF9 1px border rounded 16px p-6 min-h 160px:
- Lucide GraduationCap → "Find Scholarships" / "Get matched to programmes you actually qualify for." → /dashboard/scholarships/match
- Lucide Mic → "Practice Visa Interview" / "UK, USA, Canada, Germany. AI feedback on every answer." → /dashboard/interview
- Lucide FileText → "Write Your SOP" / "AI-assisted, Pakistani context, Chevening-ready." → /dashboard/documents/sop
- Lucide LayoutDashboard → "Application Tracker" / "Track deadlines and document checklists." → /dashboard/tracker
Each card has Lucide ArrowRight 18px #64748B bottom-right.

"Your top matches" text-lg weight 600 + 3 compact cards (h ~88px bg #FFFDF9 1px border rounded 12px p-3.5 px-5): Flag 20px + name weight 600 + meta line text-xs #64748B + 2 validated-stripe chips Lucide Check "CGPA 3.7 qualifies" "IELTS 7.0". Right: match % weight 700 #426B5A + [View] ghost generated + [+ Tracker] secondary sm. Below: ghost link "See all matches →".

Tracker Summary Widget: "Applications in progress" text-base weight 600. Stage strip 6 segments text-sm #334155: "Researching (2) | Preparing (1) | Applied (0) | Interview (0) | Decision (0) | Accepted (0)". Near-deadline row danger-stripe (border-left 3px #B94A48 bg #F4D8D6 rounded 12px p-3.5): Lucide AlertTriangle + "Chevening (UK) — deadline in 12 days · 3 documents missing" + ghost "Go to tracker →".

Sidebar 240px sticky md+: brand header "AidwiseAI" Sora 600 text-lg + groups EXPLORE / APPLY / ACCOUNT / UPGRADE with Lucide icons (Home, Search, Compass, Bookmark, LayoutDashboard, FileText, Mic, User, Settings, Star). UPGRADE active item text #8B6914 bg #F5EDD6 rounded 12px. Footer of sidebar: avatar (32px initials) + name + email text-xs #64748B + ghost "Sign out" (turns danger #B94A48 hover, Lucide LogOut).

Replace ALL Material icons with Lucide. Fonts Sora/IBM Plex Sans/Mono via Google Fonts. Footer "© 2026 AidwiseAI. All rights reserved." (replace any © 2024).
```

---

## 10. Scholarship Match — Desktop (EDIT screen `6931780275874cfc9c6e89a2d9db6e92`)
```
Refine Scholarship Match cards with required semantic stripes.

Page header "Scholarships matched to your profile" Sora 700 24px + "Based on: NUST · CS · CGPA 3.7 · IELTS 7.0 · UK, Germany · Fully funded" #64748B + ghost "Edit profile" link.

Summary bar bg #F5EDD6 1px rgba(139,105,20,0.2) rounded 12px p-4 text #8B6914: "4 fully funded scholarships match your profile. 9 more available with Pro, including 2 closing in 47 days." + gold sm button "Upgrade to Pro →".

Tabs [Eligible (4)] [Partially Eligible (3)] [Stretch (5)]. Active tab text #0C1117 weight 600 + 2px bottom border #0C1117.

Each Eligible card needs:
- Header: country flag 20px + name Sora 600 18px + "FULLY FUNDED" badge tone=validated (bg #DDE9E2 text #426B5A) right.
- Provider sub-line #334155 text-sm.
- VALIDATED-STRIPE block (border-left 3px #426B5A bg #DDE9E2 rounded 12px p-3.5): Lucide Check 16px + "Your 3.7 CGPA from NUST is approximately a 3.7 US GPA." + "Qualifies for programs requiring min 3.0."
- Meta row: Lucide Calendar + "Deadline in 47 days (Nov 2025)" (color by urgency: >60d #334155, 31–60d #B7791F, ≤30d #B94A48) + right "GBP 18,000 / year" weight 600.
- Eligibility chips: Lucide CheckCircle "IELTS 7.0", "Min CGPA 3.0", Lucide GraduationCap "Masters".
- GENERATED-STRIPE block (border-left 3px #2E5B9A bg #DCE6F4 rounded 12px p-3.5): Lucide Sparkles + label "Match reason" IBM Plex Mono uppercase #2E5B9A 11px + body "Matches your CGPA, IELTS score, CS focus, and UK target."
- Footer row: secondary sm "View Details" + primary sm "+ Add to Tracker" (Lucide Plus).

Partially Eligible cards swap validated-stripe for CAUTION-STRIPE: Lucide AlertTriangle + "Missing: IELTS score. Add it to qualify fully." + ghost "Update profile →".

Free-tier blur: results 4+ are rendered blur-sm opacity-50 pointer-events-none under UpgradeWall card centered: Lucide Lock (paper-warm circle) + eyebrow "Scholarship matches" font-mono uppercase + headline Sora 600 "9 more scholarships match your profile, including 2 fully funded ones closing in 47 days." + primary "Upgrade to Pro — PKR 2,499/mo →" + footnote "No consultant. No hidden fees. Cancel anytime."

Replace Material icons with Lucide. Fonts Sora/IBM Plex Sans/Mono via Google Fonts. Brand "AidwiseAI". Footer "© 2026 AidwiseAI".
```

---

## 11. SOP Builder — Desktop (EDIT screen `01ff1adc931e46fda7941ad96be6c8c1`)
```
Refine SOP Builder preview panel to spec §9.3.

Two-panel split: LEFT 40% input (bg #F7F5F0), RIGHT 60% preview (bg #FFFDF9). 1px vertical divider.

INPUT panel: scholarship selector top "Targeting a scholarship?". Step progress 4-step strip "Academic Background → Research & Work → Why This Program → Goals & Pakistan". 4 stacked steps with pre-filled NUST/CS context fields + textareas (Career goals helper: "For Chevening / HEC, mention intention to return to Pakistan."). Sticky CTA primary lg full-width "Generate SOP Draft →" Lucide Sparkles prefix.

PREVIEW panel after generation:
- Action bar (secondary sm): Lucide Copy "Copy" · Lucide Download "Download .txt" · Lucide RefreshCw "Regenerate" · ghost Lucide ArrowLeft "Edit inputs"
- Word count right: "743 words · 6 paragraphs" text-xs #64748B
- 6 paragraphs each prefixed with IBM Plex Mono 12px uppercase tracking-[0.1em] weight 700 #64748B label, mt-6 mb-2:
  1. OPENING
  2. ACADEMIC BACKGROUND
  3. RESEARCH & EXPERIENCE
  4. MOTIVATION FOR THIS PROGRAM
  5. CAREER GOALS
  6. CLOSING
  Each paragraph 100–150 words IBM Plex Sans 15px leading 1.7, with 1px rgba(12,17,23,0.08) divider between. Total 600–800 words. Pakistani context: NUST CS, Chevening UK target, CGPA 3.7, IELTS 7.0, intent to return.
- Whole body wrapped in generated-stripe: border-left 3px #2E5B9A, bg #DCE6F4 10% opacity, p-6, header Lucide Sparkles "Generated draft · revisit before submitting."
- Validated facts callout — validated-stripe (border-left 3px #426B5A bg #DDE9E2 rounded 12px p-4): Lucide Check + "Scholarship facts used — Verified source" + "Chevening requires 2 years of work experience. Deadline: November 5, 2025. Award: GBP 18,000."
- Elite line-by-line feedback per paragraph (paragraph 3 expanded by default): accordion "+ Feedback v" with 3 sub-blocks:
   - validated-stripe + Lucide Check "What works well"
   - caution-stripe + Lucide AlertTriangle "What to improve"
   - generated-stripe + Lucide Sparkles "Suggested rewrite"
- Bottom disclaimer caution-stripe (border-left 3px #B7791F bg #F4E7CF p-4): Lucide AlertTriangle + "This draft is AI-generated from your inputs. Personalise it — admissions committees can detect generic AI writing. Add specific details only you know."

Mobile: tab switcher [Form] [Preview], content stacked.

Replace Material icons with Lucide. Fonts Sora/IBM Plex Sans/Mono via Google Fonts. Brand "AidwiseAI". Footer "© 2026 AidwiseAI".
```

---

## 12. Visa Simulator — Desktop (EDIT screen `4ed7275cef644700978061b4d53b0ada`)
```
Extend Visa Interview Simulator beyond setup. Render 4 sections stacked vertically:

SECTION 1 Setup (refine): "Visa Interview Practice" Sora 700 24px + "Practice with an AI visa officer. Get feedback on every answer." #334155.
"STEP 1 — Which visa are you practising for?" font-mono uppercase. 4 country flag cards w-180px p-6 bg #FFFDF9 border 2px rounded 16px: 🇬🇧 UK Student Visa (20q) · 🇺🇸 USA F-1 (20) · 🇨🇦 Canada Study Permit (15) · 🇩🇪 Germany Student Visa (15). Selected: border #0C1117 bg #F1EDE4 + Lucide Check 20px overlay.
"STEP 2 — How do you want to practise?" — 2 mode cards: Study Mode (Lucide BookOpen, "full AI feedback after every answer, red-flag detection, ideal answer shown") · Exam Mode (Lucide Clock, "no feedback between questions, timer visible, builds endurance").
Primary lg "Start Practice Session →" disabled until both chosen. Sub "10 questions · about 15–20 minutes."

SECTION 2 Q&A (Study Mode mid-session):
Top bar: Lucide ArrowLeft "Exit" ghost left · "Question 3 of 10" center · "05:42" font-mono right. Progress bar h-1.5 bg #E7E1D5 fill #0C1117 at 30%.
Question card bg #FFFDF9 1px border rounded 20px p-10: Category badge caution-soft #F4E7CF text #B7791F weight 600 12px "Ties to Pakistan". Question Sora 600 20px leading 1.4: "What ties do you have to Pakistan that will bring you back after your studies?" Hint #64748B text-sm: "Visa officers want specific numbers and confirmed funding sources. Vague answers raise red flags."
Textarea min-h 160px bg #FFFDF9 1px border rounded 12px focus ring 2px #2E5B9A placeholder "Type your answer as you would speak it. Be natural, not rehearsed." Char count "0 / no limit" right. Primary lg full-width "Submit Answer →" + ghost "← Previous question".

SECTION 3 Feedback Panel:
Card bg #FFFDF9 1px border rounded 16px p-7 mt-4. Three score meters side-by-side: Clarity 4.2 / Confidence 3.5 / Relevance 4.6. Bar h-2 bg #E7E1D5 fill validated #426B5A (4–5), caution #B7791F (3–3.9), danger #B94A48 (<3).
Red flag block danger-stripe (border-left 3px #B94A48 bg #F4D8D6 p-3.5): Lucide AlertTriangle + "Red flag detected: 'family in UK' phrased without context — clarify the relationship is unrelated to your study plan."
Three labeled blocks each with stripe:
- validated-stripe + Lucide Check "What you did well"
- caution-stripe + Lucide AlertTriangle "What to include next time"
- generated-stripe + Lucide Sparkles "Strong answer includes"
CTA primary full-width "Next Question →" + sub #64748B "Question 4 of 10 · Finances".

SECTION 4 Session Summary:
"Session Complete" Sora 700 24px + "🇬🇧 UK Student Visa · Study Mode · 10 questions" text-sm #64748B. Radar chart SVG 4 axes Clarity·Confidence·Relevance·Red Flag Avoidance. Overall "3.8 / 5.0" Sora 700 36px #426B5A + "Good preparation level". 3 "Areas to improve" ranked cards. Question-by-question table with score cells (validated 4–5, caution 3–3.9, danger <3). Actions: secondary "Practice Again" + secondary "Download Summary" + gold "Download Full Transcript" (Elite only badge) + ghost "← Back to dashboard".

Bottom disclaimer caution-stripe: Lucide AlertTriangle + "Approval-rate badges are educated estimates (0.62–0.85), not measured statistics. Use them as a directional signal, not a guarantee."

Replace Material icons with Lucide. Fonts Sora/IBM Plex Sans/Mono via Google Fonts. Brand "AidwiseAI". Footer "© 2026 AidwiseAI".
```

---

## 13. Upgrade — Desktop (EDIT screen `870571a417d14fe0a15517fa02de4682`)
```
Refine Upgrade page to spec §11.

Sticky Demo Mode Banner directly below top bar: bg #F5EDD6 border-bottom 1px rgba(139,105,20,0.2) text #8B6914 text-sm py-2.5 px-6. Content: Lucide Star 16px + "Demo mode — all Elite features unlocked." + "In production: Pro PKR 2,499/mo · Elite PKR 7,999/mo" + Lucide X dismiss 32×32 ghost.

Header centered: "Find the right plan for you" Sora 700 36px + "Start free. Upgrade when you're serious." #334155.

Currency switcher centered — five pill buttons in order PKR · GBP · EUR · AED · USD. Active pill bg #0C1117 text #FFFDF9 rounded 12px h-9 px-4. Inactive bg #F1EDE4 text #334155. Default PKR. Inline note "Prices update instantly — no reload."

Four pricing cards in a 4-column grid:
a) Explorer (Free Forever) — standard card · [Start free] secondary CTA.
b) Pro (PKR 2,499/mo) — 2px gold #8B6914 ring + shadow-soft + "Most popular" badge (tone gold). [Get Pro →] gold lg. Variants: GBP 6.99/mo · EUR 7.99/mo · AED 29/mo · USD 8.99/mo.
c) Elite (PKR 7,999/mo) — "For serious applicants" badge (generated tone). [Get Elite →] primary lg. Variants: GBP 19.99 · EUR 22.99 · AED 89 · USD 24.99.
d) Institution (Contact us) — bg #F1EDE4 1px dashed border, no price. [Contact us →] secondary linking to `mailto:partnerships@aidwiseai.pk`. The mailto MUST be visible below button as footnote in #8B6914 text-xs: "partnerships@aidwiseai.pk".

Feature rows inside cards: included = Lucide Check (validated #426B5A); excluded = em-dash (—) in #64748B.

Anchor copy under Pro: "2 months of AidwiseAI Pro = less than 1 consultant meeting." Under Elite: "For Pakistani families in the UK or UAE, less than a coffee per week."

Waitlist accordion inside Pro and Elite cards (collapsed by default, expand when CTA clicked): "Join the Pro waitlist" + "Payments launching soon. We'll email you first." Email input + gold full-width "Join Pro Waitlist →". Post-submit state: validated-stripe block with Lucide Check + "You're on the list! We'll email you when Pro launches."

Comparison table "Compare all features" below cards. Columns Feature | Explorer | Pro | Elite | Institution. Category rows (bg #E7E1D5 uppercase weight 700 #64748B): SCHOLARSHIP DISCOVERY · SOP BUILDER · VISA INTERVIEW · TRACKER · ELITE EXCLUSIVE · B2B. Check = Lucide Check, em-dash = excluded, Lucide Star = Elite only. Pro column subtle gold tint. Header row bg #F1EDE4.

Footer trust signals "No consultant. No hidden fees. Cancel anytime." centered text-sm #64748B.

Replace Material icons with Lucide. Fonts Sora/IBM Plex Sans/Mono via Google Fonts. Brand "AidwiseAI". Footer "© 2026 AidwiseAI".
```

---

## 14. Legal & Settings — Privacy panel (EDIT screen `a242d1b435ce458ca3a102bf671584a0`)
```
Rebuild Legal & Settings to spec §12 + PRD legal seeds.

Header: "Privacy & data" Sora 700 24px + "Control your consent, export your data, and manage account deletion under PDPB-Pakistan compliance." #334155.

Legal documents card (bg #FFFDF9 1px border rounded 16px p-6) — FIVE rows, each with doc name weight 600 + "v1.0 · Effective 2026-05-15" text-xs #64748B + "Review" link (Lucide ExternalLink). Five docs:
- Terms of Service
- Privacy Policy
- Data Processing Agreement (DPA)
- Acceptable Use Policy
- Cookie Policy
Each row right side: consent status chip "Granted v1.0 · 2026-05-15" tone=validated (Lucide Check).

Pakistan PDPB callout (validated-stripe, border-left 3px #426B5A bg #DDE9E2 rounded 12px p-4): Lucide ShieldCheck + "AidwiseAI complies with PDPB-Pakistan. We never collect sensitive categories (religion, political opinion, biometric data). Your consent grants log IP, user-agent, and a sha256 of the document body. We retain consent audit records for 7 years."

Liability + dispute resolution disclosure (caution-stripe, border-left 3px #B7791F bg #F4E7CF rounded 12px p-4): Lucide Scale + "Liability cap: PKR 1,000 or 6 months of fees, whichever is greater. Disputes resolved by LCIA arbitration. Class-action waiver applies. Read full Terms of Service v1.0."

Cookie & analytics consent toggles card (bg #FFFDF9 1px border rounded 16px p-6):
- "Cookie preferences" header
- Row 1 "Essential" — always-on disabled toggle, helper "Required to keep AidwiseAI working."
- Row 2 "Analytics" — toggle off default, helper "Helps us understand how students use the product. No PII shared."
- Row 3 "Marketing" — toggle off default, helper "Personalised tips and newsletters."
- Persistence row: Lucide Info + "Choices persist to your account and a session cookie. Re-shown when the consent doc version changes (server returns HTTP 451)."

Data export card (bg #FFFDF9 1px border rounded 16px p-6): "Download my data" weight 600 + helper "We'll prepare a JSON+CSV bundle of your profile, matches, tracker, and SOP drafts. Email link expires after 7 days." Primary button "Request export →" Lucide Download. Status chip area.

Account deletion card (danger-stripe, border-left 3px #B94A48 bg #F4D8D6 rounded 12px p-4): "Delete my account" weight 600 + helper "Your account will be deactivated immediately and permanently deleted after a 30-day grace window. You may cancel deletion any time before day 30. Some legal records (consent audit, payment receipts) are retained as required by Pakistani law." Danger button "Request deletion →" Lucide Trash2. Typed-confirm dialog (type 'DELETE' to confirm).

Bottom footer "© 2026 AidwiseAI" + contact "partnerships@aidwiseai.pk".

Replace ALL Material icons with Lucide React SVG. Sora/IBM Plex Sans/Mono via Google Fonts. Update any dates to 2026-05-15.
```

---

## 15. Legal Viewer — Privacy Policy (NEW — generate via generate_screen_from_text, DESKTOP)
```
AidwiseAI legal viewer page /legal/[slug] — rendering the Privacy Policy v1.0 (PDPB-Pakistan).

Top nav: "AidwiseAI" wordmark + back link "← Back to settings".

Article container max-w 65–75ch centered (~720px) p-8 page bg #F7F5F0:

H1 Sora 700 36px: "Privacy Policy"
Sub line text-sm #64748B: "Version 1.0 · Effective 2026-05-15 · Document hash sha256:abc123…"

Section headings Sora 600 24px, body IBM Plex Sans 15px leading 1.7 #334155. 1px #E7E1D5 divider between sections.

Sections (use Pakistani PDPB compliance language):
1. Information we collect — academic profile, target countries, test scores, scholarship interactions. NEVER religion, political opinion, biometric data.
2. How we use your information — match scholarships, build SOP drafts, generate visa interview feedback, send deadline reminders.
3. Legal basis under PDPB-Pakistan — explicit consent grants logged with IP, user-agent, sha256 of doc body. Latest grant wins. Version mismatch returns HTTP 451.
4. Sharing with universities (B2B) — only with `b2b_share_consent=true` AND signed DPA. Snapshot at share time; no retro-leak.
5. Cookies — essential, analytics (opt-in), marketing (opt-in).
6. Your rights — access, correction, deletion (30-day grace), portability (data export JSON+CSV).
7. Data retention — 7-year consent audit retention; account data deleted after 30-day window.
8. Liability — PKR 1,000 or 6 months of fees, whichever is greater (per Terms v1.0).
9. Dispute resolution — LCIA arbitration, class-action waiver, Pakistan as governing jurisdiction.
10. Contact — privacy@aidwiseai.pk, partnerships@aidwiseai.pk.

Sticky action bar bottom (bg #FFFDF9 border-top 1px shadow-soft): "I have read and agree to Privacy Policy v1.0" + primary lg button "I agree, version 1.0" (posts to `POST /privacy/consent`).

Replace any Material icon with Lucide React SVG. Fonts Sora/IBM Plex Sans via Google Fonts. Footer "© 2026 AidwiseAI".
```

---

## How to apply this pack

### Option A — Stitch Web UI (most reliable)
1. Open https://labs.google.com/stitch and the "AidwiseAI Scholarship Platform" project.
2. For each EDIT prompt: click the target screen, hit Edit, paste the prompt, choose model **Gemini 3.1 Pro** (highest fidelity) or **Gemini 3 Flash** (faster), run. Wait 1–3 min.
3. For each NEW (generate) prompt: hit Generate, paste, run.
4. Order by priority: §9 Dashboard-Desktop, §11 SOP, §12 Visa, §10 Match, §13 Upgrade, §14 Legal, §1 Landing-Desktop, then onboarding 1/3/4/5, then signup/login, then §15 legal viewer, then §2 Landing-Mobile.

### Option B — Stitch MCP from Claude Code (slower, throttle-prone)
Re-run the same prompts via `mcp__stitch__edit_screens` / `mcp__stitch__generate_screen_from_text`. Use `modelId: "GEMINI_3_FLASH"`, send ONE op per call, wait 2–3 min before the next.

### Option C — Skip Stitch, write to codebase
The actual frontend lives at `frontend/src/`. Bypass Stitch and patch the live components per spec — that's what ships anyway.

## Verification gate (run after each screen)
Per `frontend/CLAUDE.md` PR-blocking rules:
- No Material Symbols.
- All AI-generated blocks wrapped in generated-stripe + Sparkles.
- All validated facts wrapped in validated-stripe + Check.
- Sora + IBM Plex Sans + IBM Plex Mono declared.
- Brand reads "AidwiseAI".
- 44×44 tap targets, focus-visible ring 2px #2E5B9A.
- LCP <1.8s, INP <200ms, initial JS ≤180KB gzipped.

— End of pack —
