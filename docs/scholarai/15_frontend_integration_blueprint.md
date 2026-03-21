# ScholarAI Frontend Integration Blueprint

## Purpose
This document translates the canonical PRD, governance rules, and current implementation into a practical frontend integration plan. It defines how the website should look and flow from landing to preparation and admin workflows, while preserving MVP boundaries and trust constraints.

## Integration Objectives
1. Keep the end-to-end student journey coherent: `Discover -> Understand fit -> Prepare -> Track`.
2. Keep validated scholarship facts visually and structurally separate from generated guidance.
3. Keep all MVP features discoverable through clear information architecture without adding scope creep.
4. Keep frontend implementation feasible for a constrained team and timeline.

## Product Surface Inventory
### Public pages
| Route | Purpose | Primary audience |
|---|---|---|
| `/` | Marketing and trust framing | New visitors |
| `/scholarships` | Search and browse published scholarships | New + returning visitors |
| `/scholarships/[scholarshipId]` | Scholarship facts and requirements detail | New + returning visitors |
| `/login` | Authentication entry | Returning users |
| `/signup` | Account creation | New users |

### Authenticated student pages
| Route | Purpose | Primary audience |
|---|---|---|
| `/onboarding` | First-time profile completion | New authenticated users |
| `/profile` | Profile maintenance | Returning users |
| `/dashboard` | Workspace hub and next actions | Returning users |
| `/recommendations` | Explainable fit-prioritized shortlist | Returning users |
| `/document-feedback` | Document submission and bounded guidance | Returning users |
| `/interview` | Structured practice sessions and rubric feedback | Returning users |

### Admin pages
| Route | Purpose | Primary audience |
|---|---|---|
| `/curation` | Review and publish scholarship records | Curators / admins |

## Global IA And Navigation Model
### Marketing shell (public)
- Top nav: `Scholarships`, `How it works`, auth actions (`Login`, `Get started`).
- Hero message: constrained value proposition (Canada-first, MS-focused, trust model).
- CTA priority:
  1. `Get started` for conversion.
  2. `Browse scholarships` for immediate utility.

### App shell (authenticated)
- Primary nav sequence (left-to-right): `Scholarships`, `Recommendations`, `Dashboard`, `Documents`, `Interview`.
- Route availability:
  - Public: `Scholarships`
  - Auth-required: `Recommendations`, `Dashboard`, `Documents`, `Interview`
- Secondary pathways:
  - Profile management via dashboard and onboarding/profile pages.
  - Admin curation accessible to admin role users.

## End-To-End User Journey Plan
1. User lands on `/` and sees trust model plus bounded scope.
2. User explores `/scholarships` and opens detail pages to inspect validated facts.
3. User signs up and completes `/onboarding` profile.
4. User enters `/dashboard` for status and next actions.
5. User visits `/recommendations` for explainable ranked opportunities.
6. User uses `/document-feedback` and `/interview` for preparation.
7. User iterates between profile updates, recommendations, and preparation tools.

## Page-Level Integration Blueprint
## 1) Landing Page (`/`)
### Visual intent
- Editorial + product tone, restrained premium look, light-theme first.
- Three visible trust anchors:
  - Scope clarity (Canada-first, MS DS/AI/Analytics).
  - Source-of-truth clarity (validated facts lead).
  - Workflow clarity (discovery to preparation path).

### Required sections
1. Hero with value proposition + dual CTA.
2. Trust rail cards (catalog, trust model, scope).
3. How-it-works flow (3-step summary).
4. Data-vs-guidance split panel.

### Feature placement rules
- Do not expose deep feature controls here.
- Keep this page conversion + confidence focused.

## 2) Scholarship Browse (`/scholarships`)
### Visual intent
- High information density but calm layout.
- Persistent, non-modal filtering.

### Required layout
- Left/inline filter controls (scope-safe filters).
- Main results list with cards showing:
  - Title
  - Provider
  - Deadline
  - Country/scope markers
  - Published/validated context indicators
- Actions: open detail, save (if authenticated).

### Feature placement rules
- Highlight that only published records are user-facing.
- Keep search language grounded in curated corpus boundaries.

## 3) Scholarship Detail (`/scholarships/[scholarshipId]`)
### Visual intent
- Facts-first document-style page.

### Required content blocks
1. Scholarship overview.
2. Requirements and eligibility constraints.
3. Deadlines and funding details.
4. Provenance and source links.
5. Action panel (save, go to recommendations/preparation when authenticated).

### Feature placement rules
- Provenance should remain visible near policy-critical fields.
- Generated guidance should never replace facts on this page.

## 4) Auth Entry (`/login`, `/signup`)
### UX intent
- Fast entry with minimal friction.
- Clear handoff into onboarding/dashboard.

### Placement rules
- Keep forms narrow and direct.
- Keep marketing tone minimal; focus on account action.

## 5) Onboarding + Profile (`/onboarding`, `/profile`)
### UX intent
- Collect recommendation inputs quickly and clearly.

### Required sections
1. Academic target (degree, field, country).
2. Eligibility-related profile fields (citizenship, GPA, language if applicable).
3. Experience indicators used for ranking signals.

### Placement rules
- Show why each section matters for recommendations.
- Keep update path always available from dashboard.

## 6) Dashboard (`/dashboard`)
### UX intent
- Operational home for returning users.

