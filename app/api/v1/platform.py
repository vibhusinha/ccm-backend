from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import NotFoundError
from app.core.permissions import require_platform_admin
from app.schemas.auth import CurrentUser
from app.schemas.platform import (
    AddAdminRequest,
    AuditLogEntryRead,
    BootstrapRequest,
    BootstrapResponse,
    DeleteClubRequest,
    PlatformAdminRead,
    PlatformClubRead,
    ReactivateClubRequest,
    SetupStatusResponse,
    SuspendClubRequest,
)
from app.services.platform_service import PlatformService

router = APIRouter(prefix="/platform", tags=["platform"])


@router.get("/setup-status", response_model=SetupStatusResponse)
async def get_setup_status(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SetupStatusResponse:
    """Check if platform setup is needed. Public endpoint (no auth)."""
    service = PlatformService(db)
    status = await service.get_setup_status()
    return SetupStatusResponse(**status)


@router.post("/bootstrap", response_model=BootstrapResponse)
async def bootstrap_platform(
    body: BootstrapRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BootstrapResponse:
    """Bootstrap the platform with the current user as the first admin."""
    service = PlatformService(db)
    admin = await service.bootstrap(current_user.user_id, body.platform_name)
    return BootstrapResponse(
        message="Platform setup complete. You are now the platform administrator.",
        admin_id=admin.id,
    )


@router.get("/settings")
async def get_settings(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Get platform settings. Requires platform admin."""
    require_platform_admin(current_user)
    service = PlatformService(db)
    return await service.get_settings()


@router.get("/clubs", response_model=list[PlatformClubRead])
async def list_clubs(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[PlatformClubRead]:
    """List all clubs. Requires platform admin."""
    require_platform_admin(current_user)
    service = PlatformService(db)
    clubs = await service.get_all_clubs()
    return [PlatformClubRead(**c) for c in clubs]


@router.get("/clubs/{club_id}", response_model=PlatformClubRead)
async def get_club(
    club_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PlatformClubRead:
    """Get a specific club. Requires platform admin."""
    require_platform_admin(current_user)
    service = PlatformService(db)
    club = await service.get_club(club_id)
    if not club:
        raise NotFoundError("Club not found")
    return PlatformClubRead(**club)


@router.post("/clubs/suspend")
async def suspend_club(
    body: SuspendClubRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Suspend a club. Requires platform admin."""
    require_platform_admin(current_user)
    service = PlatformService(db)
    result = await service.suspend_club(body.club_id, body.reason, current_user.user_id)
    if not result:
        raise NotFoundError("Club not found")
    return result


@router.post("/clubs/reactivate")
async def reactivate_club(
    body: ReactivateClubRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Reactivate a suspended club. Requires platform admin."""
    require_platform_admin(current_user)
    service = PlatformService(db)
    result = await service.reactivate_club(body.club_id, current_user.user_id)
    if not result:
        raise NotFoundError("Club not found")
    return result


@router.post("/clubs/delete")
async def delete_club(
    body: DeleteClubRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Soft delete a club. Requires platform admin."""
    require_platform_admin(current_user)
    service = PlatformService(db)
    result = await service.delete_club(body.club_id, body.reason, current_user.user_id)
    if not result:
        raise NotFoundError("Club not found")
    return result


@router.get("/admins", response_model=list[PlatformAdminRead])
async def list_admins(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[PlatformAdminRead]:
    """List all platform admins. Requires platform admin."""
    require_platform_admin(current_user)
    service = PlatformService(db)
    admins = await service.get_admins()
    return [PlatformAdminRead(**a) for a in admins]


@router.post("/admins", response_model=PlatformAdminRead)
async def add_admin(
    body: AddAdminRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PlatformAdminRead:
    """Add a platform admin. Requires platform admin."""
    require_platform_admin(current_user)
    service = PlatformService(db)
    admin = await service.add_admin(body.user_id, current_user.user_id)

    # Fetch profile for the response
    from app.models.profile import Profile
    from sqlalchemy import select

    result = await db.execute(select(Profile).where(Profile.id == admin.user_id))
    profile = result.scalar_one_or_none()

    return PlatformAdminRead(
        id=admin.id,
        user_id=admin.user_id,
        email=profile.email if profile else "",
        full_name=profile.full_name if profile else None,
        is_active=admin.is_active,
        permissions_list=["manage_clubs", "view_analytics"],
        created_at=admin.created_at,
        last_login_at=None,
    )


@router.delete("/admins/{admin_id}")
async def remove_admin(
    admin_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Remove a platform admin. Requires platform admin."""
    require_platform_admin(current_user)
    service = PlatformService(db)
    success = await service.remove_admin(admin_id, current_user.user_id)
    if not success:
        raise NotFoundError("Admin not found")
    return {"message": "Admin removed"}


@router.get("/audit-log", response_model=list[AuditLogEntryRead])
async def get_audit_log(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(50, ge=1, le=500),
) -> list[AuditLogEntryRead]:
    """Get audit log entries. Requires platform admin."""
    require_platform_admin(current_user)
    service = PlatformService(db)
    entries = await service.get_audit_log(limit)
    return [AuditLogEntryRead(**e) for e in entries]
