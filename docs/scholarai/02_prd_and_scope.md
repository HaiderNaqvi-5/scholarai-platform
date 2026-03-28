# ScholarAI PRD And Scope

## Product Goal
Build a focused scholarship operating system that helps students move from "I do not know where to start" to "I know what fits, why it fits, what is missing, and what to do next" within a constrained **v0.1 SLC** scope.

## Primary Users
| User | Need | Why ScholarAI matters |
|---|---|---|
| Student applicant | Find relevant scholarships and act confidently | Replaces fragmented manual research with guided execution |
| Admin curator | Validate and publish scholarship data | Preserves trust in policy-critical fields |
| Test-user (internal QA) | Validate flows in production-like scenarios | Protects release confidence without using real user identities |
| Product and research team | Evaluate explainability and workflow quality | Supports defensible product and research progress |

## User Jobs To Be Done
1. Discover relevant scholarships quickly.
2. Understand hard eligibility constraints early.
3. Prioritize opportunities with transparent reasoning.
4. Improve documents with bounded, context-aware feedback.
5. Practice interview responses with actionable coaching.

## Product Principles
1. SLC discipline beats feature breadth.
2. Structured validated data beats generic AI confidence.
3. Explainable guidance beats opaque scoring.
4. Advisory AI beats overstated automation.
5. One coherent journey beats disconnected tools.

## v0.1 SLC Scope
### In scope
| Capability | Description |
|---|---|
| Curated scholarship discovery | Search and browse Canada-first scholarship corpus within defined academic scope |
| Eligibility-aware filtering | Enforce hard constraints from structured validated rules and graph-derived logic |
| Explainable fit guidance | Present transparent fit rationale with next-step guidance |
| Scholarship detail pages | Show requirements, deadlines, funding, provenance, and source links |
| Save and tracker workflows | Preserve opportunities and track readiness and deadlines |
| Document preparation support | Bounded SOP/CV/essay feedback workflows |
| Interview practice | Scholarship-style prompts with structured feedback |
| Admin curation workflow | Validate and publish scholarship records through provenance states |

### Deferred By Stage
| Item | Target stage | Reason |
|---|---|---|
| Compare mode and richer timeline planning | v0.2 | Secondary to core loop completeness |
| Voice-first interview practice | v0.2-v0.3 | Increases implementation and QA complexity |
| Mentor collaboration workflows | v0.3 | Adds privacy and workflow complexity |
| Institution-facing verification and dashboards | v0.3-v1.x | Requires partner operating model and governance |
| Broad geography and degree expansion | v1.x | Must not dilute data quality in v0.1 |
| Deterministic acceptance-style claims | never in v0.1 | Unsupported without real outcome labels |

## Scope Boundaries
### Geography
- Canada is the primary v0.1 scope.
- USA is limited to narrowly scoped Fulbright-related cases.
- Broad USA scraping remains deferred.

### Academic scope
- Degree level: MS.
- Program targets: Data Science, Artificial Intelligence, Analytics.
- General undergraduate and PhD discovery are deferred.

### Data scope
- Official requirements, deadlines, and funding rules come from structured validated records.
- Generated output is advisory and must not override validated facts.

## Core User Flows
1. Student signs in and completes profile/onboarding.
2. Student explores scholarships and applies filters.
3. System enforces hard eligibility before fit guidance.
4. Student reviews details and saves priority opportunities.
5. Student uses preparation tools and tracker next actions.

## Functional Requirements
| ID | Requirement |
|---|---|
| PRD-01 | Store scholarship records with provenance state and source references. |
| PRD-02 | Support search and filtering over the v0.1 SLC corpus. |
| PRD-03 | Evaluate hard eligibility constraints before fit guidance ranking. |
| PRD-04 | Provide explanation-oriented fit output with actionable next steps. |
| PRD-05 | Support bounded document-feedback workflows. |
| PRD-06 | Support interview-practice workflows with structured feedback. |
| PRD-07 | Provide admin workflows for validation and publication of scholarship data. |
| PRD-08 | Support saved scholarships and readiness-oriented tracking workflow. |

## Non-Functional Scope Constraints
| Area | Constraint |
|---|---|
| Team feasibility | Deliverable by 3 developers in 16 weeks |
| Architecture | Modular monolith |
| Operations | Avoid heavy distributed-service sprawl |
| Transparency | Avoid deterministic acceptance claims |
| Trust | Prefer narrower validated coverage over broad noisy coverage |
| Quality evidence | UI completion requires visual verification artifacts |

## Release Framing
### v0.1 SLC
Constrained corpus, clear eligibility rules, explainable guidance, save/tracker workflows, and bounded preparation tools with premium UX expectations.

### Future Research Extensions
Graph-layer comparisons, trust/evaluation studies, and improved outcome-label research methods.

### Deferred By Stage
v0.2 depth improvements, v0.3 platform expansion, and v1.x ecosystem/commercial scale.

## Acceptance Conditions For v0.1 SLC
1. Users can browse, inspect, save, and track scholarships without confusion.
2. Eligibility-relevant rules are represented in structured validated data.
3. Fit guidance is explainable and framed as advisory estimates.
4. Document and interview tools are bounded and transparent.
5. Admin curation supports `raw`, `validated`, and `published` provenance states.
6. Primary screens demonstrate consistent quality across desktop and mobile.

## SLC decision (v0.1)
ScholarAI v0.1 will focus on a narrow, high-quality scholarship workflow for Canada-first MS programs with explainable fit guidance, save/tracker execution, and bounded preparation support.

## Deferred By Stage
- v0.2 depth features (compare mode, richer planning, deeper preparation).
- v0.3 mentor and operations expansion.
- v1.x broader geography, institutional surfaces, and ecosystem integrations.

## Assumptions
- A constrained corpus is more valuable in v0.1 than large low-confidence coverage.
- Students benefit from clear rationale and next actions over opaque scores.
- Evidence-driven QA can hold premium UX quality in a small-team delivery model.

## Risks
- Users may still expect broader coverage unless scope is communicated clearly.
- Advisory outputs may be over-trusted if boundaries are weak in UI copy.
- Scope creep can degrade product coherence before v0.1 maturity.
