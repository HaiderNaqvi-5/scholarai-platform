"""Schemas for /waitlist + /upgrade pricing (Feature 10)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


_ALLOWED_PLANS = {"pro", "elite", "institution"}
_ALLOWED_CURRENCIES = {"PKR", "GBP", "EUR", "AED", "USD"}


class WaitlistJoinRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str = Field(min_length=5, max_length=255)
    plan: str = Field(default="pro", max_length=16)
    currency: str = Field(default="PKR", max_length=8)
    country: str | None = Field(default=None, min_length=2, max_length=2)

    @field_validator("email")
    @classmethod
    def normalise_email(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("plan")
    @classmethod
    def plan_allowed(cls, value: str) -> str:
        v = value.strip().lower()
        if v not in _ALLOWED_PLANS:
            raise ValueError("plan must be one of pro, elite, institution")
        return v

    @field_validator("currency")
    @classmethod
    def currency_allowed(cls, value: str) -> str:
        v = value.strip().upper()
        if v not in _ALLOWED_CURRENCIES:
            raise ValueError("currency must be PKR / GBP / EUR / AED / USD")
        return v

    @field_validator("country")
    @classmethod
    def upper_country(cls, value: str | None) -> str | None:
        return value.upper() if value else value


class WaitlistJoinResponse(BaseModel):
    id: UUID
    email: str
    plan: str
    currency: str
    created_at: datetime


class PricingTier(BaseModel):
    key: str
    label: str
    is_recommended: bool
    monthly_price: str
    yearly_hint: str | None
    feature_summary: str
    bullet_features: list[str]


class PricingResponse(BaseModel):
    currency: str
    tiers: list[PricingTier]
