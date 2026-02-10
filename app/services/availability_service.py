from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.match_availability import MatchAvailability
from app.models.player import Player
from app.models.team import Team
from app.models.team_selection import TeamSelection


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

    async def get_availability_summary(self, match_id: UUID) -> list[dict]:
        """Get availability for all club players for a match, with selection status."""
        players_stmt = (
            select(Player, Team.name.label("team_name"))
            .outerjoin(Team, Player.team_id == Team.id)
            .where(Player.club_id == self.club_id)
            .order_by(Player.name)
        )
        players_result = await self.db.execute(players_stmt)
        player_rows = players_result.all()

        # Availability map
        avail_stmt = select(MatchAvailability).where(MatchAvailability.match_id == match_id)
        avail_result = await self.db.execute(avail_stmt)
        avail_map = {a.player_id: a for a in avail_result.scalars().all()}

        # Selection map
        sel_stmt = select(TeamSelection.player_id).where(TeamSelection.match_id == match_id)
        sel_result = await self.db.execute(sel_stmt)
        selected_ids = {r[0] for r in sel_result.all()}

        return [
            {
                "player_id": player.id,
                "player_name": player.name,
                "player_role": player.role,
                "team_name": team_name,
                "availability_status": avail_map[player.id].status if player.id in avail_map else None,
                "is_selected": player.id in selected_ids,
            }
            for player, team_name in player_rows
        ]

    async def send_availability_requests(self, match_id: UUID) -> int:
        """Create notification stubs for players who haven't responded."""
        avail_stmt = select(MatchAvailability.player_id).where(
            MatchAvailability.match_id == match_id
        )
        avail_result = await self.db.execute(avail_stmt)
        responded_ids = {r[0] for r in avail_result.all()}

        players_stmt = select(Player).where(Player.club_id == self.club_id)
        players_result = await self.db.execute(players_stmt)
        all_players = list(players_result.scalars().all())

        sent = 0
        for player in all_players:
            if player.id not in responded_ids:
                sent += 1

        return sent
