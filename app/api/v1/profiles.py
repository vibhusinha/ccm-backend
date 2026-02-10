from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import ForbiddenError, NotFoundError
from app.schemas.auth import CurrentUser
from app.schemas.profile import AvatarResponse, AvatarUpload, ProfileRead, ProfileUpdate
from app.services.profile_service import ProfileService

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("/{user_id}", response_model=ProfileRead)
async def get_profile(
    user_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProfileRead:
    service = ProfileService(db)
    profile = await service.get_by_id(user_id)
    if not profile:
        raise NotFoundError("Profile not found")
    return ProfileRead.model_validate(profile)


@router.patch("/{user_id}", response_model=ProfileRead)
async def update_profile(
    user_id: Annotated[UUID, Path()],
    body: ProfileUpdate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProfileRead:
    if current_user.user_id != user_id and not current_user.is_platform_admin:
        raise ForbiddenError("You can only update your own profile")
    service = ProfileService(db)
    profile = await service.update(user_id, **body.model_dump(exclude_unset=True))
    return ProfileRead.model_validate(profile)


@router.post("/{user_id}/avatar", response_model=AvatarResponse)
async def upload_avatar(
    user_id: Annotated[UUID, Path()],
    body: AvatarUpload,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AvatarResponse:
    if current_user.user_id != user_id and not current_user.is_platform_admin:
        raise ForbiddenError("You can only update your own avatar")
    service = ProfileService(db)
    profile = await service.upload_avatar(user_id, body.image_data, body.mime_type)
    return AvatarResponse(avatar_url=profile.avatar_url)


@router.delete("/{user_id}/avatar", response_model=AvatarResponse)
async def delete_avatar(
    user_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AvatarResponse:
    if current_user.user_id != user_id and not current_user.is_platform_admin:
        raise ForbiddenError("You can only delete your own avatar")
    service = ProfileService(db)
    profile = await service.delete_avatar(user_id)
    return AvatarResponse(avatar_url=profile.avatar_url)
