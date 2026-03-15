# ScholarAI Research And Evaluation

## Purpose
This document frames ScholarAI as an FYP-level research system and defines an evaluation plan that is academically defensible under current data constraints.

## Research Problem Statement
Scholarship discovery is fragmented, eligibility interpretation is often opaque, and generic AI writing tools are poorly grounded in scholarship-specific context. ScholarAI studies whether a structured, explainable, and guidance-oriented system can improve prioritization and preparation without overstating what the data can support.

## Research Questions
| ID | Question |
|---|---|
| RQ1 | Does eligibility-aware hybrid ranking improve recommendation quality over simpler baselines in a constrained scholarship corpus? |
| RQ2 | Do structured explanations improve user trust and actionability compared with ranked results alone? |
| RQ3 | Can bounded document-assistance RAG provide useful feedback while maintaining grounding and citation discipline? |
| RQ4 | Can rubric-based interview practice deliver feedback that users perceive as useful without being presented as authoritative judgment? |

## Hypotheses
| ID | Hypothesis |
|---|---|
| H1 | Rules plus vector retrieval will outperform rules-only baselines on ranking quality metrics. |
| H2 | Structured explanations will increase self-reported trust and actionability compared with unexplained recommendations. |
| H3 | Citation-grounded document feedback will achieve higher reviewer-rated usefulness than unguided generic feedback prompts. |
| H4 | Rubric-based interview feedback will show moderate alignment with human judgments on a pilot evaluation set. |

## Academic Contribution
| Area | Contribution |
|---|---|
| Recommendation systems | A constrained scholarship-domain hybrid recommender with explicit rule grounding |
| Explainability | Explanation design and user-study framing for scholarship recommendation trust |
| Applied NLP | A bounded RAG approach that keeps policy truth separate from generated guidance |
| Human-AI interaction | Scholarship-oriented interview-practice workflow with rubric-based feedback |

## Engineering Contribution
| Area | Contribution |
|---|---|
| Data reliability | A provenance-aware curation pipeline from `raw` to `validated` to `published` |
| System design | A documentation-first modular monolith that a 3-person team can implement |
| Evaluation discipline | A product and research plan that avoids unsupported predictive claims |

## Novelty Claim
ScholarAI's novelty does not rely on claiming breakthrough prediction of scholarship outcomes. The defensible novelty claim is the combination of:
- structured scholarship curation with explicit provenance
- eligibility-aware hybrid ranking
- explanation-oriented recommendation presentation
- bounded scholarship-preparation assistance inside one coherent system

## Evaluation Methodology
### Evaluation tracks
| Track | Method |
|---|---|
| Recommendation quality | Offline judged-set evaluation across baselines |
| Explainability usefulness | User study with explanation and no-explanation variants |
| Document assistance | Grounding and usefulness review on curated examples |
| Interview practice | Pilot human comparison against rubric outputs |
| System performance | Load and latency measurement on core paths |

## Recommendation Quality Metrics
| Metric | Why it matters |
|---|---|
| Precision@K | Measures top-result usefulness |
| Recall@K | Measures whether good candidates are surfaced |
| NDCG@K | Measures ranking quality beyond binary relevance |
| MRR | Measures speed to first strong candidate |
| Constraint violation rate | Measures trust-critical failures |
| Coverage | Measures whether ranking works across the published corpus |

## Explainability User Study
### Study design
- Compare recommendation views with and without explanation panels.
- Use representative scholarship-search tasks, not abstract questionnaires alone.
- Collect perceived trust, clarity, and actionability scores.

### Candidate measures
| Measure | Type |
|---|---|
| Trust score | Likert-style subjective measure |
| Actionability | Likert-style subjective measure |
| Explanation comprehension | Short task-based comprehension check |
| Willingness to apply | Behavioral intention measure |

### Statistical tests
- Paired t-test if assumptions are met
- Wilcoxon signed-rank test if data is non-normal
- Effect size reporting for either path

## System Performance Evaluation
| Area | Metric |
|---|---|
| Recommendation latency | P50, P95, P99 |
| Ingestion stability | success rate, partial-failure rate |
| Document-feedback turnaround | end-to-end response time |
| Interview session turnaround | prompt generation and feedback latency |
| Resource usage | CPU and memory during core demo workloads |

## Candidate Statistical Tests
| Comparison | Candidate test |
|---|---|
| Ranking metrics across judged queries | Paired bootstrap or Wilcoxon signed-rank |
| Explanation/no-explanation trust study | Paired t-test or Wilcoxon signed-rank |
| Human versus model rubric alignment | Spearman correlation or weighted kappa |
| Failure-rate differences | McNemar or chi-square where appropriate |

## Data And Label Constraints
There is no true large-scale public scholarship outcome dataset for this domain. Because of that:
- ML scoring must be framed as estimate-based ranking
- synthetic labels may be used for training support, not for causal claims
- judged relevance sets are more defensible than fabricated success labels

## Reproducibility Plan
1. Version all datasets, prompts, and schema definitions.
2. Record seeds for synthetic data generation.
3. Version embedding and reranking model names.
4. Preserve judged-set guidelines and annotation rubrics.
5. Record exact evaluation scripts and metric definitions.
6. Keep documentation aligned with the implementation actually evaluated.

## Threats To Validity
| Threat | Impact |
|---|---|
| Synthetic-label bias | Model quality may reflect the label heuristic more than reality |
| Small or narrow corpus | Results may not generalize beyond the MVP scope |
| Annotation subjectivity | Judged-set relevance may vary by reviewer |
| User-study recruitment bias | Student sample may not represent broader applicant populations |
| UI confounds | Trust outcomes may reflect interface quality as much as explanation content |

## Ethical Considerations
1. Do not present estimated fit scores as admissions truth.
2. Keep user data handling minimal and purpose-bound.
3. Preserve transparency around model limitations and missing data.
4. Avoid encouraging users to ignore official scholarship requirements.
5. Use human review where scholarship facts affect publication.

## MVP
- Offline evaluation of recommendation baselines.
- Explanation user study on a feasible pilot cohort.
- Document-feedback grounding checks.
- Core performance measurement on recommendation, ingestion, and AI assistance paths.

## Future Research Extensions
- Larger longitudinal studies with real usage data.
- Comparative graph-database evaluation.
- Stronger causal or predictive claims only if true outcome labels are available.

## Post-MVP Startup Features
- Product analytics that connect recommendation behavior to downstream application actions.
- Provider-facing reporting products based on validated aggregate behavior.

## MVP decision
ScholarAI research will focus on explainable, eligibility-aware ranking and grounded preparation workflows, with evaluation methods chosen to match the limited but realistic data available in MVP.

## Deferred items
- Real-world acceptance prediction studies.
- Large-scale longitudinal outcome modeling.
- Broad generalization claims outside the MVP corpus.

## Assumptions
- A judged-set evaluation is feasible within the project timeline.
- A pilot user study can recruit enough participants for directional findings.
- Documentation, prompts, and evaluation scripts will remain versioned together.

## Risks
- Overclaiming novelty or predictive power would weaken thesis defensibility.
- Small sample sizes may limit statistical power.
- Evaluation quality will suffer if annotation guidelines are weak or inconsistent.
