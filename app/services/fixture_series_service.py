from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fixture_series import FixtureSeries
from app.services.base import BaseService


class FixtureSeriesService(BaseService[FixtureSeries]):
    def __init__(self, db: AsyncSession, club_id: UUID):
        super().__init__(model=FixtureSeries, db=db, club_id=club_id)

    async def get_all(self, *, offset: int = 0, limit: int = 50) -> list[FixtureSeries]:
        stmt = (
            self._scoped_query()
            .order_by(FixtureSeries.start_date.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
