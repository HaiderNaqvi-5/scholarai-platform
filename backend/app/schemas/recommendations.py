from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RecommendationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    limit: int = Field(default=10, ge=1, le=25)


class RecommendationEvaluationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    predicted_ids: list[str] = Field(min_length=1)
    judged_relevance: dict[str, int] = Field(min_length=1)
    k_values: list[int] = Field(default_factory=lambda: [1, 3, 5, 10], min_length=1)
    thresholds: list["RecommendationMetricThresholdItem"] = Field(default_factory=list)
    baseline_metrics: list["RecommendationMetricItem"] = Field(default_factory=list)


class RecommendationMetricItem(BaseModel):
    k: int = Field(ge=1)
    precision_at_k: float = Field(ge=0.0, le=1.0)
    recall_at_k: float = Field(ge=0.0, le=1.0)
    ndcg_at_k: float = Field(ge=0.0, le=1.0)


class RecommendationMetricThresholdItem(BaseModel):
    k: int = Field(ge=1)
    precision_at_k_min: float | None = Field(default=None, ge=0.0, le=1.0)
    recall_at_k_min: float | None = Field(default=None, ge=0.0, le=1.0)
    ndcg_at_k_min: float | None = Field(default=None, ge=0.0, le=1.0)
    ndcg_delta_min: float | None = None


class RecommendationKPIGateItem(BaseModel):
    k: int = Field(ge=1)
    precision_at_k_pass: bool | None = None
    recall_at_k_pass: bool | None = None
    ndcg_at_k_pass: bool | None = None
    ndcg_delta_pass: bool | None = None
    ndcg_delta_value: float | None = None
    all_passed: bool


class RecommendationEvaluationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metrics: list[RecommendationMetricItem]
    kpi_gates: list[RecommendationKPIGateItem] = Field(default_factory=list)
    kpi_passed: bool | None = None
    policy_version: str
    metric_set: str
    pipeline_version: str


class RecommendationSignalLanguage(BaseModel):
    facts_label: str
    estimated_signals_label: str
    estimated_signals_notice: str


class RecommendationFactor(BaseModel):
    code: str
    label: str
    detail: str
    stage: Literal["scope", "eligibility", "retrieval", "rerank", "explanation"]
    source: Literal[
        "published_record",
        "validated_rule",
        "profile_input",
        "retrieval_model",
        "rerank_model",
    ]
    direction: Literal["supports", "limits", "neutral"]
    numeric_value: float | None = None
    display_value: str | None = None


class RecommendationStageDetail(BaseModel):
    status: Literal["applied", "fallback", "skipped"]
    summary: str
    factors: list[RecommendationFactor] = Field(default_factory=list)


class RecommendationRationaleStages(BaseModel):
    scope: RecommendationStageDetail
    eligibility: RecommendationStageDetail
    retrieval: RecommendationStageDetail
    rerank: RecommendationStageDetail
    explanation: RecommendationStageDetail


class RecommendationRationale(BaseModel):
    summary: str
    facts: list[RecommendationFactor] = Field(default_factory=list)
    estimated_signals: list[RecommendationFactor] = Field(default_factory=list)
    stages: RecommendationRationaleStages


class RecommendationItem(BaseModel):
    scholarship_id: str
    title: str
    provider_name: str | None
    country_code: str
    deadline_at: datetime | None
    record_state: str
    estimated_fit_score: float
    fit_band: str
    match_summary: str
    matched_criteria: list[str]
    constraint_notes: list[str]
    top_reasons: list[str]
    warnings: list[str]
    shap_explanation: dict[str, float] | None = None
    retrieval_source: str
    semantic_similarity: float | None = None
    rule_pass_count: int = Field(ge=0)
    rule_total_count: int = Field(ge=0)
    heuristic_factors: dict[str, float]
    fallback_reason: str | None = None
    eligibility_graph: dict[str, Any]
    signal_language: RecommendationSignalLanguage | None = None
    rationale: RecommendationRationale | None = None


