"""
Pydantic v2 schemas for ScholarAI.
Organised by domain: User/Auth, StudentProfile, Scholarship, Application, MatchScore.
"""
import uuid
from datetime import datetime, date
from typing import Optional, List, Any

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


# ─────────────────────────────────────────────
#  Common
# ─────────────────────────────────────────────

class PaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[Any]


# ─────────────────────────────────────────────
#  Auth / User
# ─────────────────────────────────────────────

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=255)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    avatar_url: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshRequest(BaseModel):
    refresh_token: str


# ─────────────────────────────────────────────
#  Student Profile
# ─────────────────────────────────────────────

class StudentProfileCreate(BaseModel):
    gpa: Optional[float] = Field(None, ge=0, le=4.0)
    gpa_scale: float = Field(4.0, ge=1.0, le=10.0)
    field_of_study: str = Field(..., min_length=2, max_length=255)
    degree_level: str = Field(..., pattern="^(bachelor|master|phd)$")
    university: Optional[str] = Field(None, max_length=255)
    country_of_origin: Optional[str] = Field(None, max_length=100)
    target_countries: Optional[List[str]] = None
    citizenship: Optional[str] = Field(None, max_length=100)
    research_publications: int = Field(0, ge=0)
    research_experience_months: int = Field(0, ge=0)
    leadership_roles: int = Field(0, ge=0)
    volunteer_hours: int = Field(0, ge=0)
    language_test_type: Optional[str] = None
    language_test_score: Optional[float] = None
    extracurricular_summary: Optional[str] = None
    sop_draft: Optional[str] = None

    @field_validator("gpa")
    @classmethod
    def validate_gpa(cls, v, values):
        return v  # GPA validation relative to scale is done at service layer


class StudentProfileUpdate(StudentProfileCreate):
    field_of_study: Optional[str] = None
    degree_level: Optional[str] = None


class StudentProfileResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    gpa: Optional[float] = None
    gpa_scale: float
    field_of_study: str
    degree_level: str
    university: Optional[str] = None
    country_of_origin: Optional[str] = None
    target_countries: Optional[List[str]] = None
    citizenship: Optional[str] = None
    research_publications: int
    research_experience_months: int
    leadership_roles: int
    volunteer_hours: int
    language_test_type: Optional[str] = None
    language_test_score: Optional[float] = None
    extracurricular_summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
#  Scholarship
# ─────────────────────────────────────────────

class EligibilityRequirementResponse(BaseModel):
    id: uuid.UUID
    requirement_type: str
    operator: Optional[str] = None
    value: str

    model_config = {"from_attributes": True}


class ScholarshipResponse(BaseModel):
    id: uuid.UUID
    name: str
    provider: Optional[str] = None
    country: str
    university: Optional[str] = None
    field_of_study: Optional[List[str]] = None
    degree_levels: Optional[List[str]] = None
    min_gpa: Optional[float] = None
    funding_type: Optional[str] = None
    funding_amount_usd: Optional[float] = None
    deadline: Optional[date] = None
    description: Optional[str] = None
    simplified_description: Optional[str] = None
    source_url: str
    is_active: bool
    eligibility_requirements: List[EligibilityRequirementResponse] = []

    model_config = {"from_attributes": True}


class ScholarshipListItem(BaseModel):
    id: uuid.UUID
    name: str
    provider: Optional[str] = None
    country: str
    funding_type: Optional[str] = None
    funding_amount_usd: Optional[float] = None
    deadline: Optional[date] = None
    is_active: bool
    ai_match_score: Optional[float] = None   # injected by recommender
    success_probability: Optional[float] = None

    model_config = {"from_attributes": True}


class ScholarshipSearchParams(BaseModel):
    q: Optional[str] = None
    country: Optional[str] = None
    degree_level: Optional[str] = None
    field_of_study: Optional[str] = None
    min_funding_usd: Optional[float] = None
    max_deadline_days: Optional[int] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


