from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ProfileRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    email: str
    full_name: str | None
    avatar_url: str | None
    phone: str | None
    created_at: datetime
    updated_at: datetime


class ProfileUpdate(BaseModel):
    full_name: str | None = None
    avatar_url: str | None = None
    phone: str | None = None
