from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.season import Season
from app.services.base import BaseService


class SeasonService(BaseService[Season]):
    def __init__(self, db: AsyncSession, club_id: UUID):
        super().__init__(model=Season, db=db, club_id=club_id)

    async def get_all(self, *, offset: int = 0, limit: int = 50) -> list[Season]:
        stmt = self._scoped_query().order_by(Season.start_date.desc()).offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def set_current(self, season_id: UUID) -> Season | None:
        # Unset all current seasons for this club
        stmt = select(Season).where(Season.club_id == self.club_id, Season.is_current.is_(True))
        result = await self.db.execute(stmt)
        for season in result.scalars().all():
            season.is_current = False

        # Set the target season as current
        target = await self.get_by_id(season_id)
        if not target:
            return None
        target.is_current = True
        target.status = "active"
        await self.db.flush()
        await self.db.refresh(target)
        return target
