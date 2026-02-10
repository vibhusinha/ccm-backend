from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ApprovedClubRead(BaseModel):
    id: UUID
    name: str
    slug: str
    logo_url: str | None = None
    primary_color: str
    member_count: int = 0


class RegistrationStatusRead(BaseModel):
    status: str
    club_id: UUID | None = None
    club_name: str | None = None
    rejection_reason: str | None = None


class RegistrationRequestRead(BaseModel):
    id: UUID
    user_id: UUID
    club_id: UUID
    status: str
    requested_at: datetime
    reviewed_at: datetime | None = None
    rejection_reason: str | None = None
    user_email: str | None = None
    user_full_name: str | None = None


class PendingClubRegistrationRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    requested_by: UUID
    club_name: str
    club_slug: str
    status: str
    requested_at: datetime
    reviewed_at: datetime | None = None
    rejection_reason: str | None = None


class PendingClubWithUserRead(PendingClubRegistrationRead):
    requester_email: str | None = None
    requester_full_name: str | None = None


class UpdateRequestedClubRequest(BaseModel):
    club_id: UUID


class ApproveRegistrationRequest(BaseModel):
    registration_id: UUID
    role: str = "player"


class RejectRegistrationRequest(BaseModel):
    registration_id: UUID
    reason: str | None = None


class SubmitClubRequest(BaseModel):
    club_name: str = Field(..., max_length=255)


class ApproveClubRequest(BaseModel):
    pending_club_id: UUID


class RejectClubRequest(BaseModel):
    pending_club_id: UUID
    reason: str | None = None
