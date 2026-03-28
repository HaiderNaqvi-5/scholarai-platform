import uuid
from typing import Annotated
import logging

from fastapi import Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.authorization import Capability, get_role_capabilities
from app.core.database import get_db
from app.core.security import decode_token, oauth2_scheme
from app.models import User, UserRole
from scholarai_common.errors import ScholarAIException, ErrorCode
from app.core.rate_limit import redis_client
import json


logger = logging.getLogger(__name__)


# ── Current user ─────────────────────────────────────────────────────────────

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Decode Bearer token and return the matching User row with Redis caching."""
    payload = decode_token(token, expected_type="access")

    user_id_raw = payload.get("sub")
    if user_id_raw is None:
        raise ScholarAIException(
            code=ErrorCode.AUTH_TOKEN_EXPIRED,
            message="Token payload missing subject",
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    cache_key = f"user_session:{user_id_raw}"
    try:
        cached_user_json = await redis_client.get(cache_key)
        if cached_user_json:
            user_data = json.loads(cached_user_json)
            # Create a mock-like object that behaves like a User model for the auth guards
            # In a full-blown system, you might use a Pydantic model here.
            # For now, we'll re-verify against DB if not found or corrupted.
            pass
    except Exception:
        pass # Fallback to DB if Redis is down

    try:
        user_id = uuid.UUID(str(user_id_raw))
    except ValueError:
        raise ScholarAIException(
            code=ErrorCode.AUTH_TOKEN_EXPIRED,
            message="Invalid user identifier in token",
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise ScholarAIException(
            code=ErrorCode.NOT_FOUND,
            message="User not found",
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    if not user.is_active:
        raise ScholarAIException(
            code=ErrorCode.AUTH_INACTIVE_ACCOUNT,
            message="Account is disabled",
            status_code=status.HTTP_403_FORBIDDEN
        )
    token_version = payload.get("token_version")
    if token_version is None or token_version != user.auth_token_version:
        raise ScholarAIException(
            code=ErrorCode.AUTH_TOKEN_EXPIRED,
            message="Session token is no longer valid",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    token_capabilities_raw = payload.get("capabilities")
    token_capabilities: set[str] = set()
    if token_capabilities_raw is not None:
        if not isinstance(token_capabilities_raw, list):
            raise ScholarAIException(
                code=ErrorCode.AUTH_TOKEN_EXPIRED,
                message="Token capabilities claim must be an array",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        non_string_entries = [cap for cap in token_capabilities_raw if not isinstance(cap, str)]
        if non_string_entries:
            raise ScholarAIException(
                code=ErrorCode.AUTH_TOKEN_EXPIRED,
                message="Token capabilities entries must be strings",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        token_capabilities = {cap for cap in token_capabilities_raw if cap}
    token_policy_version = payload.get("policy_version")
    token_institution_scope = payload.get("institution_scope")

    if token_institution_scope is not None:
        user_scope = str(user.institution_id) if user.institution_id else None
        if user_scope != str(token_institution_scope):
            raise ScholarAIException(
                code=ErrorCode.AUTH_SCOPE_FORBIDDEN,
                message="Institution scope mismatch",
                status_code=status.HTTP_403_FORBIDDEN,
            )

    if user.role == UserRole.UNIVERSITY:
        if user.institution_id is None:
            raise ScholarAIException(
                code=ErrorCode.AUTH_SCOPE_FORBIDDEN,
                message="University access requires institution scope",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        if token_institution_scope is None:
            raise ScholarAIException(
                code=ErrorCode.AUTH_SCOPE_FORBIDDEN,
                message="University token requires institution scope claim",
                status_code=status.HTTP_403_FORBIDDEN,
            )

    setattr(user, "_token_capabilities", token_capabilities)
    setattr(user, "_token_policy_version", token_policy_version)
    setattr(user, "_token_institution_scope", token_institution_scope)

    # Cache the user identity (minimal fields) for 5 minutes to reduce DB load
    try:
        minimal_user = {"id": str(user.id), "email": user.email, "role": user.role.value, "is_active": user.is_active}
        await redis_client.setex(cache_key, 300, json.dumps(minimal_user))
    except Exception:
        pass

    return user


def _has_capability(current_user: User, capability: Capability | str) -> bool:
    normalized = capability.value if isinstance(capability, Capability) else capability
    token_capabilities = getattr(current_user, "_token_capabilities", None)
    if isinstance(token_capabilities, set) and token_capabilities:
        return normalized in token_capabilities

    logger.warning(
        "Capability fallback to role map for user %s role %s",
        str(current_user.id),
        current_user.role.value,
    )
    return normalized in get_role_capabilities(current_user.role)


def require_capability(capability: Capability | str):
    async def _dependency(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if not _has_capability(current_user, capability):
            capability_key = capability.value if isinstance(capability, Capability) else capability
            raise ScholarAIException(
                code=ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS,
                message=f"Missing capability: {capability_key}",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        return current_user

    return _dependency


def require_any_capability(*capabilities: Capability | str):
    async def _dependency(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if any(_has_capability(current_user, capability) for capability in capabilities):
            return current_user

        capability_keys = [cap.value if isinstance(cap, Capability) else cap for cap in capabilities]
        raise ScholarAIException(
            code=ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS,
            message=f"At least one capability required: {', '.join(capability_keys)}",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    return _dependency


# ── Compatibility role-based wrappers (capability-backed) ───────────────────

async def require_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Compatibility wrapper for admin-like internal access."""
    if current_user.role not in {UserRole.ADMIN, UserRole.OWNER, UserRole.DEV}:
        raise ScholarAIException(
            code=ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS,
            message="Admin privileges required",
            status_code=status.HTTP_403_FORBIDDEN
        )
    return current_user


