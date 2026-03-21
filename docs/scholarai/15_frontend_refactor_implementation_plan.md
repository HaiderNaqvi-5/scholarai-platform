# ScholarAI Frontend Refactor Implementation Plan

## Purpose
This plan translates the ScholarAI frontend design-direction prompt into an implementation-ready, end-to-end refactor plan for the current Next.js + TailwindCSS frontend. It covers visual direction, page architecture, component strategy, and a feature-by-feature function-level delivery backlog.

## 1) Design DNA Synthesis
### Layout
- Apply Apple-like spatial restraint: fewer competing panels per viewport, stronger primary column hierarchy.
- Apply Stripe-like section sequencing: each screen should move from summary -> detail -> action.
- Apply Linear/Vercel shell discipline: clear top-nav + predictable content container + consistent section rhythm.
- Apply Notion clarity: dense content stays readable through strict grouping and heading order.

### Typography
- Keep existing font stack (`Sora`, `IBM Plex Sans`, `IBM Plex Mono`) and standardize semantic roles:
  - Display: landing hero + major dashboard section titles.
  - UI text: all controls, labels, explanatory paragraphs.
  - Mono: provenance values, IDs, score labels, timestamps.
- Enforce fixed scale tokens for title/subtitle/body/label/caption to prevent ad hoc sizing.

### Spacing
- Keep existing 4/8/12/16/24/32/48/64 scale and enforce one vertical rhythm per surface.
- No one-off spacing values in component-level utility classes unless introduced as tokenized exceptions.

### Hierarchy
- Facts before guidance (core trust model): validated data blocks always appear before generated guidance blocks.
- One primary call-to-action per section; secondary actions visually downgraded.
- Use section headers (`PageHeader`) with explicit eyebrow/title/description on all core surfaces.

### Color
- Preserve current restrained light system (`paper`, `ink`, `sage`, `sky`, `amber`, `coral`).
- Reduce decorative accents; use color almost exclusively for state, interaction, and data emphasis.
- Map states consistently:
  - Validated = sage
  - Generated/advisory = sky
  - Warning/review = amber
  - Error/blocked = coral

### Motion
- Keep short fade/slide transitions only for page-level structure reveal.
- Remove ornamental movement from data-dense areas.
- Motion should confirm navigation, state change, or progressive disclosure only.

### Interaction Design
- Progressive disclosure for explanations: summary first, detailed rationale on demand.
- Keep filters persistent on browse/recommendation surfaces.
- Preserve low-friction save/unsave, compare, and follow-up flows.

### Product Storytelling
- Landing should communicate trust contract:
  - curated facts
  - explainable recommendations
  - preparation support
- Product pages should narrate user progress instead of feature lists.

### Trust Design
- Continue explicit separation of:
  - validated scholarship facts
  - student input
  - generated suggestions
  - limitations/disclaimers
- Add consistent provenance blocks and “what to verify” modules everywhere recommendations appear.

### Dashboard Design
- Standardize dashboard shell pattern: KPI strip -> active work modules -> context modules.
- Keep cards dense but not noisy; no crowded badge clusters.

### Admin Design
- Shift admin from generic metrics tiles to operational workflows:
  - queue state
  - record quality
  - source health
  - action logs
- Keep enterprise clarity without heavy enterprise chrome.

### Form Design
- Keep explicit labels above inputs (no placeholder-only fields).
- Group fields by decision model relevance, not database structure.
- Add inline validation with specific corrective guidance.

## 2) ScholarAI Visual Positioning
ScholarAI should sit at:
- **35% Apple calm restraint**
- **25% Stripe structural clarity**
- **20% Vercel/Linear product sharpness**
- **10% Notion approachability**
- **10% Clerk/Supabase/Attio operational trust**

Practical interpretation:
- The product should look premium and intentional first (Apple), then understandable (Stripe), then precise (Vercel/Linear).
- It should remain academically approachable (Notion) while clearly production-grade in dashboard/admin operation (Clerk/Supabase/Attio).
- Visual novelty is subordinate to legibility, trust, and implementation consistency.

## 3) Ranked Inspiration Usage Map By ScholarAI Surface
| ScholarAI surface | Primary inspiration | Secondary inspiration |
|---|---|---|
| Landing page | Apple, Stripe, Framer | Raycast, Vercel |
| Navigation | Vercel, Linear | Notion |
| Onboarding | Notion, Clerk | Stripe |
| Profile setup | Notion, Clerk | Supabase |
| Recommendations UI | Linear, Vercel | Stripe, Attio |
| Recommendation explanations | Stripe, Notion | Supabase |
| Saved opportunities | Notion, Linear | Attio |
| Student dashboard shell | Linear, Vercel | Notion, Raycast |
| Document assistance | Notion, Stripe | Anthropic, Superhuman |
| Interview practice | Superhuman, Linear | Notion |
| Curator/admin dashboard | Retool, Supabase, Clerk | Brex, Ramp, Figma admin |
| Data review tables | Attio, Figma admin, Retool | Airtable, Brex |
| Settings/account pages | Clerk, Notion | Supabase |

