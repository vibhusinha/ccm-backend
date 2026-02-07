from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fixture_type import FixtureType
from app.services.base import BaseService


class FixtureTypeService(BaseService[FixtureType]):
    def __init__(self, db: AsyncSession, club_id: UUID):
        super().__init__(model=FixtureType, db=db, club_id=club_id)

    async def get_all(self, *, offset: int = 0, limit: int = 50) -> list[FixtureType]:
        stmt = (
            self._scoped_query()
            .order_by(FixtureType.display_order, FixtureType.name)
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
