import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AdminAuditUser, OwnerControlUser
from app.schemas import (
    AccessControlManagedUserListResponse,
    AccessControlRoleChangeItem,
    AccessControlRoleChangeListResponse,
    AccessControlRoleRevertRequest,
    AccessControlRoleUpdateRequest,
)
from app.services.access_control import AccessControlService

router = APIRouter()


@router.get("/users", response_model=AccessControlManagedUserListResponse)
async def list_managed_users(
    current_user: AdminAuditUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AccessControlManagedUserListResponse:
    service = AccessControlService(db)
    return await service.list_managed_users()


@router.get("/role-changes", response_model=AccessControlRoleChangeListResponse)
async def list_role_changes(
    current_user: AdminAuditUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    target_user_id: uuid.UUID | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> AccessControlRoleChangeListResponse:
    service = AccessControlService(db)
    return await service.list_role_changes(target_user_id=target_user_id, limit=limit)


@router.patch("/users/{target_user_id}/role", response_model=AccessControlRoleChangeItem)
async def update_user_role(
    target_user_id: uuid.UUID,
    payload: AccessControlRoleUpdateRequest,
    current_user: OwnerControlUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AccessControlRoleChangeItem:
    service = AccessControlService(db)
    response = await service.update_user_role(
        actor_user_id=current_user.id,
        target_user_id=target_user_id,
        role=payload.role,
        reason=payload.reason,
    )
    await db.commit()
    return response


@router.post(
    "/role-changes/{audit_id}/revert",
    response_model=AccessControlRoleChangeItem,
)
async def revert_role_change(
    audit_id: uuid.UUID,
    payload: AccessControlRoleRevertRequest,
    current_user: OwnerControlUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AccessControlRoleChangeItem:
    service = AccessControlService(db)
    response = await service.revert_role_change(
        actor_user_id=current_user.id,
        audit_id=audit_id,
        reason=payload.reason,
    )
    await db.commit()
    return response
