"""Pakistan demo seed orchestrator (Feature 10, PRD §10).

Idempotent. Runs all upstream seeds, creates the Zara Khan demo student
with plan=elite, plants three placeholder waitlist rows, and grants the
demo account every required consent so the gated routes work.

Usage:
    cd backend && python scripts/demo_seed_pakistan.py
"""

from __future__ import annotations

import asyncio
import logging
import sys
from datetime import date, datetime, timezone
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import select  # noqa: E402

from app.core.consent import record_consent  # noqa: E402
from app.core.database import async_session_factory  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.demo.pakistan_dataset import (  # noqa: E402
    PAKISTAN_SCHOLARSHIP_SEED,
    PAKISTAN_SOURCE_REGISTRY_SEED,
)
from app.demo.pakistan_universities import UNIVERSITIES_SEED  # noqa: E402
from app.demo.visa_questions import VISA_INTERVIEW_QUESTION_BANK  # noqa: E402
from app.demo.legal_documents import LEGAL_DOCUMENTS_V1  # noqa: E402
from app.models import (  # noqa: E402
    DegreeLevel,
    StudentProfile,
    User,
    UserRole,
    University,
    VisaInterviewQuestion,
    Waitlist,
)
from scripts.seed_legal_documents import _seed as seed_legal_documents_impl  # noqa: E402
from scripts.seed_pakistan_scholarships import (  # noqa: E402
    _upsert_sources,
    _upsert_scholarship,
)
from scripts.seed_visa_interview_questions import _seed as seed_visa_questions_impl  # noqa: E402


logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger("demo_seed_pakistan")


DEMO_EMAIL = "zara.khan@example.com"
DEMO_PASSWORD = "ScholarAI-Demo-2026!"
DEMO_FULL_NAME = "Zara Khan"


async def _seed_universities() -> int:
    async with async_session_factory() as session:
        count = 0
        for payload in UNIVERSITIES_SEED:
            result = await session.execute(
                select(University).where(
                    University.name == payload["name"],
                    University.country == payload["country"],
                )
            )
            uni = result.scalar_one_or_none()
            if uni is None:
                uni = University(name=payload["name"], country=payload["country"])
                session.add(uni)
            for key, value in payload.items():
                setattr(uni, key, value)
            count += 1
        await session.commit()
        return count


async def _seed_pakistan_scholarships() -> int:
    async with async_session_factory() as session:
        sources = await _upsert_sources(session)
        count = 0
        for payload in PAKISTAN_SCHOLARSHIP_SEED:
            await _upsert_scholarship(session, payload, sources)
            count += 1
        await session.commit()
        return count


async def _create_demo_student() -> None:
    async with async_session_factory() as session:
        result = await session.execute(select(User).where(User.email == DEMO_EMAIL))
        user = result.scalar_one_or_none()
        if user is None:
            user = User(
                email=DEMO_EMAIL,
                password_hash=hash_password(DEMO_PASSWORD),
                full_name=DEMO_FULL_NAME,
                role=UserRole.STUDENT,
            )
            session.add(user)
        else:
            user.password_hash = hash_password(DEMO_PASSWORD)
            user.full_name = DEMO_FULL_NAME

        user.plan = "elite"
        user.plan_currency = "PKR"
        user.billing_country = "PK"
        user.plan_activated_at = datetime.now(timezone.utc)
        user.plan_expires_at = datetime(2099, 12, 31, tzinfo=timezone.utc)
        user.marketing_consent = True
        user.b2b_share_consent = True
        user.b2b_share_consent_at = datetime.now(timezone.utc)
        user.is_active = True

        await session.flush()
        await session.refresh(user)

        # Demo profile
        result = await session.execute(
            select(StudentProfile).where(StudentProfile.user_id == user.id)
        )
        profile = result.scalar_one_or_none()
        if profile is None:
            profile = StudentProfile(
                user_id=user.id,
                citizenship_country_code="PK",
                target_field="Computer Science",
                target_country_code="GB",
            )
            session.add(profile)
        profile.gpa_value = 3.7
        profile.gpa_scale = 4.0
        profile.target_degree_level = DegreeLevel.MS
        profile.target_countries = ["GB", "DE"]
        profile.target_fields = ["cs", "ds_ai"]
        profile.target_field = "Computer Science"
        profile.target_country_code = "GB"
        profile.language_test_type = "IELTS"
        profile.language_test_score = 7.0
        profile.ielts_score = 7.0
        profile.hec_degree_level = "bachelor"
        profile.pakistani_university = "NUST"
        profile.cgpa_scale_choice = "4.0"
        profile.degree_subject = "Computer Science"
        profile.graduation_year = 2024
        profile.has_research_publications = True
        profile.research_publication_count = 1
        profile.funding_requirement = "fully_funded_only"
        profile.intake_target = "sep_2026"
        profile.city_of_origin = "Islamabad"
        profile.can_afford_application_fees = False
        profile.needs_gre_waiver = True
        profile.family_has_funds_for_bank_statement = True
        profile.years_work_experience = 1
        profile.referral_source = "youtube"

        await session.flush()

        # Grant every consent so the gated routes work without prompting.
        for consent_type in ("terms", "privacy", "marketing", "b2b_share", "cookies"):
            await record_consent(
                session,
                user,
                consent_type=consent_type,
                version="1.0",
                granted=True,
            )

        await session.commit()


async def _seed_waitlist_placeholders() -> int:
    placeholders = [
        ("ali.hassan+demo@example.com", "pro", "PKR", "PK"),
        ("usman.malik+demo@example.com", "elite", "GBP", "GB"),
        ("nust.career.center+demo@example.com", "institution", "PKR", "PK"),
    ]
    async with async_session_factory() as session:
        count = 0
        for email, plan, currency, country in placeholders:
            result = await session.execute(select(Waitlist).where(Waitlist.email == email))
            row = result.scalar_one_or_none()
            if row is None:
                row = Waitlist(email=email)
                session.add(row)
            row.plan = plan
            row.currency = currency
            row.country = country
            count += 1
        await session.commit()
        return count


async def _run() -> dict:
    legal = await seed_legal_documents_impl()
    scholarships = await _seed_pakistan_scholarships()
    universities = await _seed_universities()
    visa_questions = await seed_visa_questions_impl()
    await _create_demo_student()
    waitlist = await _seed_waitlist_placeholders()
    return {
        "legal_documents": legal,
        "pakistan_scholarships": scholarships,
        "universities": universities,
        "visa_questions": visa_questions,
        "waitlist_placeholders": waitlist,
        "demo_email": DEMO_EMAIL,
        "demo_password": DEMO_PASSWORD,
    }


def main() -> int:
    summary = asyncio.run(_run())
    logger.info("Pakistan demo seed complete: %s", summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
