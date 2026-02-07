from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.team import Team
from app.services.base import BaseService


class TeamService(BaseService[Team]):
    def __init__(self, db: AsyncSession, club_id: UUID):
        super().__init__(model=Team, db=db, club_id=club_id)

    async def get_all(self, *, offset: int = 0, limit: int = 50) -> list[Team]:
        stmt = (
            self._scoped_query()
            .order_by(Team.display_order, Team.name)
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
