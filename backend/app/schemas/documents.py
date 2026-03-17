from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


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
    has_file: bool = False

    @model_validator(mode="after")
    def validate_input_mode(self) -> "DocumentSubmissionValidation":
        if not self.content_text and not self.has_file:
            raise ValueError("Provide document text or upload a supported file")
        if self.content_text and self.has_file:
            raise ValueError("Choose either pasted text or a supported file upload")
        return self
