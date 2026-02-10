from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import NotFoundError
from app.core.permissions import require_admin, require_member
from app.schemas.auth import CurrentUser
from app.schemas.media import (
    GalleryCreate,
    GalleryRead,
    GalleryUpdate,
    MediaItemCreate,
    MediaItemRead,
    MediaItemUpdate,
    MediaSummary,
    MediaTagCreate,
    MediaTagRead,
)
from app.services.media_service import MediaGalleryService, MediaItemService, MediaTagService

# Club-scoped routes
club_router = APIRouter(prefix="/clubs/{club_id}/media", tags=["media"])

# Gallery-scoped routes
gallery_router = APIRouter(prefix="/media/galleries/{gallery_id}", tags=["media"])

# Non-club-scoped gallery routes (for update/delete)
gallery_action_router = APIRouter(prefix="/media/galleries/{id}", tags=["media"])

# Item-scoped routes
item_router = APIRouter(prefix="/media/items/{item_id}", tags=["media"])

# Tag action routes
tag_router = APIRouter(prefix="/media/tags/{tag_id}", tags=["media"])


async def _get_gallery_club_id(gallery_id: UUID, db: AsyncSession) -> UUID:
    from app.models.media_gallery import MediaGallery
    from sqlalchemy import select

    stmt = select(MediaGallery.club_id).where(MediaGallery.id == gallery_id)
    result = await db.execute(stmt)
    club_id = result.scalar_one_or_none()
    if club_id is None:
        raise NotFoundError("Gallery not found")
    return club_id


async def _get_item_club_id(item_id: UUID, db: AsyncSession) -> UUID:
    from app.models.media_item import MediaItem
    from sqlalchemy import select

    stmt = select(MediaItem.club_id).where(MediaItem.id == item_id)
    result = await db.execute(stmt)
    club_id = result.scalar_one_or_none()
    if club_id is None:
        raise NotFoundError("Media item not found")
    return club_id


async def _get_tag_club_id(tag_id: UUID, db: AsyncSession) -> UUID:
    from app.models.media_tag import MediaTag
    from sqlalchemy import select

    stmt = select(MediaTag.club_id).where(MediaTag.id == tag_id)
    result = await db.execute(stmt)
    club_id = result.scalar_one_or_none()
    if club_id is None:
        raise NotFoundError("Tag not found")
    return club_id


# --- Galleries ---

