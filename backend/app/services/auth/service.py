import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.authorization import get_role_capabilities
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models import Capability, InviteCode, RoleCapability, User, UserCapability
from app.schemas import TokenResponse, UserCreate, UserLogin
from scholarai_common.errors import ScholarAIException, ErrorCode


logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, payload: UserCreate) -> User | None:
        existing = await self.db.execute(select(User).where(User.email == payload.email))
        if existing.scalar_one_or_none():
            return None

        # Redeem invite code BEFORE creating the user so an invalid / expired
        # / exhausted code rejects the signup without leaving an orphan row.
        # ``_redeem_invite_code`` raises ScholarAIException on failure; on
        # success it returns the code row (with the redemption already
        # accounted for) so we can grant the plan + expiry at user creation.
        invite = await self._redeem_invite_code(
            getattr(payload, "invite_code", None)
        )

        user = User(
            email=payload.email.lower(),
            password_hash=hash_password(payload.password),
            full_name=payload.full_name,
        )
        if payload.billing_country:
            user.billing_country = payload.billing_country
        user.marketing_consent = bool(getattr(payload, "marketing_consent", False))

        # Optional Air University cohort capture — all three fields are
        # independent and skipped silently when not provided.
        if getattr(payload, "air_uni_uni", None):
            user.air_uni_uni = payload.air_uni_uni
        if getattr(payload, "air_uni_dept", None):
            user.air_uni_dept = payload.air_uni_dept
        if getattr(payload, "air_uni_batch", None):
            user.air_uni_batch = payload.air_uni_batch

        if invite is not None:
            user.plan = invite.grants_plan
            user.plan_activated_at = datetime.now(timezone.utc)
            user.plan_expires_at = datetime.now(timezone.utc) + timedelta(
                days=invite.trial_days
            )
            user.redeemed_invite_code = invite.code

        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        await self._record_signup_consent(user, payload)
        return user

    async def _redeem_invite_code(self, code: str | None) -> InviteCode | None:
        """Validate + atomically increment the invite code's ``uses`` counter.

        Returns ``None`` when no code was supplied. Raises ScholarAIException
        with a 400 status code (and a stable ``ErrorCode.VALIDATION_ERROR``)
        when the supplied code is invalid, inactive, outside its validity
        window, or exhausted. The increment is gated by a row-level lock
        (``with_for_update``) so two concurrent signups racing on the last
        slot cannot both succeed.
        """
        if not code:
            return None

        normalised = code.strip().upper()
        if not normalised:
            return None

        row_result = await self.db.execute(
            select(InviteCode).where(InviteCode.code == normalised).with_for_update()
        )
        row = row_result.scalar_one_or_none()
        if row is None:
            raise ScholarAIException(
                code=ErrorCode.VALIDATION_ERROR,
                message="Invite code is not recognised.",
                status_code=400,
            )
        if not row.is_active:
            raise ScholarAIException(
                code=ErrorCode.VALIDATION_ERROR,
                message="Invite code is no longer active.",
                status_code=400,
            )

        now = datetime.now(timezone.utc)
        if now < row.valid_from or now > row.valid_until:
            raise ScholarAIException(
                code=ErrorCode.VALIDATION_ERROR,
                message="Invite code is outside its valid window.",
                status_code=400,
            )
        if row.uses >= row.max_uses:
            raise ScholarAIException(
                code=ErrorCode.VALIDATION_ERROR,
                message="Invite code has reached its redemption limit.",
                status_code=400,
            )

        await self.db.execute(
            update(InviteCode)
            .where(InviteCode.code == normalised)
            .values(uses=InviteCode.uses + 1)
        )
        # Re-read so the returned row reflects the incremented counter.
        await self.db.refresh(row)
        return row

    async def _record_signup_consent(self, user: User, payload: UserCreate) -> None:
        """Persist initial terms + privacy consent if the signup payload carries
        versions. Late binding to avoid an import cycle with app.core.consent."""

        terms_version = getattr(payload, "terms_version", None)
        privacy_version = getattr(payload, "privacy_version", None)
        if not (terms_version and privacy_version and getattr(payload, "accepted", False)):
            return

        from app.core.consent import record_consent  # local import (cycle guard)

        for consent_type, version in (
            ("terms", terms_version),
            ("privacy", privacy_version),
        ):
            try:
                await record_consent(
                    self.db,
                    user,
                    consent_type=consent_type,
                    version=version,
                    granted=True,
                )
            except Exception:
                # Consent capture is best-effort at signup; the gated routes
                # will re-prompt if the audit row is missing.
                continue

        if getattr(payload, "marketing_consent", False):
            try:
                await record_consent(
                    self.db,
                    user,
                    consent_type="marketing",
                    version="1.0",
                    granted=True,
                )
            except Exception:
                pass

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

        capabilities = await self._resolve_capabilities(user)
        token_data = {
            "sub": str(user.id),
            "role": user.role.value,
            "capabilities": capabilities,
            "policy_version": "rbac.v1",
            "institution_scope": str(user.institution_id) if user.institution_id else None,
            "token_version": user.auth_token_version,
        }
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
        token_version = payload.get("token_version")
        if token_version is None or token_version != user.auth_token_version:
            raise ScholarAIException(
                code=ErrorCode.AUTH_TOKEN_EXPIRED,
                message="Refresh token is no longer valid",
                status_code=401,
            )

        capabilities = await self._resolve_capabilities(user)
        token_data = {
            "sub": str(user.id),
            "role": user.role.value,
            "capabilities": capabilities,
            "policy_version": "rbac.v1",
            "institution_scope": str(user.institution_id) if user.institution_id else None,
            "token_version": user.auth_token_version,
        }
        return TokenResponse(
            access_token=create_access_token(token_data),
            refresh_token=create_refresh_token(token_data),
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def logout(self, *, user: User) -> None:
        user.auth_token_version += 1
        await self.db.flush()

    async def _resolve_capabilities(self, user: User) -> list[str]:
        role_result = await self.db.execute(
            select(Capability.capability_key)
            .join(RoleCapability, RoleCapability.capability_id == Capability.id)
            .where(RoleCapability.role == user.role)
            .where(Capability.is_active.is_(True))
        )
        db_role_capabilities = {row[0] for row in role_result.all()}
        role_capabilities = db_role_capabilities or set(get_role_capabilities(user.role))
        now_utc = datetime.now(timezone.utc)
        result = await self.db.execute(
            select(Capability.capability_key)
            .join(UserCapability, UserCapability.capability_id == Capability.id)
            .where(UserCapability.user_id == user.id)
            .where(Capability.is_active.is_(True))
            .where(
                (UserCapability.expires_at.is_(None))
                | (UserCapability.expires_at > now_utc)
            )
        )
        user_capabilities = {row[0] for row in result.all()}
        return sorted(role_capabilities | user_capabilities)
