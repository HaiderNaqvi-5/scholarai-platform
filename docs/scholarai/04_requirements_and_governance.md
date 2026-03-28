# ScholarAI Requirements And Governance

## Purpose
Define baseline requirements, governance rules, and operational boundaries that keep ScholarAI implementable, trustworthy, and aligned with the **v0.1 SLC** direction.

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
| FR-01 | Store scholarships, requirements, deadlines, funding information, and provenance states in structured records. | v0.1 SLC |
| FR-02 | Support search and filtering across the defined v0.1 corpus. | v0.1 SLC |
| FR-03 | Enforce hard eligibility logic before ranking outputs. | v0.1 SLC |
| FR-04 | Provide recommendation outputs with explanation-oriented rationale. | v0.1 SLC |
| FR-05 | Support document-feedback workflows for SOPs, essays, and related materials. | v0.1 SLC |
| FR-06 | Support interview-practice workflows with structured feedback. | v0.1 SLC |
| FR-07 | Support admin curation and publication workflows for scholarship data. | v0.1 SLC |
| FR-08 | Track provenance through `raw`, `validated`, and `published` states. | v0.1 SLC |
| FR-09 | Support save/tracker visibility for readiness gaps, deadlines, and next actions. | v0.1 SLC |

## Non-Functional Requirements
| ID | Requirement | Priority |
|---|---|---|
| NFR-01 | Keep the system understandable and maintainable by a 3-person team. | v0.1 SLC |
| NFR-02 | Avoid distributed microservice complexity in active architecture. | v0.1 SLC |
| NFR-03 | Keep policy-critical information sourced from structured validated data. | v0.1 SLC |
| NFR-04 | Frame AI outputs as advisory guidance, not authoritative decisions. | v0.1 SLC |
| NFR-05 | Maintain boundaries between user data, validated facts, and generated outputs. | v0.1 SLC |
| NFR-06 | Keep documentation as source of truth while scope evolves by stage. | v0.1 SLC |
| NFR-07 | Require visual evidence for completion of UI-affecting changes. | v0.1 SLC |

## Data Governance
### Source-of-truth rule
Structured validated data is authoritative for eligibility, deadlines, funding rules, and official scholarship requirements.

### Provenance rule
Every scholarship record moves through:
1. `raw`
2. `validated`
3. `published`

### Validation rule
Generated responses may not override validated scholarship facts.

## AI Governance
### Allowed AI assistance
- Explainable fit guidance.
- Bounded document and interview feedback.
- Preparation strategy and next-step suggestions.

### Disallowed claims
- Deterministic scholarship acceptance claims.
- Policy truth derived from generated text.
- Unsupported accuracy claims or invented coverage.

### Model framing rule
Without real outcome labels, all recommendation and scoring outputs are estimates and guidance signals only.

## Scope Governance
### v0.1 SLC
- Canada-first scholarship corpus.
- MS Data Science, MS Artificial Intelligence, MS Analytics.
- USA only for narrowly scoped Fulbright-related context.

### Future Research Extensions
- Graph-layer comparative experiments.
- Stronger outcome-label and evaluation frameworks.

### Deferred By Stage
- v0.2 depth expansions.
- v0.3 platform and mentor workflow expansion.
- v1.x ecosystem and institution-facing scale.

## Change-Control Rules
1. Features that increase operational complexity must justify modular-monolith boundaries.
2. New data sources must define validation and provenance handling.
3. New AI workflows must specify whether they affect validated facts or advisory guidance only.
4. Expansion beyond v0.1 scope must be explicitly staged.
5. Terminology updates must remain consistent across canonical docs and readmes.

## Architecture Governance
| Topic | Rule |
|---|---|
| Knowledge Graph Layer | Mandatory logical concept; v0.1 default remains relationally derived graph abstraction |
| Search architecture | PostgreSQL + pgvector baseline; extra systems need explicit justification |
| Background jobs | Celery + Redis where async processing is necessary |
| Experiment tracking | Lightweight tracking preferred; heavier tooling must be justified |

## Documentation Governance
1. Canonical active docs live under `docs/scholarai/`.
2. Legacy docs outside canonical set are reference inputs, not authority.
3. Canonical docs end with `SLC decision (v0.1)`, `Deferred By Stage`, `Assumptions`, and `Risks`.
4. Placeholder sections are not permitted.

## Review Gates
| Gate | Check |
|---|---|
| Scope gate | No staged-deferred features leaked into v0.1 |
| Data gate | Source-of-truth fields remain validated-data grounded |
| AI gate | Generated outputs are clearly advisory |
| Architecture gate | Design remains feasible for a 3-person team |
| Documentation gate | Terminology and section naming remain consistent |
| UI quality gate | Browser or screenshot evidence exists for UI completion |

## Authorization Governance (RBAC Expansion)
### Authorization model rule
ScholarAI uses a capability-based authorization matrix. Roles are assignment bundles; access decisions evaluate explicit capabilities.

### Canonical role set
1. `ENDUSER_STUDENT`
2. `INTERNAL_USER`
3. `DEV`
4. `ADMIN`
5. `UNIVERSITY`
6. `OWNER`
7. `MENTOR` (staged and policy-gated)
8. `TEST_USER` (internal QA simulation role)

### Capability governance rules
1. Deny by default for endpoints/actions without explicit capability mapping.
2. No implicit cross-role inheritance in runtime checks.
3. High-risk capability assignments require secondary reviewer approval.
4. Privileged operations must emit audit events with actor and request tracing metadata.

### Institution scope rule for university access
`UNIVERSITY` access must enforce explicit `institution_id` scope at service and query layers.

### Owner and support visibility rule
Owner/admin visibility is operational and security-oriented. It must not become unrestricted personal-data surveillance.

### Migration governance rule
Role-only claims transition through compatibility window:
1. accept legacy role claims
2. issue capability claims in parallel
3. compare runtime decisions for mismatch telemetry
4. remove legacy fallback after sustained stability

### RBAC-specific review gates
| Gate | Check |
|---|---|
| Capability gate | Protected endpoints reference explicit capabilities |
| Scope isolation gate | Institution-scoped access is enforced for university actors |
| Compatibility gate | Legacy/new auth mismatches are measured and bounded |
| Audit gate | Privileged operations are fully traceable |
| Deprecation gate | Legacy role-only path has dated removal milestone |

## SLC decision (v0.1)
ScholarAI governance prioritizes constrained scope, structured data authority, advisory AI framing, and evidence-backed quality over feature sprawl.

## Deferred By Stage
- Governance for institution-commercial workflows at scale.
- Expanded cross-jurisdiction legal and policy handling.
- Advanced experimentation governance dependent on outcome-label maturity.

## Assumptions
- Documentation updates are treated as product and architecture updates.
- Admin curation remains available to enforce provenance discipline.
- Evidence requirements are enforced in review, not only documented.

## Risks
- Governance can drift if review gates are not actively applied.
- Scope creep can reintroduce pre-SLC instability.
- Weak provenance discipline can undermine trust and explainability claims.
