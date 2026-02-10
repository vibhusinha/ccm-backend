from uuid import UUID

from sqlalchemy import Column, ForeignKey, Table, func, select
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base
from app.models.media_gallery import MediaGallery
from app.models.media_item import MediaItem
from app.models.media_tag import MediaTag
from app.services.base import BaseService

# Association table reference
media_item_tags = Table(
    "media_item_tags",
    Base.metadata,
    Column("media_item_id", PGUUID(as_uuid=True), ForeignKey("media_items.id"), primary_key=True),
    Column("media_tag_id", PGUUID(as_uuid=True), ForeignKey("media_tags.id"), primary_key=True),
    extend_existing=True,
)


class MediaGalleryService(BaseService[MediaGallery]):
    def __init__(self, db: AsyncSession, club_id: UUID):
        super().__init__(model=MediaGallery, db=db, club_id=club_id)

    async def get_all_with_counts(self) -> list[dict]:
        stmt = (
            select(
                MediaGallery,
                func.count(MediaItem.id).label("item_count"),
            )
            .outerjoin(MediaItem, MediaGallery.id == MediaItem.gallery_id)
            .where(MediaGallery.club_id == self.club_id)
            .group_by(MediaGallery.id)
            .order_by(MediaGallery.created_at.desc())
        )
        result = await self.db.execute(stmt)
        rows = result.all()
        return [
            {
                **{c.key: getattr(gallery, c.key) for c in MediaGallery.__table__.columns},
                "item_count": item_count,
            }
            for gallery, item_count in rows
        ]

    async def get_with_count(self, gallery_id: UUID) -> dict | None:
        stmt = (
            select(
                MediaGallery,
                func.count(MediaItem.id).label("item_count"),
            )
            .outerjoin(MediaItem, MediaGallery.id == MediaItem.gallery_id)
            .where(MediaGallery.id == gallery_id)
            .group_by(MediaGallery.id)
        )
        result = await self.db.execute(stmt)
        row = result.one_or_none()
        if not row:
            return None
        gallery, item_count = row
        return {
            **{c.key: getattr(gallery, c.key) for c in MediaGallery.__table__.columns},
            "item_count": item_count,
        }

    async def create(self, *, created_by: UUID, **kwargs) -> MediaGallery:
        return await super().create(created_by=created_by, **kwargs)


class MediaItemService(BaseService[MediaItem]):
    def __init__(self, db: AsyncSession, club_id: UUID):
        super().__init__(model=MediaItem, db=db, club_id=club_id)

    async def get_all_with_tags(self, gallery_id: UUID | None = None) -> list[dict]:
        stmt = self._scoped_query().order_by(MediaItem.created_at.desc())
        if gallery_id:
            stmt = stmt.where(MediaItem.gallery_id == gallery_id)
        result = await self.db.execute(stmt)
        items = list(result.scalars().all())

        items_data = []
        for item in items:
            tags = await self._get_tags(item.id)
            items_data.append({
                **{c.key: getattr(item, c.key) for c in MediaItem.__table__.columns},
                "tags": tags,
            })
        return items_data

    async def get_with_tags(self, item_id: UUID) -> dict | None:
        item = await self.get_by_id(item_id)
        if not item:
            return None
        tags = await self._get_tags(item.id)
        return {
            **{c.key: getattr(item, c.key) for c in MediaItem.__table__.columns},
            "tags": tags,
        }

    async def create(self, *, uploaded_by: UUID, **kwargs) -> MediaItem:
        return await super().create(uploaded_by=uploaded_by, **kwargs)

    async def _get_tags(self, item_id: UUID) -> list[str]:
        stmt = (
            select(MediaTag.name)
            .join(media_item_tags, MediaTag.id == media_item_tags.c.media_tag_id)
            .where(media_item_tags.c.media_item_id == item_id)
        )
        result = await self.db.execute(stmt)
        return [r[0] for r in result.all()]


class MediaTagService(BaseService[MediaTag]):
    def __init__(self, db: AsyncSession, club_id: UUID):
        super().__init__(model=MediaTag, db=db, club_id=club_id)

    async def get_all(self, *, offset: int = 0, limit: int = 100) -> list[MediaTag]:
        stmt = self._scoped_query().order_by(MediaTag.name)
        stmt = stmt.offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_summary(self) -> dict:
        galleries = (await self.db.execute(
            select(func.count()).where(MediaGallery.club_id == self.club_id)
        )).scalar_one()
        items = (await self.db.execute(
            select(func.count()).where(MediaItem.club_id == self.club_id)
        )).scalar_one()
        tags = (await self.db.execute(
            select(func.count()).where(MediaTag.club_id == self.club_id)
        )).scalar_one()
        return {
            "total_galleries": galleries,
            "total_items": items,
            "total_tags": tags,
        }
