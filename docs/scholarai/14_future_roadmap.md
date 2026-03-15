# ScholarAI Future Roadmap

## Purpose
This document separates near-term post-MVP improvements from longer-horizon research and startup opportunities so that the MVP remains disciplined while still preserving a growth path.

## Short-Term Post-MVP Improvements
| Area | Improvement |
|---|---|
| Corpus quality | Expand validated Canadian scholarship coverage within the same MS scope |
| Recommendation quality | Refine judged-set evaluation and improve reranker calibration behavior |
| Explanation UX | Improve explanation comparisons and transparency around uncertainty |
| Document assistance | Better workflows for revision tracking and version comparison |
| Admin tooling | Better queue management and curation productivity features |

## Future Research Extensions
| Area | Research direction |
|---|---|
| DAAD | Add DAAD as a deferred research-track corpus |
| Graph evaluation | Compare relational graph abstraction with narrowly scoped Neo4j |
| Outcome data | Study how voluntary outcome labels affect fit and competitiveness modeling |
| Explainability | Evaluate alternative explanation formats and their trust effects |
| Interview practice | Correlate rubric-based outputs with human evaluator scores at larger scale |

## Startup-Scale Features
| Area | Opportunity |
|---|---|
| Geography expansion | Broaden beyond Canada once curation operations are stable |
| Additional degree levels | Expand to other postgraduate programs before undergraduate breadth |
| Provider tooling | Provider-submitted scholarship data with review workflows |
| Institution tooling | Dashboards for scholarship offices and program admins |
| Student workflow | Reminder systems, planning timelines, and collaboration features |

## Data Moat Strategy
### Near-term
- Build a clean, validated scholarship dataset with provenance and freshness signals.
- Maintain structured eligibility and funding fields that generic directories often ignore.

### Medium-term
- Add curator-reviewed corrections and change histories.
- Capture anonymized interaction patterns to improve ranking quality cautiously.

### Long-term
- Collect voluntary post-application outcomes and revision histories.
- Build higher-quality provider and institution relationships around validated data submission.

## Partnership And Provider-Submitted Data Possibilities
| Partner type | Opportunity | Constraint |
|---|---|---|
| Universities | Structured scholarship updates and program-specific funding data | Must remain curator-reviewed |
| Scholarship providers | Direct record submission and correction workflows | Needs moderation and audit trail |
| Advisors or mentors | Feedback or review workflows | Not part of MVP |

## Monetization-Supporting Capabilities
### Post-MVP possibilities
- premium application-planning workflows
- institution or provider analytics dashboards
- sponsored but clearly labeled scholarship visibility
- operational tooling for data submission and validation

Monetization should not distort source-of-truth governance or ranking transparency.

## Roadmap Separation
### MVP
- Canada-first validated scholarship discovery
- eligibility-aware ranking
- grounded preparation support

### Future Research Extensions
- DAAD
- graph-comparison studies
- richer evaluation and label collection

### Post-MVP Startup Features
- market expansion
- partner integrations
- monetization-supporting tooling

## Strategic Guardrails
1. Do not expand geography faster than curation quality can support.
2. Do not let monetization pressure compromise publication trust.
3. Do not add startup-scale infrastructure before product reliability is proven.
4. Keep the Knowledge Graph Layer and explanation discipline intact as the product grows.

## MVP decision
ScholarAI will treat the current MVP as a trust-and-data foundation, while using the roadmap to sequence research expansion and startup opportunities without leaking them into the core deliverable.

## Deferred items
- DAAD and broad international expansion.
- Provider self-service workflows.
- Institution analytics products and monetization tooling.

## Assumptions
- A stronger data asset is more strategically valuable than rapid feature sprawl.
- Expansion will happen first through better validated coverage, not through uncontrolled scraping breadth.
- Provider partnerships are only useful if moderation and provenance remain strong.

## Risks
- Premature expansion can destroy the data-quality advantage of the MVP.
- Monetization features can bias ranking or trust if governance is weak.
- Partner-submitted data can become noisy unless curator review remains mandatory.