## 4) ScholarAI Design Rules
### Must always be true
1. Facts are visually and structurally separate from generated guidance.
2. Every page has one clear primary action.
3. State badges and status language are consistent across all surfaces.
4. Typography defines hierarchy; decorative containers do not.
5. Components render predictably across desktop and mobile without re-invented layouts.

### Must be avoided
1. Template-like hero blocks with generic gradient spectacle.
2. Arbitrary card styles between features.
3. Multiple competing emphasized actions in one panel.
4. Mixed semantic meanings for the same color/badge pattern.

### Premium feel comes from
- strict spacing cadence
- restrained color use
- high-quality typography hierarchy
- concise interaction states
- clean, low-noise shells

### Trustworthy feel comes from
- provenance first
- visible limitations
- explicit “verify this” guidance
- consistent error and recovery patterns

### Academic but modern comes from
- clear analytical structure (headings, labels, tables, rationale blocks)
- minimal ornament
- contemporary typography and component polish

### Crafted dashboard feel comes from
- unified shell
- consistent card density
- reusable section archetypes
- deliberate motion and transitions

### Operationally strong admin without heaviness comes from
- workflow-first layouts
- compact but legible tables
- action-focused row controls
- contextual detail drawers instead of full-page jumps for every task

## 5) Anti-Pattern List (Explicit Rejections)
Reject:
1. Template-feeling hero sections and stock “AI productivity” visual language.
2. Excessive gradients and neon glow accents.
3. Cluttered equal-weight card grids.
4. Weak type hierarchy where labels, values, and headings blend together.
5. Random animations not tied to user intent.
6. Noisy dashboards with too many badges and decorative containers.
7. UI over-explanation that hides core user actions.
8. Flashy, low-credibility visuals for scholarship and eligibility contexts.
9. Obvious AI-generated composition habits (symmetry without purpose, repeated blocks, filler copy).
10. Generic admin-panel kit aesthetics.
11. Legacy enterprise table leftovers with cramped unreadable rows.
12. Sidebars/shells that look copied from standard SaaS kits.

## 6) Page-By-Page Design Direction
### Landing page (`/`)
- Layout: narrative marketing shell with trust rail + feature proof sections.
- Tone: calm, confident, academically credible.
- Density: low-to-medium.
- Hierarchy: value proposition -> trust model -> workflow.
- Interaction: clear route into signup and scholarship browse.
- Inspiration: Apple + Stripe + Framer.

### Recommendations page (`/recommendations`)
- Layout: two-column workspace (ranked list + profile/trust context).
- Tone: analytical and transparent.
- Density: medium-high.
- Hierarchy: recommendation summary -> rationale -> constraints -> action.
- Interaction: save/unsave, detail drill-in, rationale expand/collapse.
- Inspiration: Linear + Stripe + Supabase.

### Student dashboard (`/dashboard`)
- Layout: KPI row + profile state + shortlist + next actions.
- Tone: focused progress tracking.
- Density: medium.
- Hierarchy: account readiness -> active work -> exploration.
- Interaction: continue workflow via clear next-step cards.
- Inspiration: Linear + Notion + Vercel dashboard.

### Saved opportunities page (new `/saved`)
- Layout: shortlist-focused page with sorting/filtering and follow-up states.
- Tone: practical and deadline-aware.
- Density: medium.
- Hierarchy: urgent deadlines first, then recently saved.
- Interaction: bulk unsave, compare, open details.
- Inspiration: Attio + Notion + Ramp.

### Document feedback page (`/document-feedback`)
- Layout: editor/feedback split with evidence-backed guidance sections.
- Tone: coaching without overclaiming.
- Density: medium-high.
- Hierarchy: document state -> grounded feedback -> generated guidance -> next edits.
- Interaction: save draft, request feedback, section-level improvements.
- Inspiration: Notion + Stripe + Anthropic.

### Interview practice page (`/interview`)
- Layout: session timeline + rubric panel + follow-up prompts.
- Tone: focused, constructive, confidence-building.
- Density: medium.
- Hierarchy: current prompt -> response -> score breakdown -> recommended next attempt.
- Interaction: mode selection, attempt loop, trend tracking.
- Inspiration: Superhuman + Linear.

