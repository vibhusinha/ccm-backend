from uuid import UUID

from app.core.exceptions import ForbiddenError
from app.schemas.auth import CurrentUser

ADMIN_ROLES = {"clubadmin", "secretary", "treasurer"}
SELECTION_ROLES = ADMIN_ROLES | {"captain", "vice_captain"}
ALL_MEMBER_ROLES = SELECTION_ROLES | {"player", "sponsor"}


def require_platform_admin(current_user: CurrentUser) -> None:
    """Check that the user is a platform admin."""
    if not current_user.is_platform_admin:
        raise ForbiddenError("Platform admin access required")


def require_role(
    current_user: CurrentUser,
    club_id: UUID,
    allowed_roles: set[str],
) -> dict:
    """Check that the user has one of the allowed roles for the given club."""
    if current_user.is_platform_admin:
        return {"club_id": club_id, "role": "super_admin", "member_id": None}

    for m in current_user.memberships:
        if m.club_id == club_id and m.role in allowed_roles:
            return {"club_id": club_id, "role": m.role, "member_id": m.member_id}

    raise ForbiddenError(f"Requires one of: {', '.join(sorted(allowed_roles))}")


def require_member(current_user: CurrentUser, club_id: UUID) -> dict:
    return require_role(current_user, club_id, ALL_MEMBER_ROLES | {"super_admin"})


def require_admin(current_user: CurrentUser, club_id: UUID) -> dict:
    return require_role(current_user, club_id, ADMIN_ROLES | {"super_admin"})


def require_admin_or_captain(current_user: CurrentUser, club_id: UUID) -> dict:
    return require_role(current_user, club_id, SELECTION_ROLES | {"super_admin"})
