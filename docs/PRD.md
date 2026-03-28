# ScholarAI Product Requirements Document

> Status: Canonical SLC PRD
> Version: v0.1 SLC
> Date: 2026-03-27
> Positioning: ScholarAI helps students discover verified scholarships, understand fit, prepare stronger applications, and track progress in one premium, trustworthy workflow.

## Executive Position
ScholarAI is no longer framed as a broad product experiment. The product is explicitly positioned as a v0.1 SLC release: simple, lovable, and complete for the core student journey.

The product must feel calm, coherent, and credible in real usage, not like a stitched demo. AI remains advisory. Validated scholarship facts remain authoritative.

## Product North Star
ScholarAI should help a student move from confusion to confident action by answering four questions in the first ten minutes:
1. What fits me?
2. Why does it fit?
3. What is missing?
4. What should I do next?

## Versioning Model
| Stage | Goal | User perception | Representative capabilities |
|---|---|---|---|
| v0.1 SLC | Complete core loop | Coherent and trustworthy | Browse, fit guidance, save, prepare, track |
| v0.2 Depth | Stronger guidance quality | Smarter and more useful | Deeper recommendation and preparation feedback |
| v0.3 Platform | Operational expansion | More scalable | Mentor workflows, stronger operations surfaces |
| v1.x Ecosystem | Commercial and partner scale | Category-level platform | Provider and institution integrations, paid tiers |

## v0.1 SLC Boundaries
### In Scope
- Verified scholarship discovery and detail pages with source provenance.
- Profile-aware, explainable fit guidance with action-oriented summaries.
- Save and tracking workflows with readiness and deadline context.
- Bounded document guidance (SOP, CV, essays).
- Text-first interview practice with rubric-style feedback.
- Role-aware operations surfaces for student, admin, and owner.

### Deferred By Stage
- Compare mode and deeper planning automation (v0.2).
- Voice interview, richer mentor workflows, broader recommendation depth (v0.2-v0.3).
- Institution-facing verification and full partner workflows (v0.3-v1.x).
- Blockchain trust-layer and direct provider submission network (v1.x).

## Roles and Access Contract
| Role | Product responsibility | Core access |
|---|---|---|
| Student | Primary external user | Profile, recommendations, tracker, documents, interview |
| Mentor | Guided support role | Controlled student-assist and review workflows (gated) |
| Admin / Manager | Operations and curation | Ingestion review, support queues, moderation, data lifecycle |
| Owner | Governance and reliability | Full operational visibility, role control, audit views, system health |
| Test-User (Internal QA) | Validation and simulation | Student-like flows with explicit test-account markers |

Authorization remains capability-based, deny-by-default, and institution-scoped where applicable.

## Explainable AI Contract
- Fit outputs are guidance bands (for example: Strong, Possible, Stretch), not deterministic acceptance claims.
- Every AI output must separate validated facts, inferred signals, generated guidance, and limitations.
- Generated text must not override structured validated scholarship policy fields.

## Data and Curation Contract
- Every published scholarship record must include source URL, provider identity, last-checked timestamp, and provenance state.
- Provenance lifecycle remains `raw -> validated -> published`.
- Ambiguous or stale records must be flagged, archived, or withheld from primary user surfaces.

## UX and Delivery Quality Rules
- Visible quality is mandatory: passing lint and tests is insufficient for UI completion.
- UI changes require rendered evidence across desktop and mobile breakpoints.
- Primary student journey must remain obvious and low-friction.
- Verified facts and advisory guidance must be visually distinct.

## Frontend and Backend Boundaries
| Layer | Owns | Does not own |
|---|---|---|
| Frontend | Rendering, interaction state, role-aware navigation | Policy truth, ranking truth, ingestion heuristics |
| Backend API | Auth, role resolution, eligibility logic, recommendation contracts, audit events | Presentation-level styling decisions |
| Async workers | Ingestion, long-running processing, recalculation jobs | Browser UX behavior |
| Database | Authoritative records, provenance, permissions, audit logs | Presentation-only denormalization without purpose |

## Monetization Direction
| Tier | Core value |
|---|---|
| Free | Verified browse, save, baseline fit, foundational preparation |
| Pro Student | Deeper readiness and preparation workflows |
| Mentor | Controlled collaboration and review tooling (staged) |
| Institution / Partner | Deferred platform-facing workflows |

Monetization must not distort ranking trust. Sponsored visibility, if introduced later, must be explicit and isolated from fit logic.

## Acceptance Criteria (v0.1 SLC)
- A new user can sign up, onboard, browse, inspect, save, and act without confusion.
- Primary screens feel premium and consistent on desktop and mobile.
- Recommendation outputs are understandable without opening advanced internals.
- Document and interview workflows are useful, bounded, and transparent.
- Admin and owner surfaces support operations without privacy overreach.
- End-to-end demo can be run without caveats.

## SLC decision (v0.1)
ScholarAI v0.1 will ship as a premium, trustworthy student operating system with constrained scope and complete core workflow execution, not as an experimental breadth-first product.

## Deferred By Stage
- v0.2: Recommendation depth, compare mode, stronger preparation workflows.
- v0.3: Mentor and operations expansion, institution workflow scaffolding.
- v1.x: Ecosystem integrations, partner products, advanced trust infrastructure.

## Assumptions
- Constrained scope with strong execution increases user trust and adoption.
- Structured curation quality is a durable moat.
- Advisory AI framing is a product trust advantage, not a limitation.

## Risks
- Legacy docs and language can reintroduce pre-SLC mixed messaging.
- Scope creep can erode polish and trust if staged boundaries are not enforced.
- Weak evidence discipline can mask UI quality regressions.