### Curator/admin dashboard (`/curation`, `/admin`)
- Layout: operational overview + actionable queues + source/run health.
- Tone: serious, clean, operational.
- Density: high (controlled).
- Hierarchy: queue health -> blocking issues -> record actions.
- Interaction: approve/reject/publish with contextual evidence and audit metadata.
- Inspiration: Retool + Supabase + Clerk + Brex.

### Record review/detail screen (new admin detail route)
- Layout: split view (record fields + provenance/events/actions).
- Tone: audit-focused.
- Density: high.
- Hierarchy: canonical data -> source evidence -> change history.
- Interaction: field-level edits, validation flags, publish controls.
- Inspiration: Attio + Figma admin + Airtable.

### Settings/account screen (new `/settings`)
- Layout: compact sections for profile, security, notification, preferences.
- Tone: trustworthy and non-marketing.
- Density: medium.
- Hierarchy: account integrity first, preference second.
- Interaction: inline save with clear success/error responses.
- Inspiration: Clerk + Supabase + Notion.

## 7) Component-Level Design Direction
- **Buttons:** solid primary, subtle secondary, text tertiary; consistent heights and radii.
- **Inputs:** clear labels, helper text, explicit error states, predictable focus rings.
- **Select/dropdowns:** concise options, grouped semantics, keyboard-first interaction.
- **Cards:** purposeful containers only; avoid decorative nesting.
- **Tables:** high-legibility headers, zebra-optional, sticky heading where needed, compact actions.
- **Filters:** persistent and visible, not hidden behind heavy modal interactions.
- **Tabs:** clear active indicator, no ambiguous state styling.
- **Nav bars:** stable structure; section labels use consistent emphasis.
- **Sidebars:** only where task density requires it; avoid generic SaaS shell look.
- **Modals:** short decision flows and confirmations; move complex editing to panels/pages.
- **Progress/status indicators:** map to badge system with clear language.
- **Feedback/explanation blocks:** always separate facts from generated advice.
- **Dashboard widgets:** standardized KPI + context + action pattern.
- **Admin tables/row actions:** compact primary actions plus overflow for secondary tasks.
- **Record detail panels:** field-level provenance and audit trace visible by default.

## 8) Design System Implementation Brief (Next.js + TailwindCSS)
### Design token direction
1. Introduce tokenized CSS variables in `frontend/src/app/globals.css` for:
   - color semantic roles
   - typography scale
   - spacing and radius
   - motion durations/easing
2. Bind Tailwind utility usage to semantic tokens, not raw color literals.

### Reusable primitive strategy
Add a normalized primitive layer in `frontend/src/components/ui/`:
- `Button`
- `Input`
- `Select`
- `Card`
- `Table`
- `Badge`
- `Section`
- `EmptyState` (existing, upgrade into primitive usage)
- `PageHeader` (existing, become mandatory page section header primitive)

### Consistency rules
- No new page-specific button/input styles once primitives exist.
- Status mappings must route through a single badge variant resolver.
- Explanation and provenance modules must use shared composition primitives.

### Layout system rules
- Standard page container widths and section spacing.
- Shared two-column workspace pattern for data + context pages.
- Reusable grid templates for dashboard/admin KPI and list sections.

### Dashboard shell rules
- Keep `AppShell` as single source for authenticated navigation shell.
- Add slot APIs for:
  - KPI strip
  - workspace sections
  - right-rail context panels (optional)

### Admin shell rules
- Reuse `AppShell`, but add admin mode variants:
  - denser section spacing
  - queue/table-first defaults
  - audit metadata surfaces

### Responsive behavior principles
- Mobile: stack columns; keep action bar sticky where necessary.
- Tablet: preserve section order, reduce parallel density.
- Desktop: keep dual-column analysis flows for recommendations/admin review.

## 9) End-to-End Feature and Function Delivery Plan (Refactor Backlog)
### Phase A — Foundation (Design system + shell normalization)
1. **Tokenize global style system**
   - Files: `frontend/src/app/globals.css`
   - Add functions/classes: semantic token classes for text, surface, status, spacing.
2. **Create UI primitive layer**
   - Files (new): `frontend/src/components/ui/button.tsx`, `input.tsx`, `select.tsx`, `card.tsx`, `table.tsx`, `section.tsx`
   - Add component functions: `Button`, `Input`, `Select`, `Card`, `DataTable`, `Section`
