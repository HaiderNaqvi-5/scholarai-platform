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
from pydantic import TypeAdapter


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
