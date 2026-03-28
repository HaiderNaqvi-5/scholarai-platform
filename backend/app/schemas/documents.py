from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DocumentValidatedFact(BaseModel):
    scholarship_id: str
    scholarship_title: str
    label: str
    value: str
    source_url: str


class DocumentRetrievedGuidanceSnippet(BaseModel):
    key: str
    topic: str
    snippet: str
    applies_to: str


class DocumentGeneratedGuidanceItem(BaseModel):
    type: str
    guidance: str


class DocumentQualityMetrics(BaseModel):
    citation_coverage_ratio: float = Field(ge=0.0, le=1.0)
    validated_fact_count: int = Field(ge=0)
    retrieved_guidance_count: int = Field(ge=0)
    generated_guidance_count: int = Field(ge=0)
    grounded_partition_count: int = Field(ge=0)
    actionable_guidance_count: int = Field(ge=0)
    fact_to_guidance_link_ratio: float = Field(ge=0.0, le=1.0)
    caution_note_count: int = Field(ge=0)
    review_flag: bool


class DocumentQualityThresholds(BaseModel):
    min_citation_coverage_ratio: float = Field(ge=0.0, le=1.0)
    max_caution_note_count: int = Field(ge=0)
    min_retrieved_guidance_count: int = Field(ge=0)
    min_generated_guidance_count: int = Field(ge=0)
    min_grounded_partition_count: int = Field(ge=0)
    min_actionable_guidance_count: int = Field(ge=0)


class DocumentQualityGate(BaseModel):
    thresholds: DocumentQualityThresholds
    policy_version: str
    citation_coverage_pass: bool
    caution_note_count_pass: bool
    retrieved_guidance_pass: bool
    generated_guidance_pass: bool
    grounded_partition_pass: bool
    actionable_guidance_pass: bool
    all_passed: bool


class DocumentGroundedContextSections(BaseModel):
    validated_facts: list[DocumentValidatedFact]
    retrieved_writing_guidance: list[DocumentRetrievedGuidanceSnippet]
    generated_guidance: list[DocumentGeneratedGuidanceItem]
    limitations: list[str]


class DocumentFeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: str
    summary: str
    strengths: list[str]
    revision_priorities: list[str]
    caution_notes: list[str]
    citations: list[str]
    grounded_context: list[str]
    validated_facts: list[DocumentValidatedFact]
    retrieved_writing_guidance: list[DocumentRetrievedGuidanceSnippet]
    generated_guidance: list[DocumentGeneratedGuidanceItem]
    limitations: list[str]
    grounded_context_sections: DocumentGroundedContextSections
    quality_metrics: DocumentQualityMetrics
    quality_gate: DocumentQualityGate
    limitation_notice: str
    completed_at: datetime | None


class DocumentRecordSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    document_type: str
    input_method: str
    processing_status: str
    original_filename: str | None
    created_at: datetime
    updated_at: datetime
    latest_feedback_at: datetime | None
    scholarship_id: str | None = None
    scholarship_ids: list[str] | None = None


class DocumentDetailResponse(DocumentRecordSummary):
    content_text: str
    latest_feedback: DocumentFeedbackResponse | None = None


class DocumentListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[DocumentRecordSummary]
    total: int = Field(ge=0)


class DocumentSubmissionResponse(BaseModel):
    document: DocumentDetailResponse


class DocumentFeedbackRefreshResponse(BaseModel):
    document: DocumentDetailResponse


class DocumentSubmissionValidation(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    document_type: str
    content_text: str | None = Field(default=None, min_length=50, max_length=12000)
    scholarship_id: str | None = Field(default=None)
    scholarship_ids: list[str] = Field(default_factory=list, max_length=3)
    has_file: bool = False

    @model_validator(mode="after")
    def validate_input_mode(self) -> "DocumentSubmissionValidation":
        if not self.content_text and not self.has_file:
            raise ValueError("Provide document text or upload a supported file")
        if self.content_text and self.has_file:
            raise ValueError("Choose either pasted text or a supported file upload")
        if self.scholarship_id and self.scholarship_ids:
            raise ValueError("Provide either scholarship_id or scholarship_ids, not both")
        return self
