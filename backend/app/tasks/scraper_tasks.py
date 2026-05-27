import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.core.database import async_session_factory
from app.models import IngestionRun, IngestionRunStatus, SourceRegistry
from app.services.ingestion import IngestionService
from app.schemas.curation import IngestionRunStartRequest
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

# A scheduled run is considered stale if more than this many hours have
# passed since the last completion. Cadence is every 10 days (1st/11th/21st
# @ 02:00 UTC per celery_app beat) — ``SCHEDULED_MAX_AGE_HOURS = 11 * 24``
# means a hourly catch-up beat (if one is added later) would only re-fire
# after the canonical slot is fully missed.
SCHEDULED_MAX_AGE_HOURS = 11 * 24
SCHEDULED_SOURCE_KEY = "scheduled_sync_main"

# Back-compat aliases — older deploys / logs reference these names.
NIGHTLY_MAX_AGE_HOURS = SCHEDULED_MAX_AGE_HOURS
NIGHTLY_SOURCE_KEY = SCHEDULED_SOURCE_KEY


def _nightly_run_is_stale(
    last_completed_at: datetime | None,
    *,
    now: datetime | None = None,
    max_age_hours: int = SCHEDULED_MAX_AGE_HOURS,
) -> bool:
    """True when the most recent scheduled completion is missing or too old."""
    if last_completed_at is None:
        return True
    reference = now or datetime.now(timezone.utc)
    if last_completed_at.tzinfo is None:
        last_completed_at = last_completed_at.replace(tzinfo=timezone.utc)
    return (reference - last_completed_at) > timedelta(hours=max_age_hours)


async def _load_last_nightly_completion(session) -> datetime | None:
    """Most recent ``completed_at`` for the scheduled-sync source, if any."""
    try:
        result = await session.execute(
            select(IngestionRun.completed_at)
            .join(SourceRegistry)
            .where(
                SourceRegistry.source_key == SCHEDULED_SOURCE_KEY,
                IngestionRun.status.in_(
                    (IngestionRunStatus.COMPLETED, IngestionRunStatus.PARTIAL)
                ),
                IngestionRun.completed_at.is_not(None),
            )
            .order_by(IngestionRun.completed_at.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
    except Exception:  # pragma: no cover - defensive
        return None
    return row if isinstance(row, datetime) else None


async def _should_run_nightly(session) -> bool:
    last_completed = await _load_last_nightly_completion(session)
    return _nightly_run_is_stale(last_completed)


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


@celery_app.task(name="tasks.run_scheduled_ingestion")
def run_scheduled_ingestion() -> dict:
    """Automated every-10-day sync for major scholarship sources.

    Beat schedule (``app.tasks.celery_app``) fires this on the 1st, 11th, and
    21st of each month at 02:00 UTC. Skips when a recent
    (≤ ``SCHEDULED_MAX_AGE_HOURS``) successful run already exists so an
    ad-hoc invocation cannot double-burn Firecrawl credits on the same slot.
    """
    # System Reserved UUID
    SYSTEM_ADMIN_ID = "00000000-0000-0000-0000-000000000000"

    return asyncio.run(_run_scheduled_ingestion_async(SYSTEM_ADMIN_ID))


# Back-compat alias — queued tasks in flight from the nightly era still
# resolve. Remove on the deploy after this rename has shipped + drained.
@celery_app.task(name="tasks.run_nightly_ingestion")
def run_nightly_ingestion() -> dict:
    return run_scheduled_ingestion()


async def _run_scheduled_ingestion_async(system_actor_id: str) -> dict:
    async with async_session_factory() as session:
        if not await _should_run_nightly(session):
            logger.info("scheduled_ingestion_skip reason=recent_run_present")
            return {"status": "skipped", "reason": "recent_run_present"}
    return await _run_source_ingestion_async(
        run_id=None,
        source_key=SCHEDULED_SOURCE_KEY,
        actor_user_id=system_actor_id,
        source_display_name="Auto Scheduled Ingestion",
        source_base_url=None,
        source_type="official",
        max_records=20,
    )


# Back-compat alias for any callers still importing the old coroutine name.
_run_nightly_ingestion_async = _run_scheduled_ingestion_async