3. **Normalize shell APIs**
   - Files: `frontend/src/components/layout/app-shell.tsx`, `marketing-shell.tsx`
   - Add props/functions: optional slot props for `topMetrics`, `primaryAction`, `contextRail`.

### Phase B — Student workflow refactor
1. **Landing refinement**
   - File: `frontend/src/app/page.tsx`
   - Add section functions/components for trust proof, workflow map, and product surfaces.
2. **Recommendations UX refinement**
   - File: `frontend/src/components/recommendations/recommendation-workspace.tsx`
   - Add functions:
     - `RecommendationCard`
     - `RecommendationRationalePanel`
     - `RecommendationConstraintPanel`
     - `useRecommendationFilters` (hook for future filtering/sorting)
3. **Dashboard restructuring**
   - File: `frontend/src/components/dashboard/dashboard-shell.tsx`
   - Add functions:
     - `DashboardKpiStrip`
     - `ProfileReadinessPanel`
     - `SavedPreviewPanel`
     - `NextStepPanel`
4. **Saved opportunities dedicated surface**
   - Files (new): `frontend/src/app/saved/page.tsx`, `frontend/src/components/saved/saved-opportunities-shell.tsx`
   - Add functions:
     - `SavedOpportunitiesShell`
     - `SavedOpportunityRow`
     - `useSavedOpportunitySort`
5. **Settings/account dedicated surface**
   - Files (new): `frontend/src/app/settings/page.tsx`, `frontend/src/components/settings/settings-shell.tsx`
   - Add functions:
     - `SettingsShell`
     - `AccountSection`
     - `PreferencesSection`

### Phase C — Preparation workflow refactor
1. **Document assistance structure**
   - File: `frontend/src/components/documents/document-assistance-shell.tsx`
   - Add functions:
     - `DocumentGroundedFactsBlock`
     - `DocumentGeneratedGuidanceBlock`
     - `DocumentLimitationsBlock`
2. **Interview practice structure**
   - File: `frontend/src/components/interview/interview-practice-shell.tsx`
   - Add functions:
     - `InterviewModeSelector`
     - `InterviewRubricPanel`
     - `InterviewTrendSummary`

### Phase D — Admin and curation maturity
1. **Admin analytics operationalization**
   - File: `frontend/src/components/admin/analytics-dashboard-shell.tsx`
   - Add functions:
     - `IngestionHealthPanel`
     - `QueueHealthPanel`
     - `SystemAlertsPanel`
2. **Curation workspace upgrade**
   - File: `frontend/src/components/curation/curation-dashboard-shell.tsx`
   - Add functions:
     - `RecordQueueTable`
     - `RecordActionToolbar`
     - `RecordProvenanceSummary`
3. **Record detail route**
   - Files (new): `frontend/src/app/curation/[recordId]/page.tsx`, `frontend/src/components/curation/record-detail-shell.tsx`
   - Add functions:
     - `RecordDetailShell`
     - `RecordFieldAuditTimeline`
     - `RecordValidationActions`

### Phase E — Cross-cutting UX quality
1. **Form consistency pass**
   - Files: profile, onboarding, auth, settings form components
   - Add utilities/hooks: `useFormFieldState`, `FieldErrorText`.
2. **Loading/empty/error state normalization**
   - Files: all major shells using `Skeleton`, `EmptyState`, error cards
   - Add component functions: `InlineErrorState`, `SectionLoadingState`.
3. **Interaction and accessibility pass**
   - Add keyboard/focus and ARIA validation for tables, filters, and actionable cards.

### Phase F — Verification and rollout
1. **Targeted checks**
   - `frontend`: `npm run lint`, `npm run typecheck`, `npm run build`
2. **End-to-end confidence**
   - Update existing browser smoke coverage for new routes (`/saved`, `/settings`, admin record detail).
3. **Release strategy**
   - Merge behind stable route migration sequence to avoid breaking existing dashboard and recommendation flows.

## MVP decision
Perform the frontend refactor as a progressive, shell-first, primitive-first rollout that preserves existing API behavior while upgrading visual trust, interaction quality, and operational maturity across student and admin surfaces.

## Deferred items
- Dark mode and brand variants.
- Advanced charting beyond current recommendation explainability needs.
- Non-essential animation systems.

## Assumptions
- Existing backend route contracts remain stable through this refactor.
- Current page and shell architecture is the baseline to evolve, not rewrite.
- The team prioritizes consistency and reliability over high-risk redesign spikes.

## Risks
- Partial primitive adoption can create mixed UI quality if old/new patterns coexist too long.
- Admin density can regress readability if spacing and table hierarchy are not enforced.
- Introducing new routes without navigation mapping updates can fragment user flow.
