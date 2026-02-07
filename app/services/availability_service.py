from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.match_availability import MatchAvailability
from app.models.player import Player


class AvailabilityService:
    def __init__(self, db: AsyncSession, club_id: UUID):
        self.db = db
        self.club_id = club_id

    async def get_for_match(self, match_id: UUID) -> list[MatchAvailability]:
        stmt = select(MatchAvailability).where(MatchAvailability.match_id == match_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def set_availability(
        self, match_id: UUID, player_id: UUID, status: str
    ) -> MatchAvailability:
        stmt = select(MatchAvailability).where(
            MatchAvailability.match_id == match_id,
            MatchAvailability.player_id == player_id,
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.status = status
            await self.db.flush()
            await self.db.refresh(existing)
            return existing

        avail = MatchAvailability(match_id=match_id, player_id=player_id, status=status)
        self.db.add(avail)
        await self.db.flush()
        await self.db.refresh(avail)
        return avail

    async def bulk_set(self, match_ids: list[UUID], user_id: UUID, status: str) -> int:
        # Find the player for this user in this club
        stmt = select(Player).where(Player.club_id == self.club_id, Player.user_id == user_id)
        result = await self.db.execute(stmt)
        player = result.scalar_one_or_none()
        if not player:
            return 0

        count = 0
        for match_id in match_ids:
            await self.set_availability(match_id, player.id, status)
            count += 1
        return count