async def require_student(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Compatibility wrapper for student self-service access."""
    if current_user.role not in {UserRole.STUDENT, UserRole.ENDUSER_STUDENT}:
        raise ScholarAIException(
            code=ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS,
            message="Student role required",
            status_code=status.HTTP_403_FORBIDDEN
        )
    return current_user


async def require_mentor(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Compatibility wrapper for mentor/internal review access."""
    if current_user.role not in {
        UserRole.MENTOR,
        UserRole.INTERNAL_USER,
        UserRole.DEV,
        UserRole.ADMIN,
        UserRole.OWNER,
    }:
        raise ScholarAIException(
            code=ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS,
            message="Mentor privileges required",
            status_code=status.HTTP_403_FORBIDDEN
        )
    return current_user


# ── Convenience type aliases (use in route signatures) ────────────────────────

CurrentUser = Annotated[User, Depends(get_current_user)]
AdminUser   = Annotated[User, Depends(require_admin)]
StudentUser = Annotated[User, Depends(require_student)]
MentorUser  = Annotated[User, Depends(require_mentor)]
SessionReadUser = Annotated[User, Depends(require_capability(Capability.AUTH_SESSION_READ))]

ProfileReadUser = Annotated[User, Depends(require_capability(Capability.PROFILE_SELF_READ))]
ProfileWriteUser = Annotated[User, Depends(require_capability(Capability.PROFILE_SELF_WRITE))]

SavedOpportunityReadUser = Annotated[
    User, Depends(require_capability(Capability.SAVED_OPPORTUNITY_SELF_READ))
]
SavedOpportunityWriteUser = Annotated[
    User, Depends(require_capability(Capability.SAVED_OPPORTUNITY_SELF_WRITE))
]

RecommendationUser = Annotated[
    User, Depends(require_capability(Capability.RECOMMENDATION_SELF_GENERATE))
]
RecommendationEvaluationUser = Annotated[
    User,
    Depends(
        require_any_capability(
            Capability.RECOMMENDATION_EVALUATE,
            Capability.ADMIN_AUDIT_READ,
            Capability.OWNER_SYSTEM_READ,
        )
    ),
]

DocumentReadUser = Annotated[User, Depends(require_capability(Capability.DOCUMENT_SELF_READ))]
DocumentCreateUser = Annotated[User, Depends(require_capability(Capability.DOCUMENT_SELF_CREATE))]
DocumentFeedbackUser = Annotated[User, Depends(require_capability(Capability.DOCUMENT_SELF_FEEDBACK))]

InterviewCreateUser = Annotated[User, Depends(require_capability(Capability.INTERVIEW_SELF_CREATE))]
InterviewReadUser = Annotated[User, Depends(require_capability(Capability.INTERVIEW_SELF_READ))]
InterviewRespondUser = Annotated[User, Depends(require_capability(Capability.INTERVIEW_SELF_RESPOND))]

CurationQueueUser = Annotated[User, Depends(require_capability(Capability.CURATION_QUEUE_READ))]
CurationValidateUser = Annotated[
    User,
    Depends(
        require_any_capability(
            Capability.CURATION_RECORD_VALIDATE,
            Capability.CURATION_RECORD_PUBLISH,
        )
    ),
]
IngestionRunUser = Annotated[User, Depends(require_capability(Capability.ADMIN_INGESTION_RUN))]
AdminAuditUser = Annotated[
    User,
    Depends(require_any_capability(Capability.ADMIN_AUDIT_READ, Capability.OWNER_SYSTEM_READ)),
]

MentorReviewUser = Annotated[
    User,
    Depends(require_any_capability(Capability.DOCUMENT_MENTOR_REVIEW, Capability.DOCUMENT_MENTOR_SUBMIT)),
]

DBSession   = Annotated[AsyncSession, Depends(get_db)]