# ─────────────────────────────────────────────
#  Application
# ─────────────────────────────────────────────

class ApplicationCreate(BaseModel):
    scholarship_id: uuid.UUID


class ApplicationResponse(BaseModel):
    id: uuid.UUID
    student_id: uuid.UUID
    scholarship_id: uuid.UUID
    status: str
    ai_match_score: Optional[float] = None
    success_probability: Optional[float] = None
    shap_explanation: Optional[dict] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ApplicationStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(draft|submitted|under_review|accepted|rejected)$")


# ─────────────────────────────────────────────
#  Match / Recommendation
# ─────────────────────────────────────────────

class MatchScoreResponse(BaseModel):
    scholarship: ScholarshipListItem
    overall_score: float
    success_probability: Optional[float] = None
    vector_similarity: Optional[float] = None
    feature_contributions: Optional[dict] = None

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
#  Interview
# ─────────────────────────────────────────────

class InterviewStartRequest(BaseModel):
    scholarship_id: Optional[uuid.UUID] = None
    num_questions: int = Field(5, ge=1, le=10)
    input_mode: str = Field("text", pattern="^(text|voice)$")


class InterviewAnswerRequest(BaseModel):
    session_id: uuid.UUID
    question_index: int
    answer_text: Optional[str] = None
    audio_base64: Optional[str] = None  # for voice mode


class InterviewFeedbackItem(BaseModel):
    question: str
    answer: str
    feedback: str
    score: float


class InterviewSessionResponse(BaseModel):
    id: uuid.UUID
    scholarship_id: Optional[uuid.UUID] = None
    questions: Optional[List[dict]] = None
    feedback: Optional[dict] = None
    overall_score: Optional[float] = None
    duration_seconds: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
#  SOP Assistant
# ─────────────────────────────────────────────

class SopGenerateRequest(BaseModel):
    scholarship_id: uuid.UUID
    additional_context: Optional[str] = None


class SopImproveRequest(BaseModel):
    current_sop: str = Field(..., min_length=100)
    feedback_focus: Optional[str] = None  # "clarity" | "structure" | "relevance"


class SopResponse(BaseModel):
    generated_text: str
    word_count: int
    suggestions: Optional[List[str]] = None


# ─────────────────────────────────────────────
#  Admin
# ─────────────────────────────────────────────

class AdminScholarshipCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=500)
    provider: Optional[str] = None
    country: str = Field(..., min_length=2, max_length=100)
    university: Optional[str] = None
    field_of_study: Optional[List[str]] = None
    degree_levels: Optional[List[str]] = None
    min_gpa: Optional[float] = Field(None, ge=0, le=4.0)
    funding_type: Optional[str] = None
    funding_amount_usd: Optional[float] = Field(None, ge=0)
    deadline: Optional[date] = None
    description: Optional[str] = None
    source_url: str
    source_name: Optional[str] = None


class AdminScholarshipUpdate(AdminScholarshipCreate):
    name: Optional[str] = None
    country: Optional[str] = None
    source_url: Optional[str] = None


class ScraperRunResponse(BaseModel):
    id: uuid.UUID
    source_name: str
    source_url: str
    status: str
    scholarships_found: int
    scholarships_new: int
    scholarships_updated: int
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AuditLogResponse(BaseModel):
    id: uuid.UUID
    admin_id: Optional[uuid.UUID] = None
    action: str
    target_table: Optional[str] = None
    target_id: Optional[str] = None
    old_value: Optional[dict] = None
    new_value: Optional[dict] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
#  Document Upload
# ─────────────────────────────────────────────

class DocumentResponse(BaseModel):
    id: uuid.UUID
    student_id: uuid.UUID
    document_type: str
    storage_url: Optional[str] = None
    file_size_bytes: Optional[int] = None
    uploaded_at: datetime

    model_config = {"from_attributes": True}
