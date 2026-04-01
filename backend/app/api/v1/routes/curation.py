import uuid
from typing import Annotated
import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurationQueueUser, CurationValidateUser, IngestionRunUser
from app.schemas import (
    CurationActionRequest,
    CurationRawImportRequest,
    CurationRecordDetail,
    CurationRecordListResponse,
    CurationRecordUpdateRequest,
    IngestionRunBulkRetryRequest,
    IngestionRunBulkRetryResponse,
    IngestionRunDetail,
    IngestionRunListResponse,
    IngestionRunQueueAssignmentRequest,
    IngestionRunRetryRequest,
    IngestionRunStartRequest,
)
from app.services.curation import CurationService
from app.services.ingestion import IngestionService
from app.tasks.scraper_tasks import run_source_ingestion

router = APIRouter()
logger = logging.getLogger(__name__)


def _extract_run_diagnostics(run_metadata: dict | None) -> dict[str, str | int | None]:
    metadata = run_metadata if isinstance(run_metadata, dict) else {}
    execution = metadata.get("execution")
    execution_context = execution if isinstance(execution, dict) else {}
    requested_mode = (
        execution_context.get("requested_mode")
        or metadata.get("requested_mode")
        or metadata.get("execution_mode_requested")
    )
    selected_mode = (
        execution_context.get("selected_mode")
        or metadata.get("selected_mode")
        or metadata.get("execution_mode_selected")
    )
    dispatch_status = (
        execution_context.get("dispatch_status")
        or metadata.get("dispatch_status")
    )
    celery_task_id = (
        execution_context.get("celery_task_id")
        or metadata.get("celery_task_id")
    )
    return {
        "execution_mode_requested": requested_mode,
        "execution_mode_selected": selected_mode,
        "dispatch_status": dispatch_status,
        "celery_task_id": celery_task_id,
        "attempt_count": execution_context.get("attempt_count"),
        "run_retry_count": execution_context.get("run_retry_count"),
        "last_started_at": execution_context.get("last_started_at"),
        "last_retry_requested_at": execution_context.get("last_retry_requested_at"),
        "failure_phase": (metadata.get("failure") or {}).get("phase")
        if isinstance(metadata.get("failure"), dict)
        else None,
        "review_queue": execution_context.get("review_queue"),
        "queue_assigned_by_user_id": execution_context.get("queue_assigned_by_user_id"),
        "queue_assigned_at": execution_context.get("queue_assigned_at"),
        "queue_assignment_note": execution_context.get("queue_assignment_note"),
    }


def _with_run_diagnostics(detail: IngestionRunDetail) -> IngestionRunDetail:
    return detail.model_copy(update=_extract_run_diagnostics(detail.run_metadata))