class RecommendationResponseMeta(BaseModel):
    scope_policy: str
    allowed_country_codes: list[str]
    exception_policy: str
    pipeline_version: str


class RecommendationListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[RecommendationItem]
    total: int = Field(ge=0)
    meta: RecommendationResponseMeta | None = None


class RecommendationBenchmarkCaseDefinition(BaseModel):
    case_id: str = Field(min_length=1, max_length=120)
    profile_label: str = Field(min_length=1, max_length=255)
    predicted_ids: list[str] = Field(min_length=1)
    judged_relevance: dict[str, int] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_case(self) -> "RecommendationBenchmarkCaseDefinition":
        deduplicated_ids = [item for item in self.predicted_ids if item]
        if len(deduplicated_ids) != len(set(deduplicated_ids)):
            raise ValueError("predicted_ids must not include duplicates")

        invalid_scores = [value for value in self.judged_relevance.values() if value < 0]
        if invalid_scores:
            raise ValueError("judged_relevance scores must be greater than or equal to zero")

        if not any(value > 0 for value in self.judged_relevance.values()):
            raise ValueError("judged_relevance must include at least one positive relevance score")

        return self


class RecommendationBenchmarkDataset(BaseModel):
    dataset_id: str = Field(min_length=1, max_length=120)
    version: str = Field(min_length=1, max_length=120)
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    frozen_at: datetime
    k_values: list[int] = Field(min_length=1)
    thresholds: list[RecommendationMetricThresholdItem] = Field(default_factory=list)
    baseline_metrics: list[RecommendationMetricItem] = Field(default_factory=list)
    cases: list[RecommendationBenchmarkCaseDefinition] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_dataset(self) -> "RecommendationBenchmarkDataset":
        normalized_k_values = sorted(set(self.k_values))
        if any(value < 1 for value in normalized_k_values):
            raise ValueError("k_values must be positive integers")
        self.k_values = normalized_k_values

        case_ids = [item.case_id for item in self.cases]
        if len(case_ids) != len(set(case_ids)):
            raise ValueError("cases must use unique case_id values")

        threshold_k_values = [item.k for item in self.thresholds]
        if len(threshold_k_values) != len(set(threshold_k_values)):
            raise ValueError("thresholds must not repeat the same k value")

        baseline_k_values = [item.k for item in self.baseline_metrics]
        if len(baseline_k_values) != len(set(baseline_k_values)):
            raise ValueError("baseline_metrics must not repeat the same k value")

        return self


class RecommendationBenchmarkSummary(BaseModel):
    dataset_id: str
    version: str
    title: str
    frozen_at: datetime
    case_count: int = Field(ge=1)
    k_values: list[int]
    policy_version: str


class RecommendationBenchmarkListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[RecommendationBenchmarkSummary]
    total: int = Field(ge=0)


class RecommendationBenchmarkCaseResult(BaseModel):
    case_id: str
    profile_label: str
    metrics: list[RecommendationMetricItem]
    kpi_gates: list[RecommendationKPIGateItem]
    kpi_passed: bool


class RecommendationBenchmarkGatePassRateItem(BaseModel):
    k: int = Field(ge=1)
    pass_rate: float = Field(ge=0.0, le=1.0)


class RecommendationBenchmarkAggregate(BaseModel):
    case_count: int = Field(ge=0)
    pass_count: int = Field(ge=0)
    pass_rate: float = Field(ge=0.0, le=1.0)
    average_metrics: list[RecommendationMetricItem]
    gate_pass_rates: list[RecommendationBenchmarkGatePassRateItem]


class RecommendationBenchmarkEvaluationResponse(BaseModel):
    dataset_id: str
    version: str
    title: str
    policy_version: str
    metric_set: str
    pipeline_version: str
    case_results: list[RecommendationBenchmarkCaseResult]
    aggregate: RecommendationBenchmarkAggregate
