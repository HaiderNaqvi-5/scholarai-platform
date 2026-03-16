import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AdminUser
from app.schemas import (
    CurationActionRequest,
    IngestionRunDetail,
    IngestionRunListResponse,
    IngestionRunStartRequest,
    CurationRawImportRequest,
    CurationRecordDetail,
    CurationRecordListResponse,
    CurationRecordUpdateRequest,
)
from app.services.curation import CurationService
from app.services.ingestion import IngestionService

router = APIRouter()


@router.post("/ingestion-runs", response_model=IngestionRunDetail, status_code=201)
async def start_ingestion_run(
    payload: IngestionRunStartRequest,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> IngestionRunDetail:
    service = IngestionService(db)
    return await service.start_run(payload, current_user.id)


@router.get("/ingestion-runs", response_model=IngestionRunListResponse)
async def list_ingestion_runs(
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=20, ge=1, le=100),
) -> IngestionRunListResponse:
    service = IngestionService(db)
    return await service.list_runs(limit=limit)


@router.get("/ingestion-runs/{run_id}", response_model=IngestionRunDetail)
async def get_ingestion_run(
    run_id: uuid.UUID,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> IngestionRunDetail:
    service = IngestionService(db)
    return await service.get_run(run_id)


@router.post("/imports", response_model=CurationRecordDetail)
async def import_raw_curation_record(
    payload: CurationRawImportRequest,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CurationRecordDetail:
    service = CurationService(db)
    return await service.import_raw_record(payload, current_user.id)


@router.get("/records", response_model=CurationRecordListResponse)
async def list_curation_records(
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    state: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
) -> CurationRecordListResponse:
    service = CurationService(db)
    items = await service.list_records(state=state, limit=limit)
    return CurationRecordListResponse(
        items=items,
        total=len(items),
        applied_state=state.lower() if state else None,
    )


@router.get("/records/{record_id}", response_model=CurationRecordDetail)
async def get_curation_record(
    record_id: uuid.UUID,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CurationRecordDetail:
    service = CurationService(db)
    return await service.get_record(record_id)


@router.patch("/records/{record_id}", response_model=CurationRecordDetail)
async def update_curation_record(
    record_id: uuid.UUID,
    payload: CurationRecordUpdateRequest,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CurationRecordDetail:
    service = CurationService(db)
    return await service.update_record(record_id, payload, current_user.id)


@router.post("/records/{record_id}/approve", response_model=CurationRecordDetail)
async def approve_curation_record(
    record_id: uuid.UUID,
    payload: CurationActionRequest,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CurationRecordDetail:
    service = CurationService(db)
    return await service.approve_record(record_id, payload, current_user.id)


@router.post("/records/{record_id}/reject", response_model=CurationRecordDetail)
async def reject_curation_record(
    record_id: uuid.UUID,
    payload: CurationActionRequest,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CurationRecordDetail:
    service = CurationService(db)
    return await service.reject_record(record_id, payload, current_user.id)


@router.post("/records/{record_id}/publish", response_model=CurationRecordDetail)
async def publish_curation_record(
    record_id: uuid.UUID,
    payload: CurationActionRequest,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CurationRecordDetail:
    service = CurationService(db)
    return await service.publish_record(record_id, payload, current_user.id)


@router.post("/records/{record_id}/unpublish", response_model=CurationRecordDetail)
async def unpublish_curation_record(
    record_id: uuid.UUID,
    payload: CurationActionRequest,
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CurationRecordDetail:
    service = CurationService(db)
    return await service.unpublish_record(record_id, payload, current_user.id)
