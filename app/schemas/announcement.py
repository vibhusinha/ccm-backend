from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class AnnouncementRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    club_id: UUID
    type: str
    title: str
    body: str | None = None
    target_team_id: UUID | None = None
    match_id: UUID | None = None
    is_archived: bool
    created_by: UUID
    published_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class AnnouncementCreate(BaseModel):
    type: str = Field("general", pattern="^(general|match|team|urgent|event)$")
    title: str = Field(..., max_length=255)
    body: str | None = None
    target_team_id: UUID | None = None
    match_id: UUID | None = None
    is_archived: bool = False
    published_at: datetime | None = None


class AnnouncementUpdate(BaseModel):
    type: str | None = Field(None, pattern="^(general|match|team|urgent|event)$")
    title: str | None = Field(None, max_length=255)
    body: str | None = None
    target_team_id: UUID | None = None
    match_id: UUID | None = None
    is_archived: bool | None = None
    published_at: datetime | None = None
