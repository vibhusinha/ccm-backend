from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PermissionRead(BaseModel):
    key: str
    name: str
    description: str
    category: str


class RoleRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    name: str
    display_name: str
    description: str | None = None
    hierarchy_level: int
    is_system_role: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


class RolePermissionRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    permission_key: str
    granted: bool


class RoleWithPermissionsRead(RoleRead):
    permissions: list[RolePermissionRead] = []


class RoleCreate(BaseModel):
    name: str = Field(..., max_length=50)
    display_name: str = Field(..., max_length=100)
    description: str | None = None
    hierarchy_level: int = 100
    permission_keys: list[str] = []


class RoleUpdate(BaseModel):
    display_name: str | None = None
    description: str | None = None
    hierarchy_level: int | None = None
    is_active: bool | None = None
    permission_keys: list[str] | None = None


class ChangeRoleRequest(BaseModel):
    new_role: str = Field(..., max_length=50)


class SingleAdminCheckResponse(BaseModel):
    has_single_admin: bool
    admin_count: int


class UserPermissionsResponse(BaseModel):
    user_id: UUID
    club_id: UUID
    role: str
    permissions: list[str]
