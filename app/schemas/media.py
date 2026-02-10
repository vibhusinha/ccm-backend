from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


# --- Galleries ---

class GalleryRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    club_id: UUID
    title: str
    description: str | None
    cover_image_url: str | None
    match_id: UUID | None
    is_published: bool
    created_by: UUID | None
    created_at: datetime | None = None
    item_count: int = 0


class GalleryCreate(BaseModel):
    title: str
    description: str | None = None
    cover_image_url: str | None = None
    match_id: UUID | None = None


class GalleryUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    cover_image_url: str | None = None
    is_published: bool | None = None


# --- Media Items ---

class MediaItemRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    club_id: UUID
    gallery_id: UUID | None
    title: str | None
    description: str | None
    media_type: str
    url: str
    thumbnail_url: str | None
    uploaded_by: UUID | None
    created_at: datetime | None = None
    tags: list[str] = []


class MediaItemCreate(BaseModel):
    gallery_id: UUID | None = None
    title: str | None = None
    description: str | None = None
    media_type: str = "image"
    url: str
    thumbnail_url: str | None = None


class MediaItemUpdate(BaseModel):
    gallery_id: UUID | None = None
    title: str | None = None
    description: str | None = None
    thumbnail_url: str | None = None


# --- Tags ---

class MediaTagRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    club_id: UUID
    name: str


class MediaTagCreate(BaseModel):
    name: str


# --- Summary ---

class MediaSummary(BaseModel):
    total_galleries: int
    total_items: int
    total_tags: int
