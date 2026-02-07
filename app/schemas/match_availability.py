from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

AVAILABILITY_STATUS_PATTERN = "^(available|unavailable|pending)$"


class AvailabilityRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    match_id: UUID
    player_id: UUID
    status: str
    updated_at: datetime


class AvailabilityUpdate(BaseModel):
    status: str = Field(..., pattern=AVAILABILITY_STATUS_PATTERN)


class BulkAvailabilityUpdate(BaseModel):
    match_ids: list[UUID]
    status: str = Field(..., pattern=AVAILABILITY_STATUS_PATTERN)
