# ScholarAI Execution Plan

## Purpose
This document defines the 16-week delivery plan for ScholarAI. It translates the architecture and product scope into a realistic sequence of work for three developers, including testing, demos, documentation, and human review gates.

## Team Ownership Split
| Role | Primary ownership |
|---|---|
| Developer A: Backend and data systems | schema, curation flows, API, deployment foundations |
| Developer B: ML and AI workflows | recommendation pipeline, explanation layer, document assistance, evaluation tooling |
| Developer C: Frontend and product UX | search, detail, recommendation, document, interview, and admin UI |

## Exact Phase Structure
| Phase | Weeks | Goal |
|---|---|---|
| Phase 0 Foundation and planning | 1-2 | Lock docs, repo standards, schema direction, and review workflow |
| Phase 1 Core product and data layer | 3-6 | Build data foundation, curation flow, and core product reads |
| Phase 2 Recommendation and explainability features | 7-10 | Deliver ranking, explanation, document assistance, and interview baseline |
| Phase 3 Research evaluation and polish | 11-13 | Run evaluation pipelines, improve UX, and stabilize quality |
| Phase 4 Final hardening, thesis packaging, and future roadmap | 14-16 | Final QA, demos, documentation packaging, and fallback-safe delivery |

## Weekly Milestones
| Week | Milestone | Primary owner |
|---|---|---|
| 1 | Finalize canonical docs, glossary, schema direction, and source registry rules | All |
| 2 | Lock API surface draft, module boundaries, and curation-state workflow | A |
| 3 | Implement base schema and migration plan on paper, plus ingestion run model | A |
| 4 | Define curator workflow, source review process, and scholarship detail read model | A + C |
| 5 | Finalize search and filter requirements, program taxonomy, and publication rules | A + C |
| 6 | Deliver curation-ready data layer and published scholarship discovery baseline | A |
| 7 | Deliver stage 0 and stage 1 recommendation logic specification and tests | B |
| 8 | Deliver vector retrieval plan and explanation payload contract | B |
| 9 | Deliver document-assistance workflow and text-first interview baseline | B + C |
| 10 | Integrate recommendation, explanation, and preparation UI contracts | B + C |
| 11 | Build offline evaluation sets, ranking comparisons, and explanation study materials | B |
| 12 | Run pilot QA and UX polish on search, recommendation, and feedback surfaces | C |
| 13 | Freeze v0.1 SLC-scope features and complete research evaluation pass | All |
| 14 | Run full regression, deployment rehearsal, and documentation cleanup | A |
| 15 | Prepare thesis evidence, demo scripts, and fallback-safe release candidate | All |
| 16 | Final hardening, packaging, and roadmap handoff | All |

## RBAC Expansion Workstream (Docs-First)
This workstream starts immediately and must pass documentation gates before broad code implementation.

### Week-by-week RBAC milestones
| Week | RBAC milestone | Primary owner |
|---|---|---|
| 1 | Freeze role set and capability registry draft | A + B |
| 2 | Finalize institution-scoped access contract and endpoint capability map | A |
| 3 | Publish compatibility-window migration plan (`role` + `capabilities`) | A + B |
| 4 | Complete backend authorization dependency design and error contract alignment | A |
| 5 | Complete frontend role/capability UX visibility and navigation policy spec | C |
| 6 | Finalize authorization test matrix (allow, deny, cross-institution, fallback) | B |
| 7 | Run controlled local rollout with telemetry, mismatch logging, and rollback drill | All |
| 8 | Lock cutover readiness and deprecate legacy role-only path (if thresholds met) | All |

### RBAC phase gates
1. **Docs gate**: contracts merged in canonical docs before implementation PRs.
2. **Security gate**: privileged and cross-institution deny paths tested and auditable.
3. **Compatibility gate**: mismatch telemetry remains below agreed threshold.
4. **Cutover gate**: role fallback is removed only after sustained stability window.

### Team split for RBAC work
- Developer A: backend auth service updates, dependency guards, migration compatibility logic.
- Developer B: capability matrix governance, policy test harness, telemetry checks.
- Developer C: frontend role-aware routes, navigation guards, and regression UX checks.

## Phase Acceptance Criteria
### Phase 0 Foundation and planning
- Canonical docs are complete through architecture, data, execution, and QA.
- Module boundaries and source-of-truth rules are stable.
- Human review checkpoints are defined.

