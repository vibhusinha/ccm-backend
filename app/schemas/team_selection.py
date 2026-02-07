from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class SelectionRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    match_id: UUID
    player_id: UUID
    batting_position: int | None
    is_captain: bool
    is_wicketkeeper: bool
    confirmed: bool
    created_at: datetime


class SelectionCreate(BaseModel):
    player_id: UUID
    batting_position: int | None = None
    is_captain: bool = False
    is_wicketkeeper: bool = False
