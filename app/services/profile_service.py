from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.profile import Profile


class ProfileService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: UUID) -> Profile | None:
        result = await self.db.execute(select(Profile).where(Profile.id == user_id))
        return result.scalar_one_or_none()

    async def update(self, user_id: UUID, **kwargs) -> Profile:
        profile = await self.get_by_id(user_id)
        if not profile:
            raise NotFoundError("Profile not found")
        for key, value in kwargs.items():
            if value is not None:
                setattr(profile, key, value)
        await self.db.flush()
        await self.db.refresh(profile)
        return profile

    async def upload_avatar(self, user_id: UUID, image_data: str, mime_type: str) -> Profile:
        profile = await self.get_by_id(user_id)
        if not profile:
            raise NotFoundError("Profile not found")
        if len(image_data) > 2_800_000:
            raise ValueError("Image too large. Maximum size is approximately 2MB.")
        data_uri = f"data:{mime_type};base64,{image_data}"
        profile.avatar_url = data_uri
        await self.db.flush()
        await self.db.refresh(profile)
        return profile

    async def delete_avatar(self, user_id: UUID) -> Profile:
        profile = await self.get_by_id(user_id)
        if not profile:
            raise NotFoundError("Profile not found")
        profile.avatar_url = None
        await self.db.flush()
        await self.db.refresh(profile)
        return profile
