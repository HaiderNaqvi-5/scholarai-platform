from app.schemas.auth import TokenResponse, UserCreate, UserLogin, UserResponse
from app.schemas.health import ErrorEnvelope, HealthResponse
from app.schemas.recommendations import (
    RecommendationItem,
    RecommendationListResponse,
    RecommendationRequest,
)
from app.schemas.scholarships import ScholarshipDetailResponse, ScholarshipListItem
from app.schemas.students import StudentProfileResponse, StudentProfileUpsertRequest

__all__ = [
    "ErrorEnvelope",
    "HealthResponse",
    "RecommendationItem",
    "RecommendationListResponse",
    "RecommendationRequest",
    "ScholarshipDetailResponse",
    "ScholarshipListItem",
    "StudentProfileResponse",
    "StudentProfileUpsertRequest",
    "TokenResponse",
    "UserCreate",
    "UserLogin",
    "UserResponse",
]
