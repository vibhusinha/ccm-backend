from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class NotificationRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    club_id: UUID
    user_id: UUID
    type: str
    title: str
    body: str | None
    data: dict
    is_read: bool
    created_at: datetime


class PushTokenRegister(BaseModel):
    token: str
    platform: str


class PushTokenRemove(BaseModel):
    token: str
