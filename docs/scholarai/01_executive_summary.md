# ScholarAI Executive Summary

## Purpose
ScholarAI is an AI-powered scholarship platform that helps students discover verified opportunities, understand fit, prepare stronger applications, and track progress in one system. This documentation pack defines an implementation-ready **v0.1 SLC** release for a 3-person team.

## Problem Summary
Students face fragmented scholarship information, unclear eligibility interpretation, manual planning burden, and generic preparation tools. Many products either stop at directories or provide opaque AI outputs that are hard to trust.

## Product Thesis
ScholarAI reduces information friction without pretending to automate final scholarship outcomes. The product combines validated data, eligibility-aware filtering, explainable fit guidance, preparation workflows, and tracker visibility in a single coherent journey.

## What ScholarAI Delivers
| Area | User outcome | v0.1 SLC stance |
|---|---|---|
| Discovery | Students can search a curated scholarship corpus | Canada-first with strict provenance quality |
| Eligibility | Students can see hard constraints clearly | Structured validated rules are authoritative |
| Recommendation | Students receive ranked opportunities with transparent rationale | Guidance bands, not deterministic claims |
| Application support | Students get bounded SOP/CV/essay improvement support | Advisory only; facts stay data-grounded |
| Interview practice | Students rehearse scholarship-style questions with feedback | Actionable, rubric-style coaching |

## v0.1 SLC Scope Summary
### v0.1 SLC
- Canada-first scholarship and program corpus.
- Program focus: MS Data Science, MS Artificial Intelligence, MS Analytics.
- USA scope only for narrowly scoped Fulbright-related cross-border context.
- Modular monolith architecture with one Next.js frontend and one FastAPI backend.
- PostgreSQL + pgvector baseline with relationally derived graph abstraction.
- Core loops: discovery, fit understanding, save/track, document prep, interview prep, curation operations.

### Future Research Extensions
- Comparative evaluation of graph-layer implementations.
- Better experimental design for explanation helpfulness and trust outcomes.
- Expanded outcome-label collection for model evaluation rigor.

### Deferred By Stage
- v0.2: richer recommendation depth and preparation workflows.
- v0.3: mentor and stronger operations expansions.
- v1.x: partner/institution ecosystem capabilities and commercial scale surfaces.

## Delivery Model
| Constraint | Decision |
|---|---|
| Team | 3 developers |
| Timeline | 16 weeks |
| Budget | Limited |
| Development style | Documentation-first, SLC-first |
| Deployment baseline | Docker Compose |
| CI/CD baseline | GitHub Actions |

## Research Position
The defensible research framing is not acceptance prediction. It is explainable ranking, policy-grounded eligibility workflows, and structured advisory feedback in a constrained scholarship domain.

## Source-Of-Truth Principle
Structured validated data is authoritative for eligibility, deadlines, funding rules, and official scholarship requirements. Generated outputs support preparation but do not override validated facts.

## Implementation Posture
ScholarAI should be built as the simplest defensible product that demonstrates:
1. Curated ingestion and validation.
2. Eligibility-aware ranking with explainability.
3. Useful, bounded preparation workflows.
4. Premium, role-aware, evidence-verified UI quality.

## SLC decision (v0.1)
ScholarAI v0.1 is a Canada-first, premium-feeling, modular-monolith product that delivers discovery, explainable fit guidance, and preparation support without overstating AI certainty.

## Deferred By Stage
- Broader geography and provider expansion.
- Mentor marketplace or heavy collaboration workflows.
- Claims requiring real scholarship outcome labels.

## Assumptions
- A constrained, high-quality corpus creates stronger trust than broad noisy coverage.
- Transparent fit guidance is more useful than opaque scoring.
- Evidence-driven QA prevents false confidence from green CI alone.

## Risks
- Legacy pre-SLC language may cause mixed product expectations.
- Narrow scope may be perceived as limited without clear messaging.
- Advisory outputs can be over-trusted if boundaries are not explicit in UI.
