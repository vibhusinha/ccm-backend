from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.team_selection import TeamSelection


class SelectionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_for_match(self, match_id: UUID) -> list[TeamSelection]:
        stmt = select(TeamSelection).where(TeamSelection.match_id == match_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def set_selections(
        self, match_id: UUID, selections: list[dict]
    ) -> list[TeamSelection]:
        # Delete existing selections for this match
        stmt = select(TeamSelection).where(TeamSelection.match_id == match_id)
        result = await self.db.execute(stmt)
        for existing in result.scalars().all():
            await self.db.delete(existing)

        # Create new selections
        created = []
        for sel in selections:
            ts = TeamSelection(
                match_id=match_id,
                player_id=sel["player_id"],
                batting_position=sel.get("batting_position"),
                is_captain=sel.get("is_captain", False),
                is_wicketkeeper=sel.get("is_wicketkeeper", False),
            )
            self.db.add(ts)
            created.append(ts)

        await self.db.flush()
        for ts in created:
            await self.db.refresh(ts)
        return created
