from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.auth import CurrentUser, MeResponse
from app.services.profile_service import ProfileService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=MeResponse)
async def get_me(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MeResponse:
    profile_service = ProfileService(db)
    profile = await profile_service.get_by_id(current_user.user_id)

    return MeResponse(
        user_id=current_user.user_id,
        email=current_user.email,
        full_name=profile.full_name if profile else None,
        avatar_url=profile.avatar_url if profile else None,
        is_platform_admin=current_user.is_platform_admin,
        clubs=current_user.memberships,
    )
