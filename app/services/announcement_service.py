from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.announcement import Announcement
from app.services.base import BaseService


class AnnouncementService(BaseService[Announcement]):
    def __init__(self, db: AsyncSession, club_id: UUID):
        super().__init__(model=Announcement, db=db, club_id=club_id)

    async def get_all(
        self,
        *,
        offset: int = 0,
        limit: int = 50,
        include_archived: bool = False,
    ) -> list[Announcement]:
        stmt = self._scoped_query().order_by(Announcement.created_at.desc())
        if not include_archived:
            stmt = stmt.where(Announcement.is_archived.is_(False))
        stmt = stmt.offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create(self, *, created_by: UUID, **kwargs) -> Announcement:  # type: ignore[override]
        return await super().create(created_by=created_by, **kwargs)
