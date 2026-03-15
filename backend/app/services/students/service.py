import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DegreeLevel, StudentProfile
from app.schemas.students import StudentProfileUpsertRequest


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

        if profile is None:
            profile = StudentProfile(
                user_id=user_id,
                citizenship_country_code=values["citizenship_country_code"],
                gpa_value=values["gpa_value"],
                gpa_scale=values["gpa_scale"],
                target_field=values["target_field"],
                target_degree_level=DegreeLevel(values["target_degree_level"]),
                target_country_code=values["target_country_code"],
                language_test_type=values["language_test_type"],
                language_test_score=values["language_test_score"],
            )
            self.db.add(profile)
            await self.db.flush()
            await self.db.refresh(profile)
            return profile

        profile.citizenship_country_code = values["citizenship_country_code"]
        profile.gpa_value = values["gpa_value"]
        profile.gpa_scale = values["gpa_scale"]
        profile.target_field = values["target_field"]
        profile.target_degree_level = DegreeLevel(values["target_degree_level"])
        profile.target_country_code = values["target_country_code"]
        profile.language_test_type = values["language_test_type"]
        profile.language_test_score = values["language_test_score"]

        await self.db.flush()
        await self.db.refresh(profile)
        return profile
