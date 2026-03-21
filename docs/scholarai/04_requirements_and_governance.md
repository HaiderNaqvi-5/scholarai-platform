# ScholarAI Requirements And Governance

## Purpose
This document defines the baseline requirements, governance rules, and decision boundaries that keep ScholarAI implementable, defensible, and internally consistent.

## Governing Constraints
| Area | Constraint |
|---|---|
| Team | 3 developers |
| Timeline | 16 weeks |
| Budget | Limited |
| Architecture | Modular monolith |
| Frontend | Next.js + React + TypeScript + TailwindCSS |
| Backend | FastAPI |
| Async jobs | Celery + Redis |
| Primary database | PostgreSQL |
| Vector search | pgvector |
| Ingestion | Playwright + Pandas + Pydantic |
| Migration tooling | Alembic |
| Deployment baseline | Docker Compose |
| CI/CD baseline | GitHub Actions |

## Functional Requirements
| ID | Requirement | Priority |
|---|---|---|
| FR-01 | The platform must store scholarships, requirements, deadlines, funding information, and provenance states in structured records. | MVP |
| FR-02 | The platform must support search and filtering across the defined MVP corpus. | MVP |
| FR-03 | The platform must enforce hard eligibility logic before ranking results. | MVP |
| FR-04 | The platform must provide recommendation outputs with explanation-oriented rationale. | MVP |
| FR-05 | The platform must support document-feedback workflows for SOPs, essays, and related application materials. | MVP |
| FR-06 | The platform must support interview-practice workflows with structured feedback. | MVP |
| FR-07 | The platform must support admin curation and publication workflows for scholarship data. | MVP |
| FR-08 | The platform must track provenance through `raw`, `validated`, and `published` states. | MVP |

## Non-Functional Requirements
| ID | Requirement | Priority |
|---|---|---|
| NFR-01 | The system must remain understandable and maintainable by a 3-person team. | MVP |
| NFR-02 | The active architecture must avoid distributed microservice complexity. | MVP |
| NFR-03 | Policy-critical information must come from structured validated data, not generated text. | MVP |
| NFR-04 | AI outputs must be framed as guidance or estimation, not authoritative decisions. | MVP |
| NFR-05 | The system must keep clear boundaries between user data, validated facts, and generated outputs. | MVP |
| NFR-06 | Documentation must remain the source of truth while product scope is still evolving. | MVP |

## Data Governance
### Source-of-truth rule
Structured validated data is authoritative for:
- eligibility
- deadlines
- funding rules
- official scholarship requirements

### Provenance rule
Every scholarship record should move through:
1. `raw`
2. `validated`
3. `published`

### Validation rule
No generated response may override validated scholarship facts. If generated guidance conflicts with validated data, validated data wins and the generated output should be corrected or suppressed.

## AI Governance
### Allowed AI assistance
- Estimated Scholarship Fit Score generation.
- Application Competitiveness Score framing.
- SOP and essay feedback.
- Interview-answer feedback.
- Document quality suggestions.

### Disallowed claims
- Scholarship acceptance prediction framed as fact.
- Policy truth derived from generated text.
- Unsupported accuracy claims, fake metrics, or invented dataset coverage.

### Model framing rule
If real scholarship outcome labels are absent, all ranking and scoring outputs must be described as estimates based on available features and assumptions.

## Scope Governance
### MVP
- Canada-first scholarship corpus.
- MS Data Science, MS Artificial Intelligence, MS Analytics.
- USA only for Fulbright-related information and narrow cross-border logic.

### Future Research Extensions
- DAAD.
- Stronger comparative graph-layer experiments.
- Broader outcome-data collection and evaluation design.

### Post-MVP Startup Features
- Broader geography and academic coverage.
- Marketplace and institutional monetization features.
- Operational analytics products and ecosystem integrations.

