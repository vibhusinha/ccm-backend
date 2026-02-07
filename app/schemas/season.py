from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class SeasonRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    club_id: UUID
    name: str
    start_date: date
    end_date: date
    status: str
    is_current: bool
    created_at: datetime
    updated_at: datetime


class SeasonCreate(BaseModel):
    name: str = Field(..., max_length=100)
    start_date: date
    end_date: date
    is_current: bool = False
    status: str = "draft"


class SeasonUpdate(BaseModel):
    name: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool | None = None
    status: str | None = None
