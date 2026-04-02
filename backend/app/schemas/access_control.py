from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models import UserRole


class AccessControlManagedUser(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: UUID
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    auth_token_version: int = Field(ge=0)
    effective_capabilities: list[str]


class AccessControlManagedUserListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[AccessControlManagedUser]
    total: int = Field(ge=0)


class AccessControlRoleChangeItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    audit_id: UUID
    target_user_id: UUID
    actor_user_id: UUID | None
    action: str
    previous_role: UserRole
    next_role: UserRole
    reason: str | None
    changed_at: datetime
    reverted_by_audit_id: UUID | None
    is_reversible: bool


class AccessControlRoleChangeListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[AccessControlRoleChangeItem]
    total: int = Field(ge=0)


class AccessControlRoleUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: UserRole
    reason: str | None = Field(default=None, max_length=500)


class AccessControlRoleRevertRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str | None = Field(default=None, max_length=500)
