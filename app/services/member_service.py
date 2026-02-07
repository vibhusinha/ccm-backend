from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ConflictError, NotFoundError
from app.models.club_member import ClubMember


class MemberService:
    def __init__(self, db: AsyncSession, club_id: UUID):
        self.db = db
        self.club_id = club_id

    async def get_all(self, *, offset: int = 0, limit: int = 20) -> list[ClubMember]:
        stmt = (
            select(ClubMember)
            .where(ClubMember.club_id == self.club_id)
            .options(selectinload(ClubMember.profile))
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, member_id: UUID) -> ClubMember | None:
        stmt = (
            select(ClubMember)
            .where(ClubMember.id == member_id, ClubMember.club_id == self.club_id)
            .options(selectinload(ClubMember.profile))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def add_member(self, user_id: UUID, role: str) -> ClubMember:
        # Check if already a member
        stmt = select(ClubMember).where(
            ClubMember.user_id == user_id, ClubMember.club_id == self.club_id
        )
        result = await self.db.execute(stmt)
        if result.scalar_one_or_none():
            raise ConflictError("User is already a member of this club")

        member = ClubMember(user_id=user_id, club_id=self.club_id, role=role)
        self.db.add(member)
        await self.db.flush()
        await self.db.refresh(member)
        return member

    async def update_role(self, member_id: UUID, role: str) -> ClubMember:
        member = await self.get_by_id(member_id)
        if not member:
            raise NotFoundError("Member not found")

        # Prevent removing last admin
        if member.role in ("clubadmin", "secretary", "treasurer") and role not in (
            "clubadmin",
            "secretary",
            "treasurer",
        ):
            stmt = select(ClubMember).where(
                ClubMember.club_id == self.club_id,
                ClubMember.role.in_(["clubadmin", "secretary", "treasurer"]),
                ClubMember.id != member_id,
            )
            result = await self.db.execute(stmt)
            if not result.scalars().first():
                raise ConflictError(
                    "Cannot remove the last administrator. Assign another admin first."
                )

        member.role = role
        await self.db.flush()
        await self.db.refresh(member)
        return member

    async def remove_member(self, member_id: UUID) -> bool:
        member = await self.get_by_id(member_id)
        if not member:
            return False

        # Prevent removing last admin
        if member.role in ("clubadmin", "secretary", "treasurer"):
            stmt = select(ClubMember).where(
                ClubMember.club_id == self.club_id,
                ClubMember.role.in_(["clubadmin", "secretary", "treasurer"]),
                ClubMember.id != member_id,
            )
            result = await self.db.execute(stmt)
            if not result.scalars().first():
                raise ConflictError(
                    "Cannot remove the last administrator. Assign another admin first."
                )

        await self.db.delete(member)
        await self.db.flush()
        return True
