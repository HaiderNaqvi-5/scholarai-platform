# ScholarAI Frontend UI Correction Plan (v0.1 SLC)

## Purpose
Define the canonical UI correction and delivery rules to align ScholarAI with the v0.1 SLC standard: premium-feeling, trustworthy, and execution-ready.

## UI Diagnosis
- The product has strong architecture but uneven user-perceived quality.
- Analytical density appears too early in several student-facing screens.
- Dashboard surfaces inform but do not consistently drive momentum.
- Visual hierarchy is inconsistent across key flows.

## Design North Star
ScholarAI UI should feel like Apple-level calm, Stripe-level operational clarity, and Vercel-level crisp execution.

Rules:
- One dominant action per screen.
- Fast perceived performance.
- Explicit visual separation between verified facts and AI guidance.
- Minimal chrome with strong typography and spacing discipline.
- Accessibility by default.

## Global Frontend Rules
| Area | Rule | Why |
|---|---|---|
| Typography | Restrained scale with strong heading contrast | Premium readability |
| Spacing | Favor whitespace over decorative separators | Calm clarity |
| Color | Use for state/trust, not decoration | Avoid visual noise |
| Cards | Reduce badge/button clutter | Better scanning |
| Motion | Subtle state confirmation and reveal | Polished interaction |
| Responsiveness | Design for mobile intentionally | Real-world readiness |

## Product Surface Map
| Surface | Role | Primary objective |
|---|---|---|
| Landing | Public | Trust, value, conversion |
| Explore | Student | Discover and filter scholarships |
| Saved / Tracker | Student | Monitor pipeline, readiness, deadlines |
| Recommendations | Student | Understand fit, gaps, and next actions |
| Documents | Student | Improve preparation assets |
| Interview | Student | Practice and receive actionable feedback |
| Profile | Student | Maintain recommendation inputs |
| Admin | Privileged | Curation and operational support |
| Owner | Privileged | Governance, telemetry, reliability |
| Mentor | Privileged beta | Guided student support |

## Role Home Screens
| Role | Default home | Must show first |
|---|---|---|
| Student | Student dashboard | Saved count, deadlines, readiness gaps, next actions |
| Admin/Manager | Operations dashboard | Ingestion health, curation queue, support tasks |
| Owner | Owner console | System health, role changes, operational alerts |
| Mentor | Mentor workspace | Assigned students, pending reviews, coaching queue |
| Test-User (Internal QA) | Student-like dashboard + QA badge | Test-environment markers and feedback controls |

## Screen-By-Screen Correction Plan
### Landing
- One premium hero, trust rail, and focused CTA cluster.
- Replace internal-sounding copy with outcome language.
- Show realistic product panels instead of placeholder visuals.

### Auth (Login/Signup)
- Keep forms short and visually centered.
- Place OAuth options (Google/Apple where enabled) without burying email/password.
- Preserve calm visual hierarchy.

### Onboarding
- Multi-step guided narrative with progress framing.
- Explain why each input matters.
- Avoid long-form data dump experience.

### Explore
- Improve card hierarchy: title, provider, deadline, fit hint, save action.
- Keep filter state visible but not noisy.
- Hide advanced filters behind clear disclosures on smaller screens.

### Scholarship Detail
- Lead with summary block: provider, deadline, funding, fit, and next actions.
- Group requirements and preparation context into clear modules.
- Keep official source trust signal highly visible.

### Recommendations
- Default output must answer: why fit, what is missing, what to verify, what next.
- Move model internals behind advanced disclosure.
- Avoid ML-report visual style in primary student experience.

### Dashboard
- Emphasize progress and urgency, not static widgets.
- Show one dominant next action above the fold.
- Highlight nearest deadlines and active prep tasks.

### Documents
- Separate input area, active draft, feedback summary, and revision guidance.
- Distinguish facts, guidance, and limitations visually.

### Interview
- Center on mode selection, prompt-response loop, and rubric summary.
- Keep feedback concise and actionable.

### Admin and Owner
- Use dense operational layouts intentionally.
- Do not mirror student UI without purpose.
- Prioritize queues, health metrics, and audit-friendly clarity.

## Frontend-Backend Contract Rules
- Every primary screen must have explicit API contract requirements.
- Frontend must not derive policy truth from client heuristics.
- Recommendation payloads should expose summary-first and advanced-detail sections separately.
- Role dashboards should consume server-driven capability flags.

## Agentic Workflow Rules For UI Delivery
- Visible quality beats green checks.
- UI completion requires browser proof or screenshot evidence.
- Each task must produce review artifacts (scope note, changed files, evidence, risks).
- Use specialist-agent separation for implementation vs QA vs review.

## Required MCP Tooling Baseline
- GitHub context access.
- Browser automation and screenshot validation.
- Project filesystem context.
- Design-source integration where available.

## Frontend Delivery Phases
| Phase | Priority | Deliverables |
|---|---|---|
| F1 | Critical | Landing, auth, onboarding rewrite |
| F2 | Critical | Explore, detail, recommendations simplification |
| F3 | Critical | Student dashboard and tracker quality uplift |
| F4 | High | Documents and interview polish |
| F5 | High | Admin/owner operations UX refinement |
| F6 | Medium | Mentor workspace pilot |

## Acceptance Criteria
- Priority screens pass desktop and mobile visual QA.
- Primary CTA is obvious within three seconds on each key surface.
- Student journey is navigationally clear end-to-end.
- Accessibility basics pass: labels, focus order, semantics, contrast, keyboard flow.
- Role home experiences are visibly differentiated.

## SLC decision (v0.1)
Frontend completion is defined by user-visible quality and trust clarity, not by code-only completion signals.

## Deferred By Stage
- v0.2: Compare mode and deeper planning interface surfaces.
- v0.3: Mentor and platform operational expansion screens.
- v1.x: Institution-grade ecosystem interfaces.

## Assumptions
- Product team will enforce screenshot/browser evidence as a merge gate.
- Tokenized design system changes will be adopted consistently.
- Role-based UX boundaries are owned jointly by product and engineering.

## Risks
- Mixed legacy styling can reintroduce inconsistency if token usage is not enforced.
- Scope creep can reduce polish velocity.
- Weak QA evidence can hide regressions behind passing CI.
