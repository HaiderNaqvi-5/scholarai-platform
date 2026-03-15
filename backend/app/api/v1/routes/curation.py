import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AdminUser
from app.schemas import (
    CurationActionRequest,
    CurationRecordDetail,
    CurationRecordListResponse,
    CurationRecordUpdateRequest,
)
from app.services.curation import CurationService

router = APIRouter()


@router.get("/records", response_model=CurationRecordListResponse)
async def list_curation_records(
    current_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    state: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
) -> CurationRecordListResponse:
    service = CurationService(db)
    items = await service.list_records(state=state, limit=limit)
    return CurationRecordListResponse(items=items)


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
