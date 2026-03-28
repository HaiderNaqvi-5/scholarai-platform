import re
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


_PASSWORD_SPECIAL_CHARS = r"!@#$%^&*()_+-=[]{}|;:,.<>?"


def _validate_password_strength(value: str) -> str:
    if len(value) < 12:
        raise ValueError("Password must be at least 12 characters long")
    if not re.search(r"[A-Z]", value):
        raise ValueError("Password must include at least one uppercase letter")
    if not re.search(r"[a-z]", value):
        raise ValueError("Password must include at least one lowercase letter")
    if not re.search(r"\d", value):
        raise ValueError("Password must include at least one number")
    if not re.search(f"[{re.escape(_PASSWORD_SPECIAL_CHARS)}]", value):
        raise ValueError(
            "Password must include at least one special character "
            f"({_PASSWORD_SPECIAL_CHARS})"
        )
    return value


class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(..., min_length=5, max_length=255, description="Unique email address for registration")
    password: str = Field(
        ...,
        min_length=12,
        max_length=128,
        description="Strong user password (min 12 chars, upper/lower/number/special required)",
    )
    full_name: str = Field(..., min_length=2, max_length=255, description="Full legal name of the user")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return _validate_password_strength(value)


class UserLogin(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(..., min_length=5, max_length=255, description="Registered email address")
    password: str = Field(..., min_length=8, max_length=128, description="User password")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="Unique user identifier (UUID)")
    email: str = Field(..., description="User's primary email address")
    full_name: str = Field(..., description="User's full name")
    role: str = Field(
        ...,
        description=(
            "Assigned role (legacy: student/admin/mentor; expanded: "
            "ENDUSER_STUDENT, INTERNAL_USER, DEV, ADMIN, UNIVERSITY, OWNER)"
        ),
    )
    is_active: bool = Field(..., description="Whether the account is enabled")


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field("bearer", description="Type of the token")
    expires_in: int = Field(..., description="Token expiry time in seconds")


class RefreshTokenRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    refresh_token: str = Field(..., min_length=16, description="Valid refresh token")


class LogoutResponse(BaseModel):
    message: str = Field(..., description="Logout result message")
