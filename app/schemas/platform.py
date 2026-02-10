import datetime as dt
from uuid import UUID

from pydantic import BaseModel


class SetupStatusResponse(BaseModel):
    needed: bool
    has_admin: bool
    is_complete: bool


class BootstrapRequest(BaseModel):
    platform_name: str = "Cricket Club Manager"


class BootstrapResponse(BaseModel):
    message: str
    admin_id: UUID


class PlatformClubRead(BaseModel):
    id: UUID
    name: str
    slug: str
    status: str
    member_count: int
    created_at: dt.datetime
    suspended_at: dt.datetime | None = None
    suspension_reason: str | None = None


class SuspendClubRequest(BaseModel):
    club_id: UUID
    reason: str


class ReactivateClubRequest(BaseModel):
    club_id: UUID


class DeleteClubRequest(BaseModel):
    club_id: UUID
    reason: str


class PlatformAdminRead(BaseModel):
    id: UUID
    user_id: UUID
    email: str
    full_name: str | None = None
    is_active: bool
    permissions_list: list[str] = []
    created_at: dt.datetime
    last_login_at: dt.datetime | None = None


class AddAdminRequest(BaseModel):
    user_id: UUID
    permissions: list[str] = ["manage_clubs", "view_analytics"]
    notes: str | None = None


class AuditLogEntryRead(BaseModel):
    id: UUID
    admin_id: UUID | None
    admin_email: str
    action: str
    target_type: str
    target_id: UUID | None = None
    details: dict = {}
    created_at: dt.datetime
