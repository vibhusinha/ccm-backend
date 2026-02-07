from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ClubRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    name: str
    slug: str
    logo_url: str | None
    primary_color: str
    secondary_color: str
    accent_color: str
    logo_storage_path: str | None
    subscription_tier: str
    stripe_customer_id: str | None
    created_at: datetime
    updated_at: datetime


class ClubUpdate(BaseModel):
    name: str | None = None
    logo_url: str | None = None
    primary_color: str | None = None
    secondary_color: str | None = None
    accent_color: str | None = None