### Phase 1 Core product and data layer
- Scholarship data model supports `raw`, `validated`, and `published`.
- Curation workflow and discovery baseline are implementation-ready.
- Search and detail experience requirements are locked.

### Phase 2 Recommendation and explainability features
- Recommendation stages and fallback path are defined and testable.
- Explanation payload format is stable.
- Document assistance and interview baseline have bounded AI behavior.

### Phase 3 Research evaluation and polish
- Judged-set evaluation can be run end-to-end.
- Explanation study materials exist.
- Core UI flows are coherent and polished enough for demo and pilot study use.

### Phase 4 Final hardening, thesis packaging, and future roadmap
- Documentation matches the implemented system.
- Regression and demo runs are stable.
- Final report artifacts and roadmap are ready.

## Dependencies
1. Data model and curation workflow before recommendation logic.
2. Recommendation contracts before explanation UI.
3. Explanation and preparation contracts before evaluation design.
4. Evaluation assets before final thesis packaging.

## Testing Milestones
| Week | Testing checkpoint |
|---|---|
| 2 | Contract review for schema and endpoint definitions |
| 6 | Data validation and curation-flow tests defined |
| 8 | Recommendation-stage unit and integration test plan defined |
| 10 | End-to-end product flow tests defined for core screens |
| 13 | Research evaluation and regression suite frozen |
| 15 | Final demo rehearsal and failure-mode drills |

## Documentation Milestones
| Week | Deliverable |
|---|---|
| 1 | Core docs pack completed |
| 6 | Data and curation docs checked against implementation plan |
| 10 | Recommendation, XAI, and backend docs updated to match actual design |
| 14 | QA, DevOps, and risk docs finalized |
| 16 | Thesis packaging and future roadmap complete |

## Demo Milestones
| Week | Demo focus |
|---|---|
| 2 | Documentation and architecture review demo |
| 6 | Data curation and scholarship discovery demo |
| 10 | Recommendation and preparation workflow demo |
| 13 | Evaluation and polished UX demo |
| 16 | Final end-to-end thesis demo |

## AI-Assisted Development Workflow
1. Use AI tools for drafting, scaffolding, and review assistance.
2. Keep all generated artifacts mapped to documented module boundaries.
3. Require human review before accepting generated schema, ranking, or security logic.
4. Treat prompts, generated code, and generated tests as versioned artifacts worth reviewing.

## Human Review Checkpoints Before Code Acceptance
| Checkpoint | Reviewer expectation |
|---|---|
| Schema changes | Backend owner plus one additional reviewer |
| Recommendation logic changes | ML owner plus one additional reviewer |
| User-facing explanation changes | Frontend owner plus one additional reviewer |
| Curation workflow changes | Backend owner and curator workflow reviewer |
| Security-sensitive changes | Backend owner plus whole-team signoff for v0.1 SLC-critical paths |

## Schedule Risk Management
### Cut last if schedule slips
- Published scholarship discovery
- Curation-state workflow
- Rules-first recommendation baseline
- Core explanation panel

### Cut first if schedule slips
- Audio interview support
- advanced model comparison breadth
- non-critical admin analytics
- experimental UX variants
## SLC decision (v0.1)
- Phase-complete delivery focused on reliable data, usable ranking, and polished core workflows.

## Future Research Extensions
- Larger evaluation studies and graph-layer experiments after v0.1 SLC stabilization.

## Deferred By Stage
- Commercial roadmap exploration only after core product reliability and thesis packaging are complete.

## SLC decision (v0.1)
ScholarAI will be delivered through five explicit phases over 16 weeks, with data reliability and curation foundations completed before recommendation sophistication or startup-style expansion.

## Deferred items
- Broader commercialization work during the FYP timeline.
- Non-essential admin analytics and advanced UX experiments if schedule pressure rises.
- Audio-first interview as a guaranteed feature.

## Assumptions
- The team can maintain the documented ownership split with some overlap for reviews.
- Documentation remains ahead of implementation rather than trailing it.
- Pilot evaluation recruitment happens early enough to avoid end-of-project compression.

## Risks
- Frontloading too little documentation will cause downstream rework.
- Recommendation and evaluation work can overrun if data foundations are late.
- Scope creep in AI features can threaten the final hardening phase.

