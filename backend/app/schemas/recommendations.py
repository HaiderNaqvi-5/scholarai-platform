from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class RecommendationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    limit: int = Field(default=10, ge=1, le=25)


class RecommendationEvaluationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    predicted_ids: list[str] = Field(min_length=1)
    judged_relevance: dict[str, int] = Field(min_length=1)
    k_values: list[int] = Field(default_factory=lambda: [1, 3, 5, 10], min_length=1)


class RecommendationMetricItem(BaseModel):
    k: int = Field(ge=1)
    precision_at_k: float = Field(ge=0.0, le=1.0)
    recall_at_k: float = Field(ge=0.0, le=1.0)
    ndcg_at_k: float = Field(ge=0.0, le=1.0)


class RecommendationEvaluationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metrics: list[RecommendationMetricItem]
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
