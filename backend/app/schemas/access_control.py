from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AccessControlManagedUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    email: str
    role: str
    institution_id: str | None = None
    created_at: datetime


class AccessControlManagedUserListResponse(BaseModel):
    items: list[AccessControlManagedUser]
    total: int = Field(ge=0)


class AccessControlRoleChangeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: str
    role: str
    note: str | None = Field(default=None, max_length=2000)


class AccessControlRoleChangeRevertRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    change_id: str
    note: str | None = Field(default=None, max_length=2000)


class AccessControlRoleChangeItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    change_id: str
    user_id: str
    old_role: str
    new_role: str
    changed_by_user_id: str
    changed_at: datetime
    note: str | None = None


class AccessControlRoleChangeListResponse(BaseModel):
    items: list[AccessControlRoleChangeItem]
    total: int = Field(ge=0)
