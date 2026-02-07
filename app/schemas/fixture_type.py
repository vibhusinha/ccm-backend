from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class FixtureTypeRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    club_id: UUID
    name: str
    description: str | None
    color: str
    icon: str
    display_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class FixtureTypeCreate(BaseModel):
    name: str
    description: str | None = None
    color: str = "#1a7f5f"
    icon: str = "\U0001f4c5"
    display_order: int = 0
    is_active: bool = True


class FixtureTypeUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    color: str | None = None
    icon: str | None = None
    display_order: int | None = None
    is_active: bool | None = None
