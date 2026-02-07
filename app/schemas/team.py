from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class TeamRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    club_id: UUID
    name: str
    division: str | None
    division_number: int | None
    division_group: str | None
    captain_id: UUID | None
    vice_captain_id: UUID | None
    season_id: UUID | None
    display_order: int
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class TeamCreate(BaseModel):
    name: str = Field(..., max_length=100)
    division: str | None = None
    division_number: int | None = Field(None, ge=1, le=10)
    division_group: str | None = Field(None, pattern="^[A-D]$")
    captain_id: UUID | None = None
    vice_captain_id: UUID | None = None
    season_id: UUID | None = None
    display_order: int = 0
    description: str | None = None
    is_active: bool = True


class TeamUpdate(BaseModel):
    name: str | None = None
    division: str | None = None
    division_number: int | None = Field(None, ge=1, le=10)
    division_group: str | None = Field(None, pattern="^[A-D]$")
    captain_id: UUID | None = None
    vice_captain_id: UUID | None = None
    season_id: UUID | None = None
    display_order: int | None = None
    description: str | None = None
    is_active: bool | None = None
