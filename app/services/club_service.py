from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.club import Club


class ClubService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, club_id: UUID) -> Club | None:
        result = await self.db.execute(select(Club).where(Club.id == club_id))
        return result.scalar_one_or_none()

    async def get_clubs_for_user(self, user_id: UUID) -> list[Club]:
        from app.models.club_member import ClubMember

        stmt = (
            select(Club)
            .join(ClubMember, ClubMember.club_id == Club.id)
            .where(ClubMember.user_id == user_id)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update(self, club_id: UUID, **kwargs) -> Club | None:
        club = await self.get_by_id(club_id)
        if not club:
            return None
        for key, value in kwargs.items():
            if value is not None:
                setattr(club, key, value)
        await self.db.flush()
        await self.db.refresh(club)
        return club
