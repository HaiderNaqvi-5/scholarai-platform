"""Application tracker REST surface (Feature 6, PRD §6)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUser
from app.core.plan_guard import has_plan_at_least
from app.schemas.tracker import (
    TrackerChecklistPatchRequest,
    TrackerItemCreateRequest,
    TrackerItemResponse,
    TrackerListResponse,
    TrackerStageUpdateRequest,
)
from app.services.tracker import TrackerService
from app.services.tracker.service import FREE_PLAN_ITEM_LIMIT

router = APIRouter()


@router.get("", response_model=TrackerListResponse)
async def list_tracker_items(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TrackerListResponse:
    service = TrackerService(db)
    items = await service.list_items(current_user.id)
    plan_limit = (
        None
        if has_plan_at_least(current_user, "pro", "elite", "institution")
        else FREE_PLAN_ITEM_LIMIT
    )
    return TrackerListResponse(
        items=[TrackerItemResponse.model_validate(item) for item in items],
        total=len(items),
        plan_limit=plan_limit,
        plan=current_user.plan or "free",
    )


@router.post("", response_model=TrackerItemResponse, status_code=status.HTTP_201_CREATED)
async def create_tracker_item(
    payload: TrackerItemCreateRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TrackerItemResponse:
    service = TrackerService(db)
    item = await service.create(current_user, payload)
    return TrackerItemResponse.model_validate(item)


@router.patch("/{item_id}/stage", response_model=TrackerItemResponse)
async def update_tracker_stage(
    item_id: uuid.UUID,
    payload: TrackerStageUpdateRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TrackerItemResponse:
    service = TrackerService(db)
    item = await service.update_stage(current_user.id, item_id, payload)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tracker item not found")
    return TrackerItemResponse.model_validate(item)


@router.patch("/{item_id}/checklist", response_model=TrackerItemResponse)
async def update_tracker_checklist(
    item_id: uuid.UUID,
    payload: TrackerChecklistPatchRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TrackerItemResponse:
    service = TrackerService(db)
    item = await service.update_checklist(current_user.id, item_id, payload)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tracker item not found")
    return TrackerItemResponse.model_validate(item)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tracker_item(
    item_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    service = TrackerService(db)
    deleted = await service.delete(current_user.id, item_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tracker item not found")
