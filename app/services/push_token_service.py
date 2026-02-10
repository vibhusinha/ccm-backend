from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.push_token import PushToken


class PushTokenService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, user_id: UUID, token: str, platform: str) -> bool:
        stmt = select(PushToken).where(
            PushToken.user_id == user_id, PushToken.token == token
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.platform = platform
        else:
            push_token = PushToken(user_id=user_id, token=token, platform=platform)
            self.db.add(push_token)

        await self.db.flush()
        return True

    async def remove(self, user_id: UUID, token: str) -> bool:
        stmt = select(PushToken).where(
            PushToken.user_id == user_id, PushToken.token == token
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            await self.db.delete(existing)
            await self.db.flush()
            return True
        return False
