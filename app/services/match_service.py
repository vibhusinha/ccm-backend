from datetime import date
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.match import Match
from app.services.base import BaseService


class MatchService(BaseService[Match]):
    def __init__(self, db: AsyncSession, club_id: UUID):
        super().__init__(model=Match, db=db, club_id=club_id)

    async def get_all(self, *, offset: int = 0, limit: int = 50) -> list[Match]:
        stmt = (
            self._scoped_query()
            .options(selectinload(Match.team))
            .order_by(Match.date.asc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_upcoming(self, limit: int = 10) -> list[Match]:
        stmt = (
            self._scoped_query()
            .where(Match.date >= date.today(), Match.status.in_(["upcoming", "in-progress"]))
            .options(selectinload(Match.team))
            .order_by(Match.date.asc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_with_details(self, match_id: UUID) -> Match | None:
        stmt = (
            self._scoped_query()
            .where(Match.id == match_id)
            .options(
                selectinload(Match.team),
                selectinload(Match.availability),
                selectinload(Match.selections),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def cancel(self, match_id: UUID) -> Match | None:
        return await self.update(match_id, status="cancelled")