@router.post("/ingestion-runs", response_model=IngestionRunDetail, status_code=201)
async def start_ingestion_run(
    payload: IngestionRunStartRequest,
    current_user: IngestionRunUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> IngestionRunDetail:
    service = IngestionService(db)
    if payload.execution_mode == "inline":
        detail = await service.start_run(payload, current_user)
        await db.commit()
        return _with_run_diagnostics(detail)

    detail = await service.create_run(payload, current_user)
    run_id = uuid.UUID(detail.run_id)
    await db.commit()

    try:
        task_result = run_source_ingestion.apply_async(
            kwargs={
                "run_id": detail.run_id,
                "max_records": payload.max_records,
            }
        )
        detail = await service.update_execution_context(
            run_id,
            {
                "requested_mode": payload.execution_mode,
                "selected_mode": "worker",
                "dispatch_status": "queued",
                "celery_task_id": task_result.id,
            },
        )
        await db.commit()
        return _with_run_diagnostics(detail)
    except Exception as exc:
        detail = await service.execute_run(
            run_id,
            actor_user_id=current_user.id,
            max_records=payload.max_records,
            execution_context={
                "requested_mode": payload.execution_mode,
                "selected_mode": "inline",
                "dispatch_status": "inline_fallback",
                "dispatch_error": str(exc),
            },
        )
        await db.commit()
        return _with_run_diagnostics(detail)


@router.get("/ingestion-runs", response_model=IngestionRunListResponse)
async def list_ingestion_runs(
    current_user: CurationQueueUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: str | None = Query(default=None),
    source_key: str | None = Query(default=None),
    dispatch_status: str | None = Query(default=None),
) -> IngestionRunListResponse:
    service = IngestionService(db)
    response = await service.list_runs(
        current_user,
        page=page,
        page_size=page_size,
        status_filter=status,
        source_key=source_key,
        dispatch_status=dispatch_status,
    )
    return response


@router.post("/ingestion-runs/{run_id}/retry", response_model=IngestionRunDetail)
async def retry_ingestion_run(
    run_id: uuid.UUID,
    payload: IngestionRunRetryRequest,
    current_user: IngestionRunUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> IngestionRunDetail:
    service = IngestionService(db)
    detail = await service.retry_run(run_id, payload=payload, actor_user=current_user)
    await db.commit()
    return _with_run_diagnostics(detail)


@router.post("/ingestion-runs/{run_id}/assign-queue", response_model=IngestionRunDetail)
async def assign_ingestion_run_queue(
    run_id: uuid.UUID,
    payload: IngestionRunQueueAssignmentRequest,
    current_user: IngestionRunUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> IngestionRunDetail:
    service = IngestionService(db)
    detail = await service.assign_review_queue(run_id, payload=payload, actor_user=current_user)
    await db.commit()
    return _with_run_diagnostics(detail)


@router.post("/ingestion-runs/bulk-retry", response_model=IngestionRunBulkRetryResponse)
async def bulk_retry_ingestion_runs(
    payload: IngestionRunBulkRetryRequest,
    current_user: IngestionRunUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> IngestionRunBulkRetryResponse:
    service = IngestionService(db)
    response = await service.bulk_retry_runs(payload=payload, actor_user=current_user)
    await db.commit()
    return response


@router.get("/ingestion-runs/{run_id}", response_model=IngestionRunDetail)
async def get_ingestion_run(
    run_id: uuid.UUID,
    current_user: CurationQueueUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> IngestionRunDetail:
    service = IngestionService(db)
    detail = await service.get_run(run_id, actor_user=current_user)
    return _with_run_diagnostics(detail)


@router.post("/imports", response_model=CurationRecordDetail)
async def import_raw_curation_record(
    payload: CurationRawImportRequest,
    current_user: CurationValidateUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CurationRecordDetail:
    service = CurationService(db)
    return await service.import_raw_record(payload, current_user)


@router.get("/records", response_model=CurationRecordListResponse)
async def list_curation_records(
    current_user: CurationQueueUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    state: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
) -> CurationRecordListResponse:
    service = CurationService(db)
    items, total = await service.list_records(
        current_user,
        state=state,
        page=page,
        page_size=page_size,
    )
    has_more = (page * page_size) < total
    return CurationRecordListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_more=has_more,
        applied_state=state.lower() if state else None,
    )


@router.get("/records/{record_id}", response_model=CurationRecordDetail)
async def get_curation_record(
    record_id: uuid.UUID,
    current_user: CurationQueueUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CurationRecordDetail:
    service = CurationService(db)
    logger.info("curation_get_record record_id=%s actor_id=%s", record_id, current_user.id)
    return await service.get_record(record_id, current_user)


@router.patch("/records/{record_id}", response_model=CurationRecordDetail)
async def update_curation_record(
    record_id: uuid.UUID,
    payload: CurationRecordUpdateRequest,
    current_user: CurationValidateUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CurationRecordDetail:
    service = CurationService(db)
    return await service.update_record(record_id, payload, current_user)


@router.post("/records/{record_id}/approve", response_model=CurationRecordDetail)
async def approve_curation_record(
    record_id: uuid.UUID,
    payload: CurationActionRequest,
    current_user: CurationValidateUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CurationRecordDetail:
    service = CurationService(db)
    return await service.approve_record(record_id, payload, current_user)


@router.post("/records/{record_id}/reject", response_model=CurationRecordDetail)
async def reject_curation_record(
    record_id: uuid.UUID,
    payload: CurationActionRequest,
    current_user: CurationValidateUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CurationRecordDetail:
    service = CurationService(db)
    return await service.reject_record(record_id, payload, current_user)


@router.post("/records/{record_id}/publish", response_model=CurationRecordDetail)
async def publish_curation_record(
    record_id: uuid.UUID,
    payload: CurationActionRequest,
    current_user: CurationValidateUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CurationRecordDetail:
    service = CurationService(db)
    return await service.publish_record(record_id, payload, current_user)


@router.post("/records/{record_id}/unpublish", response_model=CurationRecordDetail)
async def unpublish_curation_record(
    record_id: uuid.UUID,
    payload: CurationActionRequest,
    current_user: CurationValidateUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CurationRecordDetail:
    service = CurationService(db)
    return await service.unpublish_record(record_id, payload, current_user)
