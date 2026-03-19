import asyncio
import uuid

from app.core.database import async_session_factory
from app.services.ingestion import IngestionService
from app.schemas.curation import IngestionRunStartRequest
from app.tasks.celery_app import celery_app


def _extract_run_diagnostics(run_metadata: dict | None) -> dict[str, str | None]:
    metadata = run_metadata if isinstance(run_metadata, dict) else {}
    execution = metadata.get("execution")
    execution_context = execution if isinstance(execution, dict) else {}
    return {
        "execution_mode_requested": (
            execution_context.get("requested_mode")
            or metadata.get("requested_mode")
            or metadata.get("execution_mode_requested")
        ),
        "execution_mode_selected": (
            execution_context.get("selected_mode")
            or metadata.get("selected_mode")
            or metadata.get("execution_mode_selected")
        ),
        "dispatch_status": (
            execution_context.get("dispatch_status")
            or metadata.get("dispatch_status")
        ),
        "celery_task_id": (
            execution_context.get("celery_task_id")
            or metadata.get("celery_task_id")
        ),
    }


def _detail_to_payload(detail) -> dict:
    payload = detail.model_dump()
    run_metadata = payload.get("run_metadata")
    payload.update(_extract_run_diagnostics(run_metadata))
    return payload


@celery_app.task(name="tasks.run_source_ingestion")
def run_source_ingestion(
    run_id: str | None = None,
    source_key: str | None = None,
    actor_user_id: str | None = None,
    source_display_name: str | None = None,
    source_base_url: str | None = None,
    source_type: str = "official",
    max_records: int = 5,
) -> dict:
    return asyncio.run(
        _run_source_ingestion_async(
            run_id=run_id,
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
    run_id: str | None,
    source_key: str | None,
    actor_user_id: str | None,
    source_display_name: str | None,
    source_base_url: str | None,
    source_type: str,
    max_records: int,
) -> dict:
    async with async_session_factory() as session:
        service = IngestionService(session)
        if run_id:
            detail = await service.execute_run(
                uuid.UUID(run_id),
                actor_user_id=uuid.UUID(actor_user_id) if actor_user_id else None,
                max_records=max_records,
                execution_context={
                    "selected_mode": "worker",
                    "dispatch_status": "running",
                },
                persist_running_state=True,
            )
        else:
            if source_key is None or actor_user_id is None:
                raise ValueError("source_key and actor_user_id are required when run_id is not provided")
            actor_id = uuid.UUID(actor_user_id)
            payload = IngestionRunStartRequest(
                source_key=source_key,
                source_display_name=source_display_name,
                source_base_url=source_base_url,
                source_type=source_type,
                max_records=max_records,
                execution_mode="worker",
            )
            if hasattr(service, "create_run") and hasattr(service, "execute_run"):
                created_run = await service.create_run(payload, actor_id)
                detail = await service.execute_run(
                    uuid.UUID(created_run.run_id),
                    actor_user_id=actor_id,
                    max_records=max_records,
                    execution_context={
                        "requested_mode": "worker",
                        "selected_mode": "worker",
                        "dispatch_status": "running",
                    },
                    persist_running_state=True,
                )
            else:
                detail = await service.start_run(payload, actor_id)
        await session.commit()
        return _detail_to_payload(detail)


@celery_app.task(name="tasks.run_nightly_ingestion")
def run_nightly_ingestion() -> dict:
    """
    Automated nightly sync for major scholarship sources.
    """
    # System Reserved UUID
    SYSTEM_ADMIN_ID = "00000000-0000-0000-0000-000000000000"
    
    return asyncio.run(
        _run_source_ingestion_async(
            run_id=None,
            source_key="nightly_sync_main",
            actor_user_id=SYSTEM_ADMIN_ID,
            source_display_name="Auto Nightly Ingestion",
            source_base_url=None,
            source_type="official",
            max_records=20,
        )
    )
