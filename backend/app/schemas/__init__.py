from app.schemas.auth import TokenResponse, UserCreate, UserLogin, UserResponse
from app.schemas.documents import (
    DocumentDetailResponse,
    DocumentFeedbackRefreshResponse,
    DocumentFeedbackResponse,
    DocumentListResponse,
    DocumentRecordSummary,
    DocumentSubmissionResponse,
)
from app.schemas.health import ErrorEnvelope, HealthResponse
from app.schemas.recommendations import (
    RecommendationItem,
    RecommendationListResponse,
    RecommendationRequest,
)
from app.schemas.saved_opportunities import (
    SavedOpportunityItem,
    SavedOpportunityListResponse,
)
from app.schemas.scholarships import ScholarshipDetailResponse, ScholarshipListItem
from app.schemas.students import StudentProfileResponse, StudentProfileUpsertRequest

__all__ = [
    "DocumentDetailResponse",
    "DocumentFeedbackRefreshResponse",
    "DocumentFeedbackResponse",
    "DocumentListResponse",
    "DocumentRecordSummary",
    "DocumentSubmissionResponse",
    "ErrorEnvelope",
    "HealthResponse",
    "RecommendationItem",
    "RecommendationListResponse",
    "RecommendationRequest",
    "SavedOpportunityItem",
    "SavedOpportunityListResponse",
    "ScholarshipDetailResponse",
    "ScholarshipListItem",
    "StudentProfileResponse",
    "StudentProfileUpsertRequest",
    "TokenResponse",
    "UserCreate",
    "UserLogin",
    "UserResponse",
]
