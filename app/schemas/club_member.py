from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.profile import ProfileRead

ROLE_PATTERN = "^(admin|secretary|treasurer|captain|vice_captain|player|social_member)$"


class ClubMemberRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    user_id: UUID
    club_id: UUID
    role: str
    joined_at: datetime


class ClubMemberWithProfile(ClubMemberRead):
    profile: ProfileRead | None = None


class ClubMemberCreate(BaseModel):
    user_id: UUID
    role: str = Field(..., pattern=ROLE_PATTERN)


class ClubMemberUpdate(BaseModel):
    role: str = Field(..., pattern=ROLE_PATTERN)
