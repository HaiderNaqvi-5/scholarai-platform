"""Elite application strategy report (PRD §0.6).

Assembles a structured, PDF-ready report: profile summary, top-5 universities
classified Safety/Target/Reach, top-3 scholarship matches, and a 30/60/90-day
action plan. Persists the result as a DocumentRecord (type strategy_report).

Data sources are deliberately limited to: StudentProfile, the public
``universities`` table, and ScholarshipMatchService. No B2B tables — see the
package docstring. The frontend renders the JSON via print CSS; no server-side
PDF library is involved.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.plan_guard import assert_plan_or_raise
from app.models import (
    DocumentInputMethod,
    DocumentProcessingStatus,
    DocumentRecord,
    DocumentType,
    StudentProfile,
    University,
    User,
)
from app.schemas.reports import (
    ReportActionPlan,
    ReportProfileSummary,
    ReportScholarshipMatch,
    ReportUniversityMatch,
    StrategyReportRequest,
    StrategyReportResponse,
)
from app.schemas.scholarships_match import ScholarshipMatchRequest
from app.services.scholarships import ScholarshipMatchService, is_fully_funded
from app.services.students import StudentService
from app.utils.cgpa_converter import pakistani_to_uk_class, pakistani_to_us_gpa
from app.utils.profile_targets import resolve_target_countries


# Cap how many universities we score in Python. Beyond this the report would
# become noise anyway, and the scan should not be unbounded.
UNIVERSITY_SCAN_CAP = 50

# Public tier labels — keep in lockstep with `ReportUniversityMatch.tier`.
Tier = Literal["Safety", "Target", "Reach"]
_TIER_RANK: dict[Tier, int] = {"Safety": 0, "Target": 1, "Reach": 2}


logger = logging.getLogger(__name__)


LIMITATIONS_NOTE = (
    "This strategy report is AI-assisted and built from your saved profile. "
    "University tiers (Safety/Target/Reach) are estimates, not admission "
    "predictions. Verify every deadline and requirement on the official "
    "university and scholarship pages before acting."
)


class StrategyReportService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def generate(
        self, user: User, payload: StrategyReportRequest
    ) -> StrategyReportResponse:
        # Elite-exclusive (PRD §0.6). institution rank also passes.
        assert_plan_or_raise(
            user,
            "elite",
            "institution",
            message=(
                "The application strategy report is an Elite feature. Upgrade "
                "to generate your personalised 30/60/90-day plan."
            ),
        )

        profile = await StudentService(self.db).get_profile(user.id)
        profile_summary = self._build_profile_summary(user, profile)
        universities, scholarships = await asyncio.gather(
            self._match_universities(profile),
            self._match_scholarships(user, profile),
        )
        action_plan = self._build_action_plan(profile, universities, scholarships)
        generated_guidance = self._guidance(profile, universities, scholarships)

        document = DocumentRecord(
            user_id=user.id,
            title="Application Strategy Report",
            document_type=DocumentType.STRATEGY_REPORT,
            input_method=DocumentInputMethod.TEXT,
            content_text=json.dumps(
                {
                    "profile_summary": profile_summary.model_dump(mode="json"),
                    "universities": [u.model_dump(mode="json") for u in universities],
                    "scholarships": [s.model_dump(mode="json") for s in scholarships],
                    "action_plan": action_plan.model_dump(mode="json"),
                },
                default=str,
            ),
            processing_status=DocumentProcessingStatus.COMPLETED,
        )
        self.db.add(document)
        await self.db.flush()
        await self.db.refresh(document)

        return StrategyReportResponse(
            document_id=document.id,
            profile_summary=profile_summary,
            universities=universities,
            scholarships=scholarships,
            action_plan=action_plan,
            generated_guidance=generated_guidance,
            limitations=LIMITATIONS_NOTE,
            used_llm=False,
            created_at=document.created_at or datetime.now(timezone.utc),
        )

    # ------------------------------------------------------------------
    # Sections
    # ------------------------------------------------------------------

    def _build_profile_summary(
        self, user: User, profile: StudentProfile | None
    ) -> ReportProfileSummary:
        if profile is None:
            return ReportProfileSummary(
                full_name=user.full_name,
                pakistani_university=None,
                cgpa_value=None,
                cgpa_us_equivalent=None,
                uk_degree_class=None,
                ielts_score=None,
                target_degree=None,
                target_countries=[],
                target_fields=[],
                funding_requirement=None,
            )
        cgpa = float(profile.gpa_value) if profile.gpa_value is not None else None
        countries = resolve_target_countries(profile)
        fields = [f for f in (profile.target_fields or []) if f]
        if not fields and profile.target_field:
            fields = [profile.target_field]
        return ReportProfileSummary(
            full_name=user.full_name,
            pakistani_university=profile.pakistani_university,
            cgpa_value=cgpa,
            cgpa_us_equivalent=pakistani_to_us_gpa(cgpa),
            uk_degree_class=pakistani_to_uk_class(cgpa),
            ielts_score=float(profile.ielts_score)
            if profile.ielts_score is not None
            else None,
            target_degree=profile.target_degree_level.value
            if profile.target_degree_level
            else None,
            target_countries=countries,
            target_fields=fields,
            funding_requirement=profile.funding_requirement,
        )

    async def _match_universities(
        self, profile: StudentProfile | None
    ) -> list[ReportUniversityMatch]:
        countries = resolve_target_countries(profile)
        stmt = select(University).limit(UNIVERSITY_SCAN_CAP)
        if countries:
            stmt = stmt.where(University.country.in_(countries))
        rows = (await self.db.execute(stmt)).scalars().all()

        cgpa = (
            float(profile.gpa_value)
            if profile is not None and profile.gpa_value is not None
            else None
        )
        us_gpa = pakistani_to_us_gpa(cgpa)

        scored: list[ReportUniversityMatch] = []
        for uni in rows:
            tier, reason = _classify_university(uni, us_gpa)
            scored.append(
                ReportUniversityMatch(
                    university_id=uni.id,
                    name=uni.name,
                    country=uni.country,
                    tier=tier,
                    reason=reason,
                )
            )
        scored.sort(key=lambda m: _TIER_RANK[m.tier])
        return scored[:5]

    async def _match_scholarships(
        self, user: User, profile: StudentProfile | None
    ) -> list[ReportScholarshipMatch]:
        match_service = ScholarshipMatchService(self.db)
        # Strategy report needs bucket-level access (eligible / partial /
        # stretch) to surface a balanced shortlist, so we call the internal
        # bundle method — the public ``match()`` response strips internal
        # vocabulary (Task 7) and would no longer expose those buckets.
        # top_n=3 caps the full scoring pipeline so the report doesn't pay
        # the cost of building every bucket end-to-end.
        bundle = await match_service.match_internal(
            user, profile, ScholarshipMatchRequest(), top_n=3
        )
        cards = (bundle.eligible + bundle.partial + bundle.stretch)[:3]
        return [
            ReportScholarshipMatch(
                scholarship_id=c.scholarship_id,
                title=c.title,
                country_code=c.country_code,
                funding_type=c.funding_type,
                deadline_days=c.deadline_days,
                match_reason=c.match_reason,
            )
            for c in cards
        ]

    def _build_action_plan(
        self,
        profile: StudentProfile | None,
        universities: list[ReportUniversityMatch],
        scholarships: list[ReportScholarshipMatch],
    ) -> ReportActionPlan:
        next_30 = [
            "Finalise your university shortlist and confirm each program's exact "
            "deadline and entry requirements on the official site.",
            "Request academic transcripts and start HEC degree attestation — it "
            "is slow and blocks UK/Germany applications.",
        ]
        next_60 = [
            "Draft your SOP with the SOP builder and adapt it per university.",
            "Secure 2-3 letters of recommendation; brief each referee with your "
            "target programs.",
        ]
        next_90 = [
            "Submit applications, prioritising the soonest scholarship deadlines.",
            "Practise your visa interview for each target country once offers "
            "start arriving.",
        ]
        if profile is not None and profile.ielts_score is None:
            next_30.insert(
                0,
                "Book your IELTS test — most universities will not assess your "
                "application without a language score.",
            )
        urgent = [s for s in scholarships if s.deadline_days is not None and s.deadline_days <= 30]
        if urgent:
            titles = ", ".join(s.title for s in urgent)
            next_30.insert(0, f"Urgent: {titles} close within 30 days — apply now.")
        return ReportActionPlan(
            next_30_days=next_30,
            next_60_days=next_60,
            next_90_days=next_90,
        )

    def _guidance(
        self,
        profile: StudentProfile | None,
        universities: list[ReportUniversityMatch],
        scholarships: list[ReportScholarshipMatch],
    ) -> str:
        safety = sum(1 for u in universities if u.tier == "Safety")
        reach = sum(1 for u in universities if u.tier == "Reach")
        funded = sum(1 for s in scholarships if is_fully_funded(s.funding_type))
        return (
            f"Your shortlist has {safety} safety and {reach} reach options — a "
            f"balanced spread reduces the chance of zero offers. {funded} of your "
            "top scholarship matches are fully funded; lead with those, since "
            "funding decisions gate everything else for Pakistani applicants."
        )


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------


_SAFETY_MARGIN = 0.3   # US-eq GPA over min → safety
_TARGET_MARGIN = -0.1  # US-eq GPA within 0.1 of min → still a target


def _classify_university(uni: University, us_gpa: float | None) -> tuple[Tier, str]:
    """Return (tier, reason). Lower-ranked tier sorts first via _TIER_RANK."""
    min_cgpa = float(uni.min_cgpa) if uni.min_cgpa is not None else None
    if us_gpa is None or min_cgpa is None:
        return (
            "Target",
            "Add your CGPA to your profile for a precise Safety/Target/Reach tier.",
        )
    margin = us_gpa - min_cgpa
    if margin >= _SAFETY_MARGIN:
        return (
            "Safety",
            f"Your {us_gpa:g} US-equivalent GPA clears this program's "
            f"{min_cgpa:g} minimum comfortably.",
        )
    if margin >= _TARGET_MARGIN:
        return (
            "Target",
            f"Your {us_gpa:g} US-equivalent GPA is in range of the "
            f"{min_cgpa:g} minimum — a competitive but realistic application.",
        )
    return (
        "Reach",
        f"This program's {min_cgpa:g} minimum is above your {us_gpa:g} "
        "US-equivalent GPA — strengthen the rest of your application.",
    )
