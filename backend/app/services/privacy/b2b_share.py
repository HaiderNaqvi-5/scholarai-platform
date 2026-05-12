"""B2B share service — the gatekeeper for university lead disclosure.

Critical rules (PRD §0.6 trust-boundary):
- Never share without explicit b2b_share_consent.
- Never share with an institution that has not signed a DPA.
- Snapshot the profile at share time so future profile changes don't
  retro-leak fresh data to past partners.
- Recommendation engine MUST NOT import from this module — keep B2B
  effects out of the matching graph.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.consent import latest_consent
from app.models import (
    ConsentAuditLog,
    Institution,
    StudentProfile,
    University,
    UniversityLead,
    User,
)


ALLOWED_SHARE_REASONS = {"match", "explicit_application", "paid_referral"}


class B2BShareService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def share_profile(
        self,
        *,
        target_user: User,
        university_id: uuid.UUID,
        share_reason: str,
        shared_with_email: str | None,
        institution_id: uuid.UUID | None = None,
    ) -> UniversityLead:
        if share_reason not in ALLOWED_SHARE_REASONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"share_reason must be one of {sorted(ALLOWED_SHARE_REASONS)}",
            )

        if not target_user.b2b_share_consent:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "b2b_share_consent_missing",
                    "message": (
                        "Target user has not granted b2b_share_consent. Profile cannot be shared."
                    ),
                },
            )

        # DPA enforcement: every receiving institution must have a signed DPA.
        if institution_id is not None:
            institution = await self.db.get(Institution, institution_id)
            if institution is None or institution.dpa_signed_at is None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": "institution_dpa_missing",
                        "message": "Receiving institution must sign a DPA before leads are shared.",
                    },
                )

        consent_row = await self._latest_b2b_consent_row(target_user.id)
        profile = await self._fetch_profile(target_user.id)
        snapshot = _profile_snapshot(target_user, profile)

        lead = UniversityLead(
            user_id=target_user.id,
            university_id=university_id,
            share_reason=share_reason,
            shared_with_email=shared_with_email,
            profile_snapshot=snapshot,
            consent_audit_log_id=consent_row.id if consent_row else None,
            shared_at=datetime.now(timezone.utc),
        )
        self.db.add(lead)
        await self.db.flush()
        await self.db.refresh(lead)
        return lead

    async def _fetch_profile(self, user_id: uuid.UUID) -> StudentProfile | None:
        result = await self.db.execute(
            select(StudentProfile).where(StudentProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def _latest_b2b_consent_row(self, user_id: uuid.UUID) -> ConsentAuditLog | None:
        result = await self.db.execute(
            select(ConsentAuditLog)
            .where(
                ConsentAuditLog.user_id == user_id,
                ConsentAuditLog.consent_type == "b2b_share",
                ConsentAuditLog.action == "grant",
            )
            .order_by(ConsentAuditLog.granted_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()


def _profile_snapshot(user: User, profile: StudentProfile | None) -> dict:
    snapshot = {
        "user_id": str(user.id),
        "snapshot_taken_at": datetime.now(timezone.utc).isoformat(),
        "email_redacted": _redact_email(user.email),
        "plan": user.plan,
        "billing_country": user.billing_country,
    }
    if profile is None:
        return snapshot
    snapshot.update(
        {
            "citizenship_country_code": profile.citizenship_country_code,
            "gpa_value": float(profile.gpa_value) if profile.gpa_value is not None else None,
            "ielts_score": float(profile.ielts_score) if profile.ielts_score is not None else None,
            "target_countries": list(profile.target_countries or []),
            "target_fields": list(profile.target_fields or []),
            "target_degree_level": profile.target_degree_level.value if profile.target_degree_level else None,
            "pakistani_university": profile.pakistani_university,
            "graduation_year": profile.graduation_year,
            "lead_score": profile.lead_score,
        }
    )
    return snapshot


def _redact_email(email: str | None) -> str | None:
    if not email or "@" not in email:
        return None
    local, _, domain = email.partition("@")
    if len(local) <= 2:
        prefix = local[0] if local else ""
    else:
        prefix = local[0] + "***" + local[-1]
    return f"{prefix}@{domain}"
