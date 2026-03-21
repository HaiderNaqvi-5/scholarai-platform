"""
Shared FastAPI dependency injectors.

Usage:
    from app.core.dependencies import get_current_user, require_admin

Provides:
    - get_current_user   → returns authenticated User ORM object
    - require_admin      → additionally asserts role == "admin"
    - require_mentor     → additionally asserts role == "mentor"
    - get_audit_service  → optional helper to inject AuditLogService
"""
import uuid
import logging
from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

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
            required_fields = {"id", "email", "role", "is_active"}
            if not required_fields.issubset(user_data):
                raise ValueError(f"Cached user data missing fields: {required_fields - user_data.keys()}")
            cached_user = User(
                id=uuid.UUID(user_data["id"]),
                email=user_data["email"],
                role=UserRole(user_data["role"]),
                is_active=user_data["is_active"],
            )
            if not cached_user.is_active:
                logger.warning("get_current_user: cached user %s is inactive", user_id_raw)
                raise ScholarAIException(
                    code=ErrorCode.AUTH_INACTIVE_ACCOUNT,
                    message="Account is disabled",
                    status_code=status.HTTP_403_FORBIDDEN,
                )
            return cached_user
    except ScholarAIException:
        raise
    except Exception as exc:
        logger.debug("get_current_user: cache miss or error for %s — falling back to DB: %s", user_id_raw, exc)

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

    # Cache the user identity (minimal fields) for 5 minutes to reduce DB load
    try:
        minimal_user = {"id": str(user.id), "email": user.email, "role": user.role.value, "is_active": user.is_active}
        await redis_client.setex(cache_key, 300, json.dumps(minimal_user))
    except Exception:
        pass

    return user


# ── Role-based guards ─────────────────────────────────────────────────────────

async def require_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Assert that the authenticated user has the 'admin' role."""
    if current_user.role != UserRole.ADMIN:
        raise ScholarAIException(
            code=ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS,
            message="Admin privileges required",
            status_code=status.HTTP_403_FORBIDDEN
        )
    return current_user


async def require_student(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Assert that the authenticated user has the 'student' role."""
    if current_user.role != UserRole.STUDENT:
        raise ScholarAIException(
            code=ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS,
            message="Student role required",
            status_code=status.HTTP_403_FORBIDDEN
        )
    return current_user


async def require_mentor(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Assert that the authenticated user has the 'mentor' role."""
    if current_user.role != UserRole.MENTOR:
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
DBSession   = Annotated[AsyncSession, Depends(get_db)]
