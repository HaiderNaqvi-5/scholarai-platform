from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import CurrentUser, SessionReadUser
from app.core.rate_limit import RateLimiter
from app.models import User
from app.schemas import (
    LogoutResponse,
    RefreshTokenRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from app.services.auth import AuthService

router = APIRouter()
_STRICT_RATE_LIMIT = settings.ENVIRONMENT.strip().lower() in {"production", "staging"}


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(
            RateLimiter(
                requests_limit=settings.AUTH_RATE_LIMIT_REGISTER_REQUESTS,
                window_seconds=settings.AUTH_RATE_LIMIT_WINDOW_SECONDS,
                fail_open=not _STRICT_RATE_LIMIT,
            )
        )
    ],
)
async def register(
    payload: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    service = AuthService(db)
    user = await service.register(payload)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )
    return user


@router.post(
    "/login",
    response_model=TokenResponse,
    dependencies=[
        Depends(
            RateLimiter(
                requests_limit=settings.AUTH_RATE_LIMIT_LOGIN_REQUESTS,
                window_seconds=settings.AUTH_RATE_LIMIT_WINDOW_SECONDS,
                fail_open=not _STRICT_RATE_LIMIT,
            )
        )
    ],
)
async def login(
    payload: UserLogin,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    service = AuthService(db)
    return await service.login(payload)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: SessionReadUser) -> User:
    return current_user


@router.post(
    "/refresh",
    response_model=TokenResponse,
    dependencies=[
        Depends(
            RateLimiter(
                requests_limit=settings.AUTH_RATE_LIMIT_REFRESH_REQUESTS,
                window_seconds=settings.AUTH_RATE_LIMIT_WINDOW_SECONDS,
                fail_open=not _STRICT_RATE_LIMIT,
            )
        )
    ],
)
async def refresh_session(
    payload: RefreshTokenRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    service = AuthService(db)
    return await service.refresh_session(payload.refresh_token)


@router.post(
    "/logout",
    response_model=LogoutResponse,
    dependencies=[
        Depends(
            RateLimiter(
                requests_limit=settings.AUTH_RATE_LIMIT_LOGOUT_REQUESTS,
                window_seconds=settings.AUTH_RATE_LIMIT_WINDOW_SECONDS,
                fail_open=not _STRICT_RATE_LIMIT,
            )
        )
    ],
)
async def logout(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LogoutResponse:
    service = AuthService(db)
    await service.logout(user=current_user)
    return LogoutResponse(message="Logged out successfully")
