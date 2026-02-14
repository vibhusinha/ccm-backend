from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

PLAYER_ROLE_PATTERN = "^(Batter|Bowler|All-rounder|Wicket-keeper)$"


class PlayerRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    club_id: UUID
    user_id: UUID | None
    club_member_id: UUID | None
    name: str
    email: str | None
    phone: str | None
    address: str | None
    date_of_birth: date | None
    role: str
    team_id: UUID | None
    is_core: bool
    member_since: date | None
    play_cricket_id: int | None = None
    created_at: datetime
    updated_at: datetime


class PlayerCreate(BaseModel):
    name: str = Field(..., max_length=255)
    role: str = Field(..., pattern=PLAYER_ROLE_PATTERN)
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    date_of_birth: date | None = None
    team_id: UUID | None = None
    is_core: bool = False
    user_id: UUID | None = None
    club_member_id: UUID | None = None
    play_cricket_id: int | None = None


class PlayerUpdate(BaseModel):
    name: str | None = None
    role: str | None = Field(None, pattern=PLAYER_ROLE_PATTERN)
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    date_of_birth: date | None = None
    team_id: UUID | None = None
    is_core: bool | None = None
    user_id: UUID | None = None
    club_member_id: UUID | None = None
    play_cricket_id: int | None = None
