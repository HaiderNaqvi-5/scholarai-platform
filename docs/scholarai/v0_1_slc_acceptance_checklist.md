# v0.1 SLC Acceptance Checklist

Use this checklist as the release acceptance source of truth for ScholarAI `v0.1 SLC`.

## Core Loop

| ID | Capability | Acceptance Evidence |
| --- | --- | --- |
| SLC-CORE-001 | Browse scholarship opportunities with filterable list and detail view. | Browser screenshot + API response sample |
| SLC-CORE-002 | Fit scoring is visible and traceable to structured profile inputs. | Screenshot + scoring payload excerpt |
| SLC-CORE-003 | Save/shortlist flow persists across refresh and sessions. | Screenshot + persistence log/API evidence |
| SLC-CORE-004 | Preparation guidance is available for selected scholarship targets. | Screenshot + generated preparation artifact |
| SLC-CORE-005 | Progress tracking reflects current state transitions (saved/applied/in-progress). | Screenshot + state transition evidence |

## Role Homes

| ID | Capability | Acceptance Evidence |
| --- | --- | --- |
| SLC-ROLE-001 | Student home exposes core loop entry points and personal progress summary. | Desktop + mobile screenshots |
| SLC-ROLE-002 | Admin home exposes moderation, curation, and operational controls. | Desktop + mobile screenshots |
| SLC-ROLE-003 | Owner home exposes platform oversight and governance controls. | Desktop + mobile screenshots |
| SLC-ROLE-004 | Mentor home exposes advisory workflows scoped to mentor permissions. | Desktop + mobile screenshots |
| SLC-ROLE-005 | Test-user home is constrained and clearly marked for non-production usage. | Desktop + mobile screenshots |

## Admin and Owner Operations

| ID | Capability | Acceptance Evidence |
| --- | --- | --- |
| SLC-OPS-001 | Admin can manage structured data lifecycle (add/update/archive) with auditability. | UI proof + audit/event record |
| SLC-OPS-002 | Owner can review stage conformance and governance policy adherence. | UI proof + governance artifact |
| SLC-OPS-003 | Role assignment and permission updates are tracked and reversible. | UI proof + audit record |

## Trust Boundaries

| ID | Capability | Acceptance Evidence |
| --- | --- | --- |
| SLC-TRUST-001 | Validated facts are explicitly distinguished from advisory AI guidance. | Screenshot + copy excerpt |
| SLC-TRUST-002 | Advisory AI responses include explainability cues and non-authoritative framing. | Screenshot + response excerpt |
| SLC-TRUST-003 | Structured data remains the authority for critical scholarship facts. | Data/API evidence + UI proof |

## UI Quality Evidence

| ID | Capability | Acceptance Evidence |
| --- | --- | --- |
| SLC-UI-001 | Every UI-affecting PR includes desktop screenshots for changed surfaces. | PR UI evidence links |
| SLC-UI-002 | Every UI-affecting PR includes mobile screenshots for changed surfaces. | PR UI evidence links |
| SLC-UI-003 | UI evidence is tied to checklist IDs in Acceptance Criteria Mapping. | PR checklist mapping section |

## Execution Evidence Log (2026-03-28)

| ID | Status | Evidence Link(s) |
| --- | --- | --- |
| SLC-TRUST-001 | In Progress | [Grounding/Citation evidence artifact](https://github.com/HaiderNaqvi-5/scholarai-platform/blob/split/pr50-ci-e2e-smoke/tests/artifacts/verification/v0_1_grounding_citation_evidence_2026-03-28.md) *(evidence tracked in PR #54 artifacts)* |
| SLC-TRUST-002 | In Progress | [Grounding/Citation evidence artifact](https://github.com/HaiderNaqvi-5/scholarai-platform/blob/split/pr50-ci-e2e-smoke/tests/artifacts/verification/v0_1_grounding_citation_evidence_2026-03-28.md) *(evidence tracked in PR #54 artifacts)* |
| SLC-TRUST-003 | In Progress | [Grounding/Citation evidence artifact](https://github.com/HaiderNaqvi-5/scholarai-platform/blob/split/pr50-ci-e2e-smoke/tests/artifacts/verification/v0_1_grounding_citation_evidence_2026-03-28.md) *(evidence tracked in PR #54 artifacts)* |
| SLC-UI-001 | Pending screenshots | [Grounding/Citation evidence artifact](https://github.com/HaiderNaqvi-5/scholarai-platform/blob/split/pr50-ci-e2e-smoke/tests/artifacts/verification/v0_1_grounding_citation_evidence_2026-03-28.md) *(evidence tracked in PR #54 artifacts)* |
| SLC-UI-002 | Pending screenshots | [Grounding/Citation evidence artifact](https://github.com/HaiderNaqvi-5/scholarai-platform/blob/split/pr50-ci-e2e-smoke/tests/artifacts/verification/v0_1_grounding_citation_evidence_2026-03-28.md) *(evidence tracked in PR #54 artifacts)* |
| SLC-UI-003 | In Progress | [Grounding/Citation evidence artifact](https://github.com/HaiderNaqvi-5/scholarai-platform/blob/split/pr50-ci-e2e-smoke/tests/artifacts/verification/v0_1_grounding_citation_evidence_2026-03-28.md) *(evidence tracked in PR #54 artifacts)* |
| SLC-CORE-004 | In Progress | [Grounding/Citation evidence artifact](https://github.com/HaiderNaqvi-5/scholarai-platform/blob/split/pr50-ci-e2e-smoke/tests/artifacts/verification/v0_1_grounding_citation_evidence_2026-03-28.md) *(evidence tracked in PR #54 artifacts)* |

## Completion Rule

`v0.1 SLC` is release-ready only when all applicable IDs above are marked complete with evidence links and no open high-risk exceptions.
