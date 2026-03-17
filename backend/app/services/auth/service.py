from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models import User
from app.schemas import TokenResponse, UserCreate, UserLogin
from scholarai_common.errors import ScholarAIException, ErrorCode


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, payload: UserCreate) -> User | None:
        existing = await self.db.execute(select(User).where(User.email == payload.email))
        if existing.scalar_one_or_none():
            return None

        user = User(
            email=payload.email.lower(),
            password_hash=hash_password(payload.password),
            full_name=payload.full_name,
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def login(self, payload: UserLogin) -> TokenResponse:
        result = await self.db.execute(select(User).where(User.email == payload.email.lower()))
        user = result.scalar_one_or_none()

        if user is None or not verify_password(payload.password, user.password_hash):
            raise ScholarAIException(
                code=ErrorCode.AUTH_INVALID_CREDENTIALS,
                message="Invalid email or password",
                status_code=401
            )

        if not user.is_active:
            raise ScholarAIException(
                code=ErrorCode.AUTH_INACTIVE_ACCOUNT,
                message="Account is disabled",
                status_code=403
            )

        token_data = {"sub": str(user.id), "role": user.role.value}
        return TokenResponse(
            access_token=create_access_token(token_data),
            refresh_token=create_refresh_token(token_data),
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def refresh_session(self, refresh_token: str) -> TokenResponse:
        payload = decode_token(refresh_token, expected_type="refresh")
        user_id = payload.get("sub")
        if user_id is None:
            raise ScholarAIException(
                code=ErrorCode.AUTH_TOKEN_EXPIRED,
                message="Refresh token subject is missing",
                status_code=401
            )

        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            raise ScholarAIException(
                code=ErrorCode.NOT_FOUND,
                message="User not found",
                status_code=401
            )

        if not user.is_active:
            raise ScholarAIException(
                code=ErrorCode.AUTH_INACTIVE_ACCOUNT,
                message="Account is disabled",
                status_code=403
            )

        token_data = {"sub": str(user.id), "role": user.role.value}
        return TokenResponse(
            access_token=create_access_token(token_data),
            refresh_token=create_refresh_token(token_data),
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