## Change-Control Rules
1. Any feature that adds operational complexity must justify why the modular monolith is no longer sufficient.
2. Any new data source must state validation strategy and provenance handling.
3. Any new AI workflow must state whether it affects validated facts or only advisory guidance.
4. Any expansion beyond Canada-first scope must be marked as deferred unless explicitly approved.
5. Any change to core terminology must be reflected across `README.md`, `docs/scholarai/README.md`, and relevant canonical docs.

## Architecture Governance
| Topic | Rule |
|---|---|
| Knowledge Graph Layer | Mandatory logically; MVP default is a relationally derived graph abstraction unless Neo4j becomes clearly justified |
| Search architecture | PostgreSQL + pgvector is the MVP baseline; additional search systems require explicit justification |
| Background jobs | Celery + Redis only where async work is necessary |
| Experiment tracking | Prefer lightweight tracking; MLflow must be justified by actual workflow needs |

## Documentation Governance
1. Canonical active documentation lives under `docs/scholarai/`.
2. Legacy docs outside `docs/scholarai/` are migration inputs, not long-term authorities.
3. Every documentation file must end with `MVP decision`, `Deferred items`, `Assumptions`, and `Risks`.
4. No section should remain as placeholder text.

## Review Gates
| Gate | Check |
|---|---|
| Scope gate | No deferred startup features have leaked into MVP |
| Data gate | Source-of-truth fields are grounded in validated records |
| AI gate | Generated outputs are clearly advisory |
| Architecture gate | The design remains feasible for 3 developers in 16 weeks |
| Documentation gate | Terminology and section naming remain consistent |

## Authorization Governance (RBAC Expansion)
### Authorization model rule
ScholarAI uses a capability-based authorization matrix. Roles are assignment bundles, but access decisions are evaluated through explicit capabilities.

### Canonical role set
1. `ENDUSER_STUDENT`
2. `INTERNAL_USER`
3. `DEV`
4. `ADMIN`
5. `UNIVERSITY`
6. `OWNER`

### Capability governance rules
1. Deny by default for any endpoint or action without an explicit capability mapping.
2. No implicit cross-role inheritance is assumed in runtime checks.
3. High-risk capabilities require at least one secondary reviewer for assignment changes.
4. Privileged operations must emit audit events with `actor_user_id`, `action_type`, and `request_id`.

### Institution scope rule for university access
`UNIVERSITY` access must be bound to explicit institution scope from first release of the contract.

Required controls:
- every university-bound query must enforce `institution_id` filtering
- cross-institution reads and writes must fail with authorization errors
- scope overrides are prohibited outside emergency break-glass flow

### Migration governance rule
Migration from legacy role-only claims to capability claims must use a compatibility window:
1. accept legacy role claims
2. issue capability claims in parallel
3. compare runtime decisions for mismatch telemetry
4. remove legacy fallback only after sustained stability

### RBAC-specific review gates
| Gate | Check |
|---|---|
| Capability gate | Every protected endpoint references explicit capabilities |
| Scope isolation gate | Institution-scoped access is enforced for university actors |
| Compatibility gate | Legacy/new auth decision mismatches are measured and bounded |
| Audit gate | Privileged operations are fully traceable |
| Deprecation gate | Legacy role-only path has a dated removal milestone |

## MVP decision
ScholarAI governance prioritizes constrained scope, structured data authority, advisory-only AI framing, and modular-monolith feasibility over breadth or architectural ambition.

## Deferred items
- Governance for commercial partnerships and paid workflows.
- Broader legal and institutional policy handling beyond MVP geography.
- Advanced experimentation governance tied to real outcome labels.

## Assumptions
- The team will treat documentation changes as architecture and product changes, not only editorial changes.
- Admin curation is available to maintain provenance discipline.
- MVP can rely on internal governance discipline before heavier compliance processes are needed.

## Risks
- Governance rules are easy to write and easy to ignore unless used in review.
- AI-related scope creep can happen quickly if advisory boundaries are not enforced.
- Weak provenance handling would undermine both product trust and research defensibility.
