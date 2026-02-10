from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import AuthenticationError, ForbiddenError
from app.core.security import decode_access_token
from app.schemas.auth import ClubMembership, CurrentUser


async def get_current_user(
    authorization: Annotated[str, Header()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CurrentUser:
    """Extract and validate JWT access token. Look up club memberships."""
    if not authorization.startswith("Bearer "):
        raise AuthenticationError("Invalid authorization header")

    token = authorization[7:]
    payload = decode_access_token(token)

    user_id = UUID(payload["sub"])
    email = payload.get("email", "")

    # Look up profile (registration handles creation)
    from app.models.profile import Profile

    result = await db.execute(select(Profile).where(Profile.id == user_id))
    profile = result.scalar_one_or_none()
    if profile is None:
        raise AuthenticationError("User profile not found")

    # Check if platform admin
    from app.models.platform_admin import PlatformAdmin

    result = await db.execute(
        select(PlatformAdmin).where(
            PlatformAdmin.user_id == user_id, PlatformAdmin.is_active.is_(True)
        )
    )
    is_platform_admin = result.scalar_one_or_none() is not None

    # Get all club memberships
    from app.models.club_member import ClubMember

    result = await db.execute(select(ClubMember).where(ClubMember.user_id == user_id))
    memberships = result.scalars().all()

    return CurrentUser(
        user_id=user_id,
        email=email,
        is_platform_admin=is_platform_admin,
        memberships=[
            ClubMembership(
                club_id=m.club_id,
                role=m.role,
                member_id=m.id,
            )
            for m in memberships
        ],
    )


def require_club_membership(current_user: CurrentUser, club_id: UUID) -> ClubMembership:
    """Verify user is a member of the specified club."""
    if current_user.is_platform_admin:
        return ClubMembership(club_id=club_id, role="super_admin", member_id=None)

    for m in current_user.memberships:
        if m.club_id == club_id:
            return m

    raise ForbiddenError("You are not a member of this club")
