from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import NotFoundError
from app.core.permissions import require_admin, require_platform_admin
from app.models.club_member import ClubMember
from app.schemas.auth import CurrentUser
from app.schemas.role import (
    ChangeRoleRequest,
    PermissionRead,
    RoleCreate,
    RoleRead,
    RoleUpdate,
    RoleWithPermissionsRead,
    SingleAdminCheckResponse,
    UserPermissionsResponse,
)
from app.services.member_service import MemberService
from app.services.role_service import RoleService

router = APIRouter(prefix="/roles", tags=["roles"])
permissions_router = APIRouter(prefix="/permissions", tags=["permissions"])
user_perms_router = APIRouter(prefix="/users", tags=["roles"])
members_router = APIRouter(tags=["roles"])
clubs_roles_router = APIRouter(tags=["roles"])


# ── Roles CRUD ──────────────────────────────────────────────────────


@router.get("/", response_model=list[RoleRead])
async def list_roles(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[RoleRead]:
    service = RoleService(db)
    roles = await service.get_all_active()
    return [RoleRead.model_validate(r) for r in roles]


@router.get("/with-permissions", response_model=list[RoleWithPermissionsRead])
async def list_roles_with_permissions(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[RoleWithPermissionsRead]:
    require_platform_admin(current_user)
    service = RoleService(db)
    roles = await service.get_all_with_permissions()
    return [RoleWithPermissionsRead.model_validate(r) for r in roles]


@router.get("/{role_id}", response_model=RoleWithPermissionsRead)
async def get_role(
    role_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RoleWithPermissionsRead:
    service = RoleService(db)
    role = await service.get_by_id(role_id)
    if not role:
        raise NotFoundError("Role not found")
    return RoleWithPermissionsRead.model_validate(role)


@router.post("/", response_model=RoleWithPermissionsRead, status_code=201)
async def create_role(
    body: RoleCreate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RoleWithPermissionsRead:
    require_platform_admin(current_user)
    service = RoleService(db)
    role = await service.create_role(
        name=body.name,
        display_name=body.display_name,
        description=body.description,
        hierarchy_level=body.hierarchy_level,
        permission_keys=body.permission_keys,
    )
    role = await service.get_by_id(role.id)
    return RoleWithPermissionsRead.model_validate(role)


@router.patch("/{role_id}", response_model=RoleWithPermissionsRead)
async def update_role(
    role_id: Annotated[UUID, Path()],
    body: RoleUpdate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RoleWithPermissionsRead:
    require_platform_admin(current_user)
    service = RoleService(db)
    await service.update_role(
        role_id,
        display_name=body.display_name,
        description=body.description,
        hierarchy_level=body.hierarchy_level,
        is_active=body.is_active,
        permission_keys=body.permission_keys,
    )
    role = await service.get_by_id(role_id)
    return RoleWithPermissionsRead.model_validate(role)


@router.delete("/{role_id}", status_code=204)
async def delete_role(
    role_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    require_platform_admin(current_user)
    service = RoleService(db)
    if not await service.delete_role(role_id):
        raise NotFoundError("Role not found")


# ── Permissions ─────────────────────────────────────────────────────

PERMISSION_DEFINITIONS = [
    {"key": "manage_club", "name": "Manage Club", "description": "Full club settings management", "category": "club"},
    {"key": "manage_subscription", "name": "Manage Subscription", "description": "Manage club subscription", "category": "club"},
    {"key": "manage_members", "name": "Manage Members", "description": "Add, remove, manage members", "category": "members"},
    {"key": "assign_roles", "name": "Assign Roles", "description": "Change member roles", "category": "members"},
    {"key": "manage_teams", "name": "Manage Teams", "description": "Create and manage teams", "category": "teams"},
    {"key": "select_team", "name": "Select Team", "description": "Make team selections", "category": "teams"},
    {"key": "manage_matches", "name": "Manage Matches", "description": "Create and manage matches", "category": "matches"},
    {"key": "edit_matches", "name": "Edit Matches", "description": "Edit match details and scores", "category": "matches"},
    {"key": "manage_tasks", "name": "Manage Tasks", "description": "Create and assign tasks", "category": "tasks"},
    {"key": "set_availability", "name": "Set Availability", "description": "Set own match availability", "category": "availability"},
    {"key": "view_availability", "name": "View Availability", "description": "View all members availability", "category": "availability"},
    {"key": "manage_payments", "name": "Manage Payments", "description": "Track and manage payments", "category": "finance"},
    {"key": "send_messages", "name": "Send Messages", "description": "Send messages to members", "category": "communication"},
    {"key": "manage_messages", "name": "Manage Messages", "description": "Manage all messaging", "category": "communication"},
    {"key": "view_messages", "name": "View Messages", "description": "View messages", "category": "communication"},
    {"key": "view_stats", "name": "View Stats", "description": "View statistics", "category": "analytics"},
    {"key": "view_reports", "name": "View Reports", "description": "View club reports", "category": "analytics"},
    {"key": "export_data", "name": "Export Data", "description": "Export club data", "category": "analytics"},
    {"key": "manage_merchandise", "name": "Manage Merchandise", "description": "Manage club merchandise", "category": "merchandise"},
]


@permissions_router.get("/", response_model=list[PermissionRead])
async def list_permissions(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[PermissionRead]:
    require_platform_admin(current_user)
    return [PermissionRead(**p) for p in PERMISSION_DEFINITIONS]


# ── User permissions for club ───────────────────────────────────────


@user_perms_router.get(
    "/{user_id}/clubs/{club_id}/permissions",
    response_model=UserPermissionsResponse,
)
async def get_user_permissions(
    user_id: Annotated[UUID, Path()],
    club_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserPermissionsResponse:
    if current_user.user_id != user_id and not current_user.is_platform_admin:
        require_admin(current_user, club_id)
    service = RoleService(db)
    result = await service.get_user_permissions(user_id, club_id)
    return UserPermissionsResponse(**result)


# ── Change member role ──────────────────────────────────────────────


@members_router.post("/members/{member_id}/change-role", response_model=dict)
async def change_member_role(
    member_id: Annotated[UUID, Path()],
    body: ChangeRoleRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    result = await db.execute(select(ClubMember).where(ClubMember.id == member_id))
    member = result.scalar_one_or_none()
    if not member:
        raise NotFoundError("Member not found")

    require_admin(current_user, member.club_id)
    service = MemberService(db, member.club_id)
    updated = await service.update_role(member_id, body.new_role)
    return {"id": str(updated.id), "role": updated.role}


# ── Club single admin check ────────────────────────────────────────


@clubs_roles_router.get(
    "/clubs/{club_id}/has-single-admin",
    response_model=SingleAdminCheckResponse,
)
async def check_single_admin(
    club_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SingleAdminCheckResponse:
    require_admin(current_user, club_id)
    service = RoleService(db)
    result = await service.has_single_admin(club_id)
    return SingleAdminCheckResponse(**result)
