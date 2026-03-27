# ScholarAI Executive Summary

## Purpose
ScholarAI is an AI-powered scholarship platform designed to help students discover relevant scholarships, check core eligibility, plan stronger applications, improve application documents, and practice scholarship interviews. This documentation pack defines an implementation-ready v0.1 that a 3-person team can realistically deliver in 16 weeks.

## Problem Summary
Students face a fragmented scholarship ecosystem. Official requirements are scattered across university pages, provider pages, and policy documents. Eligibility logic is often unclear, application planning is manual, and document support is generic rather than scholarship-specific. Existing tools usually stop at directory listings or generic writing help.

## Product Thesis
ScholarAI should reduce information friction without pretending to automate final admission decisions. The platform combines structured scholarship data, eligibility-aware filtering, explainable ranking, application guidance, and interview practice in one workflow. The system is designed so that structured validated data remains authoritative for all policy-critical fields.

## What ScholarAI Delivers
| Area | User outcome | Implementation stance |
|---|---|---|
| Discovery | Students can search a curated scholarship corpus | Canada-first v0.1 with targeted ingestion |
| Eligibility | Students can see whether basic hard constraints are met | Structured validated rules are authoritative |
| Recommendation | Students receive ranked opportunities with transparent reasoning | Use Estimated Scholarship Fit Score, not causal success claims |
| Application support | Students get feedback on SOPs, essays, and related documents | RAG is limited to feedback and improvement guidance |
| Interview practice | Students rehearse scholarship-style questions and receive structured feedback | Feedback is advisory, not authoritative |

## v0.1 Scope Summary
### v0.1
- Canada-first scholarship and program corpus.
- Program focus: MS Data Science, MS Artificial Intelligence, MS Analytics.
- USA scope limited to Fulbright-related provider information and narrowly scoped cross-border logic.
- Modular monolith architecture with one Next.js frontend and one FastAPI backend.
- PostgreSQL + pgvector as the primary data and retrieval foundation.
- Knowledge Graph Layer implemented logically, with a relationally derived graph abstraction as the default v0.1 approach.
- Core workflows: discovery, eligibility-aware ranking, application guidance, interview practice, and admin curation.

### Future Research Extensions
- DAAD-focused ingestion and evaluation.
- Comparative evaluation of relational graph abstraction versus narrowly scoped Neo4j deployment.
- Stronger experiment design for explanation helpfulness, trust, and ranking utility.
- Better outcome-label collection and reproducibility workflows for model evaluation.

### Deferred By Stage Startup Features
- Broader geography and program expansion.
- Mentor marketplace or paid advisory workflows.
- Institution dashboards and provider analytics.
- Workflow automation for reminders, collaboration, and operational reporting.

## Delivery Model
| Constraint | Decision |
|---|---|
| Team | 3 developers |
| Timeline | 16 weeks |
| Budget | Limited |
| Development style | Documentation-first, v0.1-first |
| Deployment baseline | Docker Compose |
| CI/CD baseline | GitHub Actions |

## Research Position
ScholarAI is both an FYP and a startup-ready v0.1 foundation. The strongest research angle is not "AI predicts who wins scholarships." The defensible research angle is that ScholarAI can study explainable ranking, policy-grounded eligibility workflows, and structured AI feedback in a constrained scholarship domain. Any ML output must be framed as an estimate rather than a causal prediction unless real outcome labels exist.

## Source-Of-Truth Principle
ScholarAI treats structured validated data as the authority for:
- eligibility
- deadlines
- funding rules
- official scholarship requirements

Generated outputs can support writing, reflection, and practice, but they do not override validated scholarship data.

## Implementation Posture
ScholarAI should be built as the simplest defensible system that can demonstrate:
1. Curated ingestion and validation.
2. Eligibility-aware ranking.
3. Explainable outputs.
4. Useful student-facing preparation workflows.
5. A premium but feasible frontend experience.

## v0.1 decision
ScholarAI v0.1 is a Canada-first, modular-monolith scholarship platform that delivers discovery, eligibility-aware ranking, document guidance, and interview practice without claiming authoritative prediction of scholarship outcomes.

## Deferred items
- DAAD-specific v0.1 ingestion.
- Broad USA university discovery.
- Mentor marketplace features.
- Claims that require real scholarship outcome labels.

## Assumptions
- A constrained Canada-first corpus is sufficient for v0.1 validation and FYP scope control.
- A relationally derived graph abstraction is the simplest defensible default for the Knowledge Graph Layer in v0.1.
- Users benefit from transparent reasoning even when recommendations are only estimated fit signals.

## Risks
- If scholarship rules are not validated carefully, user trust will collapse quickly.
- A narrow corpus may limit perceived coverage even if it improves data quality.
- Interview and document feedback can be useful but still subjective, which must be communicated clearly.


## SLC decision (v0.1)
TBD (baseline governance alignment).