### Required modules
1. Status metrics (saved count, profile readiness, preparation readiness).
2. Profile summary card with quick edit action.
3. Saved opportunities list.
4. Published opportunities preview.
5. Next-step action links to recommendations/documents/interview.

### Placement rules
- Dashboard is not a replacement for recommendations; it is a coordinator.
- Keep one-click transitions to primary task pages.

## 7) Recommendations Workspace (`/recommendations`)
### UX intent
- Prioritization and decision support through explainable ranking.

### Required layout
1. Ranked shortlist cards.
2. Per-card explanation sections:
   - Fit summary
   - Top factors
   - Hard-constraint status
   - Caution notes
   - Provenance hints
3. Save/unsave actions.
4. Optional deep explanation panel (progressive disclosure).

### Placement rules
- Use `Estimated Scholarship Fit Score` framing.
- Never present ranking as deterministic acceptance prediction.

## 8) Document Assistance (`/document-feedback`)
### UX intent
- Focused drafting and feedback loop.

### Required layout
1. Submission panel (text/file, type, optional scholarship grounding).
2. Draft/history list.
3. Feedback panel with strict separation:
   - Validated scholarship facts
   - Retrieved writing guidance
   - Generated guidance
   - Limitations
4. Citation block and refresh action.

### Placement rules
- Grounding context must be explicit when scholarship IDs are supplied.
- Limitation notices must remain visible to avoid over-trust.

## 9) Interview Practice (`/interview`)
### UX intent
- Structured practice loop, not open-ended chat.

### Required layout
1. Session start/resume block with practice mode.
2. Optional scholarship grounding input.
3. Current question and response area (text/audio).
4. Rubric feedback sections and progression state.
5. Session summary/history trend block.

### Placement rules
- Keep rubric dimensions explicit.
- Keep mode label visible (`general` vs `scholarship`).

## 10) Curation Dashboard (`/curation`)
### UX intent
- Admin-only operational review space.

### Required modules
1. Queue by provenance state (`raw`, `validated`, `published`).
2. Source/provenance inspection.
3. Review actions: validate, reject, publish, unpublish.
4. Manual raw import and ingestion-run context.

### Placement rules
- Admin workflows should remain visually distinct from student workspace.
- Publication controls require explicit state confirmation.

## Cross-Cutting UI Rules
## Fact-vs-guidance separation (mandatory)
Every feature must visually separate:
1. Validated scholarship facts
2. User-provided profile/document data
3. Generated recommendations/guidance
4. System caution or limitations

## Status language standards
- Prefer calm, precise state labels:
  - `Published`, `Validated`, `Needs review`, `In progress`, `Completed`
- Avoid dramatic binary pass/fail language.

## Accessibility baseline
1. Keyboard-accessible filters, forms, and nav.
2. Contrast-safe palette on all dense data surfaces.
3. Icons never as sole meaning carrier.
4. Motion only for structure and attention, never as blocking ornament.

## Responsive behavior priorities
1. Desktop-first density for discovery, recommendation, and admin tables.
2. Mobile-safe stack order for primary actions:
   - Read facts
   - Save/act
   - Inspect details
3. Keep CTA and critical statuses above fold where practical.

## Frontend Delivery Plan (Implementation Sequence)
1. **Navigation and IA hardening**
   - Ensure public/app/admin route discoverability aligns with current route map.
2. **Landing and trust framing polish**
   - Keep messaging consistent with PRD/governance scope.
3. **Discovery and detail consistency**
   - Standardize card/detail metadata hierarchy and provenance placement.
4. **Workspace coherence**
   - Tighten dashboard-to-recommendation-to-preparation transitions.
5. **Preparation trust UX**
   - Enforce explicit sections for facts/retrieval/generation/limitations.
6. **Admin curation clarity**
   - Keep provenance lifecycle and publish controls legible and safe.

## Acceptance Checklist For Frontend Integration
- [ ] A new visitor can understand scope and trust model on landing in < 20 seconds.
- [ ] Scholarship browse and detail surfaces clearly present published facts and provenance.
- [ ] Authenticated users can move from profile to recommendations to preparation without dead ends.
- [ ] Recommendation explanations show factors and caveats without overclaiming certainty.
- [ ] Document and interview pages expose bounded guidance with clear limitations.
- [ ] Admin curation surfaces provenance states and publication actions clearly.
- [ ] Navigation labels and page tone remain consistent across all pages.

## MVP decision
Frontend integration for MVP will prioritize one coherent journey from discovery to preparation, with strict fact-versus-guidance separation and route-level clarity across public, student, and admin surfaces.

## Deferred items
- Dark mode and advanced theming variants.
- Non-MVP geographies and broader degree-level UX pathways.
- Marketplace, partner, or institution-facing frontend surfaces.
- Advanced visualization-heavy explanation interfaces beyond current structured panels.

## Assumptions
- Current frontend routes remain the active implementation surface for Phase 1.
- The MVP remains Canada-first and MS-focused without broadening discovery scope.
- The existing design system direction (restrained premium light theme) is preserved while integrating remaining feature depth.

## Risks
- Expanding discovery UX too broadly can violate scope discipline and trust promises.
- If fact/guidance separation weakens, users may misread generated output as policy truth.
- Inconsistent labels across pages can make the workflow feel fragmented even when features exist.
