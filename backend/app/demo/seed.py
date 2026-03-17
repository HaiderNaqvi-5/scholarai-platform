import logging
from collections.abc import Iterable

from sqlalchemy import inspect, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.database import async_session_factory
from app.core.security import hash_password
from app.demo.demo_dataset import SCHOLARSHIP_SEED, SOURCE_REGISTRY_SEED
from app.models import Scholarship, ScholarshipRequirement, SourceRegistry, User, UserRole

logger = logging.getLogger(__name__)

REQUIRED_TABLES = {"users", "source_registry", "scholarships", "scholarship_requirements"}


class DemoSeedService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def ensure_seeded(self) -> tuple[int, int]:
        await self._upsert_demo_users()
        source_map = await self._upsert_sources()
        scholarship_count = 0
        for scholarship_payload in SCHOLARSHIP_SEED:
            await self._upsert_scholarship(scholarship_payload, source_map)
            scholarship_count += 1
        await self.db.flush()
        return len(source_map), scholarship_count

    async def _upsert_demo_users(self) -> None:
        await self._upsert_demo_user(
            email=settings.DEMO_STUDENT_EMAIL,
            password=settings.DEMO_STUDENT_PASSWORD,
            full_name=settings.DEMO_STUDENT_FULL_NAME,
            role=UserRole.STUDENT,
        )
        await self._upsert_demo_user(
            email=settings.DEMO_ADMIN_EMAIL,
            password=settings.DEMO_ADMIN_PASSWORD,
            full_name=settings.DEMO_ADMIN_FULL_NAME,
            role=UserRole.ADMIN,
        )

    async def _upsert_demo_user(
        self,
        *,
        email: str,
        password: str,
        full_name: str,
        role: UserRole,
    ) -> None:
        normalized_email = email.strip().lower()
        result = await self.db.execute(select(User).where(User.email == normalized_email))
        user = result.scalar_one_or_none()
        if user is None:
            user = User(email=normalized_email, password_hash=hash_password(password), full_name=full_name)
            self.db.add(user)

        user.email = normalized_email
        user.password_hash = hash_password(password)
        user.full_name = full_name
        user.role = role
        user.is_active = True

    async def _upsert_sources(self) -> dict[str, SourceRegistry]:
        sources: dict[str, SourceRegistry] = {}
        for payload in SOURCE_REGISTRY_SEED:
            result = await self.db.execute(
                select(SourceRegistry).where(
                    SourceRegistry.source_key == payload["source_key"]
                )
            )
            source = result.scalar_one_or_none()
            if source is None:
                source = SourceRegistry(source_key=payload["source_key"])
                self.db.add(source)

            source.display_name = payload["display_name"]
            source.base_url = payload["base_url"]
            source.source_type = payload["source_type"]
            source.is_active = True
            sources[payload["source_key"]] = source

        await self.db.flush()
        return sources

    async def _upsert_scholarship(
        self,
        payload: dict,
        source_map: dict[str, SourceRegistry],
    ) -> Scholarship:
        result = await self.db.execute(
            select(Scholarship)
            .where(Scholarship.source_url == payload["source_url"])
            .options(selectinload(Scholarship.requirements))
        )
        scholarship = result.scalar_one_or_none()

        if scholarship is None:
            scholarship = Scholarship(
                title=payload["title"],
                provider_name=payload["provider_name"],
                country_code=payload["country_code"],
                source_url=payload["source_url"],
                field_tags=[],
                degree_levels=[],
                citizenship_rules=[],
            )
            self.db.add(scholarship)

        scholarship.source_registry = source_map[payload["source_key"]]
        scholarship.external_source_id = payload["external_source_id"]
        scholarship.title = payload["title"]
        scholarship.provider_name = payload["provider_name"]
        scholarship.country_code = payload["country_code"]
        scholarship.summary = payload["summary"]
        scholarship.funding_summary = payload["funding_summary"]
        scholarship.funding_type = payload.get("funding_type")
        scholarship.funding_amount_min = payload.get("funding_amount_min")
        scholarship.funding_amount_max = payload.get("funding_amount_max")
        scholarship.source_url = payload["source_url"]
        scholarship.source_document_ref = payload["source_document_ref"]
        scholarship.field_tags = list(payload["field_tags"])
        scholarship.degree_levels = list(payload["degree_levels"])
        scholarship.citizenship_rules = list(payload["citizenship_rules"])
        scholarship.min_gpa_value = payload["min_gpa_value"]
        scholarship.deadline_at = payload["deadline_at"]
        scholarship.record_state = payload["record_state"]
        scholarship.imported_at = payload["imported_at"]
        scholarship.source_last_seen_at = payload["source_last_seen_at"]
        scholarship.review_notes = payload["review_notes"]
        scholarship.validated_at = payload["validated_at"]
        scholarship.published_at = payload["published_at"]
        scholarship.provenance_payload = dict(payload["provenance_payload"])
        scholarship.requirements = [
            ScholarshipRequirement(
                requirement_type=requirement["requirement_type"],
                operator=requirement["operator"],
                value_text=requirement.get("value_text"),
                value_json=requirement.get("value_json"),
            )
            for requirement in payload["requirements"]
        ]
        return scholarship


async def seed_demo_data_if_enabled() -> None:
    if not settings.AUTO_SEED_DEMO_DATA:
        return

    try:
        async with async_session_factory() as session:
            if not await _tables_exist(session, REQUIRED_TABLES):
                logger.info("Skipping demo seed because the core scholarship tables are missing.")
                return

            source_count, scholarship_count = await DemoSeedService(session).ensure_seeded()
            await session.commit()
            logger.info(
                "Demo dataset ready with %s source records and %s scholarship records.",
                source_count,
                scholarship_count,
            )
    except Exception:
        logger.exception("Failed to seed demo dataset.")


async def _tables_exist(session: AsyncSession, table_names: Iterable[str]) -> bool:
    required = set(table_names)

    def inspect_tables(sync_session) -> bool:
        inspector = inspect(sync_session.bind)
        return required.issubset(set(inspector.get_table_names()))

    return await session.run_sync(inspect_tables)