@club_router.get("/galleries", response_model=list[GalleryRead])
async def list_galleries(
    club_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[GalleryRead]:
    require_member(current_user, club_id)
    service = MediaGalleryService(db, club_id)
    galleries = await service.get_all_with_counts()
    return [GalleryRead(**g) for g in galleries]


@club_router.post("/galleries", response_model=GalleryRead, status_code=201)
async def create_gallery(
    club_id: Annotated[UUID, Path()],
    body: GalleryCreate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> GalleryRead:
    require_admin(current_user, club_id)
    service = MediaGalleryService(db, club_id)
    gallery = await service.create(created_by=current_user.user_id, **body.model_dump())
    return GalleryRead.model_validate(gallery)


@gallery_router.get("/", response_model=GalleryRead)
async def get_gallery(
    gallery_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> GalleryRead:
    club_id = await _get_gallery_club_id(gallery_id, db)
    require_member(current_user, club_id)
    service = MediaGalleryService(db, club_id)
    gallery = await service.get_with_count(gallery_id)
    if not gallery:
        raise NotFoundError("Gallery not found")
    return GalleryRead(**gallery)


@gallery_router.patch("/", response_model=GalleryRead)
async def update_gallery(
    gallery_id: Annotated[UUID, Path()],
    body: GalleryUpdate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> GalleryRead:
    club_id = await _get_gallery_club_id(gallery_id, db)
    require_admin(current_user, club_id)
    service = MediaGalleryService(db, club_id)
    gallery = await service.update(gallery_id, **body.model_dump(exclude_unset=True))
    if not gallery:
        raise NotFoundError("Gallery not found")
    return GalleryRead.model_validate(gallery)


@gallery_router.delete("/", status_code=204)
async def delete_gallery(
    gallery_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    club_id = await _get_gallery_club_id(gallery_id, db)
    require_admin(current_user, club_id)
    service = MediaGalleryService(db, club_id)
    if not await service.delete(gallery_id):
        raise NotFoundError("Gallery not found")


@gallery_router.get("/items", response_model=list[MediaItemRead])
async def list_gallery_items(
    gallery_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[MediaItemRead]:
    club_id = await _get_gallery_club_id(gallery_id, db)
    require_member(current_user, club_id)
    service = MediaItemService(db, club_id)
    items = await service.get_all_with_tags(gallery_id=gallery_id)
    return [MediaItemRead(**i) for i in items]


# --- Media Items ---

@club_router.get("/items", response_model=list[MediaItemRead])
async def list_items(
    club_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[MediaItemRead]:
    require_member(current_user, club_id)
    service = MediaItemService(db, club_id)
    items = await service.get_all_with_tags()
    return [MediaItemRead(**i) for i in items]


@club_router.post("/items", response_model=MediaItemRead, status_code=201)
async def create_item(
    club_id: Annotated[UUID, Path()],
    body: MediaItemCreate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MediaItemRead:
    require_admin(current_user, club_id)
    service = MediaItemService(db, club_id)
    item = await service.create(uploaded_by=current_user.user_id, **body.model_dump())
    return MediaItemRead.model_validate(item)


@item_router.get("/", response_model=MediaItemRead)
async def get_item(
    item_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MediaItemRead:
    club_id = await _get_item_club_id(item_id, db)
    require_member(current_user, club_id)
    service = MediaItemService(db, club_id)
    item = await service.get_with_tags(item_id)
    if not item:
        raise NotFoundError("Media item not found")
    return MediaItemRead(**item)


@item_router.patch("/", response_model=MediaItemRead)
async def update_item(
    item_id: Annotated[UUID, Path()],
    body: MediaItemUpdate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MediaItemRead:
    club_id = await _get_item_club_id(item_id, db)
    require_admin(current_user, club_id)
    service = MediaItemService(db, club_id)
    item = await service.update(item_id, **body.model_dump(exclude_unset=True))
    if not item:
        raise NotFoundError("Media item not found")
    return MediaItemRead.model_validate(item)


@item_router.delete("/", status_code=204)
async def delete_item(
    item_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    club_id = await _get_item_club_id(item_id, db)
    require_admin(current_user, club_id)
    service = MediaItemService(db, club_id)
    if not await service.delete(item_id):
        raise NotFoundError("Media item not found")


# --- Tags ---

@club_router.get("/tags", response_model=list[MediaTagRead])
async def list_tags(
    club_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[MediaTagRead]:
    require_member(current_user, club_id)
    service = MediaTagService(db, club_id)
    tags = await service.get_all()
    return [MediaTagRead.model_validate(t) for t in tags]


@club_router.post("/tags", response_model=MediaTagRead, status_code=201)
async def create_tag(
    club_id: Annotated[UUID, Path()],
    body: MediaTagCreate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MediaTagRead:
    require_admin(current_user, club_id)
    service = MediaTagService(db, club_id)
    tag = await service.create(name=body.name)
    return MediaTagRead.model_validate(tag)


@tag_router.delete("/", status_code=204)
async def delete_tag(
    tag_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    club_id = await _get_tag_club_id(tag_id, db)
    require_admin(current_user, club_id)
    service = MediaTagService(db, club_id)
    if not await service.delete(tag_id):
        raise NotFoundError("Tag not found")


# --- Summary ---

@club_router.get("/summary", response_model=MediaSummary)
async def get_summary(
    club_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MediaSummary:
    require_member(current_user, club_id)
    service = MediaTagService(db, club_id)
    summary = await service.get_summary()
    return MediaSummary(**summary)
