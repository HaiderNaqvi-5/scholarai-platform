import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DegreeLevel, StudentProfile
from app.schemas.students import StudentProfileUpsertRequest


_PROFILE_SIMPLE_FIELDS = (
    "citizenship_country_code",
    "gpa_value",
    "gpa_scale",
    "target_field",
    "target_country_code",
    "target_countries",
    "target_fields",
    "language_test_type",
    "language_test_score",
    "hec_degree_level",
    "pakistani_university",
    "cgpa_scale_choice",
    "degree_subject",
    "graduation_year",
    "ielts_score",
    "toefl_score",
    "gre_quant",
    "gre_verbal",
    "has_research_publications",
    "research_publication_count",
    "funding_requirement",
    "intake_target",
    "city_of_origin",
    "can_afford_application_fees",
    "needs_gre_waiver",
    "family_has_funds_for_bank_statement",
)


class StudentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_profile(self, user_id: uuid.UUID) -> StudentProfile | None:
        result = await self.db.execute(
            select(StudentProfile).where(StudentProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def upsert_profile(
        self,
        user_id: uuid.UUID,
        payload: StudentProfileUpsertRequest,
    ) -> StudentProfile:
        profile = await self.get_profile(user_id)
        values = payload.model_dump()
        values["target_degree_level"] = DegreeLevel(values["target_degree_level"])

        if profile is None:
            profile = StudentProfile(user_id=user_id, **{
                "target_degree_level": values["target_degree_level"],
                **{k: values[k] for k in _PROFILE_SIMPLE_FIELDS},
            })
            self.db.add(profile)
            await self.db.flush()
            await self.db.refresh(profile)
            return profile

        for field in _PROFILE_SIMPLE_FIELDS:
            setattr(profile, field, values[field])
        profile.target_degree_level = values["target_degree_level"]

        await self.db.flush()
        await self.db.refresh(profile)
        return profile
