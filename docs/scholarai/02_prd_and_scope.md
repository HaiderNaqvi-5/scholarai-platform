# ScholarAI PRD And Scope

## Product Goal
Build a focused scholarship platform that helps students move from "I do not know where to start" to "I know which scholarships fit, why they fit, and how to prepare stronger applications" within a tightly constrained v0.1.

## Primary Users
| User | Need | Why ScholarAI matters |
|---|---|---|
| Student applicant | Find relevant scholarships and understand fit | Replaces fragmented manual research with a guided workflow |
| Admin curator | Validate and publish structured scholarship data | Maintains source-of-truth quality for policy-critical fields |
| Research team | Evaluate explainable ranking and guided preparation workflows | Supports defensible FYP research framing |

## User Jobs To Be Done
1. Discover scholarships relevant to a defined academic target.
2. Understand basic eligibility constraints before investing time.
3. Prioritize scholarships using transparent reasoning.
4. Improve documents with grounded feedback.
5. Practice interview responses using scholarship-oriented prompts.

## Product Principles
1. Scope discipline beats feature breadth.
2. Structured validated data beats generic AI confidence.
3. Explainable ranking beats opaque scoring.
4. Advisory assistance beats overstated automation.
5. One coherent workflow beats disconnected tools.

## v0.1 Scope
### In scope
| Capability | Description |
|---|---|
| Curated scholarship discovery | Search and browse a Canada-first scholarship corpus tied to the defined v0.1 program scope |
| Eligibility-aware filtering | Enforce hard constraints using structured validated rules and Knowledge Graph Layer logic |
| Ranked recommendations | Present Estimated Scholarship Fit Score with explanation-oriented rationale |
| Scholarship detail pages | Show requirements, deadlines, funding information, provenance, and source links |
| Application strategy guidance | Provide workflow guidance on next steps, priorities, and preparation focus areas |
| Document feedback | Provide SOP, essay, and document-quality feedback through bounded RAG workflows |
| Interview practice | Simulate scholarship-style interview prompts and structured feedback |
| Admin curation workflow | Review, validate, and publish scholarship records through provenance states |

### Out of scope for v0.1
| Item | Reason |
|---|---|
| Broad USA university discovery | Conflicts with Canada-first scope control |
| DAAD ingestion | Explicitly deferred by repository rules |
| Mentor marketplace | Adds workflow and privacy complexity without being core to v0.1 validation |
| Automated application submission | High risk, low priority, and operationally complex |
| Claims of scholarship acceptance prediction | Unsupported without real outcome labels |
| Policy truth from generated outputs | Violates source-of-truth governance |

## Scope Boundaries
### Geography
- Canada is the primary v0.1 university and scholarship corpus.
- USA is allowed only for Fulbright-related information and narrow cross-border logic.
- Broad USA scraping is excluded from v0.1.

### Academic scope
- Degree level: MS.
- Program targets: Data Science, Artificial Intelligence, Analytics.
- General undergraduate and PhD discovery are excluded from v0.1.

### Data scope
- Official scholarship requirements, deadlines, and funding rules must come from structured validated records.
- Free-form model output is advisory only.

## Core User Flows
1. Student creates or updates a profile.
2. Student explores scholarships through search and filters.
3. System applies hard eligibility logic before ranking.
4. Student reviews scholarship details and explanations.
5. Student uses strategy, document, and interview tools to prepare.

## Functional Requirements
| ID | Requirement |
|---|---|
| PRD-01 | The system must store scholarship records with provenance state and source reference. |
| PRD-02 | The system must support search and filtering over the v0.1 scholarship corpus. |
| PRD-03 | The system must evaluate hard eligibility constraints before recommendation ranking. |
| PRD-04 | The system must provide explanation-oriented ranking output for recommendations. |
| PRD-05 | The system must support document-feedback workflows bounded to guidance use cases. |
| PRD-06 | The system must support interview-practice workflows with structured feedback. |
| PRD-07 | The system must provide admin workflows for validation and publication of scholarship data. |

## Non-Functional Scope Constraints
| Area | Constraint |
|---|---|
| Team feasibility | Must remain deliverable by 3 developers in 16 weeks |
| Architecture | Must remain a modular monolith |
| Operations | Must avoid heavy infrastructure and multi-service sprawl |
| Transparency | Must avoid black-box scholarship acceptance claims |
| Reliability | Must prefer narrower validated coverage over broad noisy coverage |

## Release Framing
### v0.1
- Constrained corpus, clear eligibility rules, explainable ranking, advisory preparation tools.

### Future Research Extensions
- DAAD and additional provider logic.
- Deeper evaluation of Knowledge Graph Layer alternatives.
- Expanded dataset collection and stronger experimental design.

### Deferred By Stage Startup Features
- Wider geography and degree coverage.
- Collaboration workflows and commercial service layers.
- Institution-facing analytics and ecosystem tooling.

## Acceptance Conditions For v0.1
1. Users can browse and inspect a curated scholarship corpus within the defined scope.
2. Eligibility-relevant rules are represented in structured validated data.
3. Recommendations are explainable and framed as estimates, not deterministic outcomes.
4. Writing and interview tools are clearly bounded as advisory aids.
5. Admin curation supports `raw`, `validated`, and `published` provenance states.

## v0.1 decision
ScholarAI v0.1 will focus on a narrow, high-quality scholarship workflow for Canada-first MS programs, with explainable ranking and bounded AI preparation tools as the core product surface.

## Deferred items
- DAAD and other non-v0.1 provider expansion.
- Mentor workflows and paid services.
- Broad geography, degree, and institutional expansion.
- Any feature that depends on real scholarship outcome labels before those labels exist.

## Assumptions
- A constrained corpus is more valuable for v0.1 than a large but weakly validated directory.
- Students prefer transparent prioritization support over fully manual scholarship research.
- Admin curation capacity is sufficient to maintain a smaller validated dataset.

## Risks
- Users may expect broader coverage than the v0.1 intentionally supports.
- Document and interview guidance may be over-trusted if disclaimers are weak.
- Recommendation usefulness depends on disciplined data validation and profile quality.


## SLC decision (v0.1)
TBD (baseline governance alignment).
