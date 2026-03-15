import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUser
from app.schemas import SavedOpportunityItem, SavedOpportunityListResponse
from app.services.saved_opportunities import SavedOpportunityService

router = APIRouter()


@router.get("", response_model=SavedOpportunityListResponse)
async def list_saved_opportunities(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SavedOpportunityListResponse:
    service = SavedOpportunityService(db)
    items = await service.list_saved(current_user.id)
    return SavedOpportunityListResponse(items=items)


@router.post("/{scholarship_id}", response_model=SavedOpportunityItem, status_code=status.HTTP_201_CREATED)
async def save_opportunity(
    scholarship_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SavedOpportunityItem:
    service = SavedOpportunityService(db)
    return await service.save(current_user.id, scholarship_id)


@router.delete("/{scholarship_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_saved_opportunity(
    scholarship_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    service = SavedOpportunityService(db)
    await service.remove(current_user.id, scholarship_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
