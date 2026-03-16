import asyncio
import uuid

from app.core.database import async_session_factory
from app.services.ingestion import IngestionService
from app.schemas.curation import IngestionRunStartRequest
from app.tasks.celery_app import celery_app


@celery_app.task(name="tasks.run_source_ingestion")
def run_source_ingestion(
    source_key: str,
    actor_user_id: str,
    source_display_name: str | None = None,
    source_base_url: str | None = None,
    source_type: str = "official",
    max_records: int = 5,
) -> dict:
    return asyncio.run(
        _run_source_ingestion_async(
            source_key=source_key,
            actor_user_id=actor_user_id,
            source_display_name=source_display_name,
            source_base_url=source_base_url,
            source_type=source_type,
            max_records=max_records,
        )
    )


async def _run_source_ingestion_async(
    *,
    source_key: str,
    actor_user_id: str,
    source_display_name: str | None,
    source_base_url: str | None,
    source_type: str,
    max_records: int,
) -> dict:
    async with async_session_factory() as session:
        service = IngestionService(session)
        detail = await service.start_run(
            IngestionRunStartRequest(
                source_key=source_key,
                source_display_name=source_display_name,
                source_base_url=source_base_url,
                source_type=source_type,
                max_records=max_records,
            ),
            uuid.UUID(actor_user_id),
        )
        await session.commit()
        return detail.model_dump()
