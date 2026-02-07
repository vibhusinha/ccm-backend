from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.player import Player
from app.services.base import BaseService


class PlayerService(BaseService[Player]):
    def __init__(self, db: AsyncSession, club_id: UUID):
        super().__init__(model=Player, db=db, club_id=club_id)

    async def get_all(self, *, offset: int = 0, limit: int = 50) -> list[Player]:
        stmt = self._scoped_query().order_by(Player.name).offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_team(self, team_id: UUID) -> list[Player]:
        stmt = self._scoped_query().where(Player.team_id == team_id).order_by(Player.name)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
