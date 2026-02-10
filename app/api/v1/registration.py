from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.permissions import require_admin, require_platform_admin
from app.models.registration_request import RegistrationRequest
from app.schemas.auth import CurrentUser
from app.schemas.registration import (
    ApproveClubRequest,
    ApproveRegistrationRequest,
    ApprovedClubRead,
    PendingClubRegistrationRead,
    PendingClubWithUserRead,
    RejectClubRequest,
    RejectRegistrationRequest,
    RegistrationRequestRead,
    RegistrationStatusRead,
    SubmitClubRequest,
    UpdateRequestedClubRequest,
)
from app.services.registration_service import RegistrationService

router = APIRouter(prefix="/registration", tags=["registration"])
club_registrations_router = APIRouter(tags=["registration"])


@router.get("/approved-clubs", response_model=list[ApprovedClubRead])
async def list_approved_clubs(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[ApprovedClubRead]:
    """List all active clubs. Public endpoint — no auth required."""
    service = RegistrationService(db)
    clubs = await service.get_approved_clubs()
    return [ApprovedClubRead(**c) for c in clubs]


@router.get("/my-status", response_model=RegistrationStatusRead)
async def get_my_status(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RegistrationStatusRead:
    service = RegistrationService(db)
    result = await service.get_my_status(current_user.user_id)
    return RegistrationStatusRead(**result)


@router.get("/all-pending", response_model=list[RegistrationRequestRead])
async def get_all_pending(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[RegistrationRequestRead]:
    require_platform_admin(current_user)
    service = RegistrationService(db)
    requests = await service.get_all_pending()
    return [RegistrationRequestRead(**r) for r in requests]


@router.get("/pending-clubs", response_model=list[PendingClubRegistrationRead])
async def get_pending_clubs(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[PendingClubRegistrationRead]:
    require_platform_admin(current_user)
    service = RegistrationService(db)
    clubs = await service.get_pending_clubs()
    return [PendingClubRegistrationRead.model_validate(c) for c in clubs]


@router.get("/pending-clubs-with-users", response_model=list[PendingClubWithUserRead])
async def get_pending_clubs_with_users(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[PendingClubWithUserRead]:
    require_platform_admin(current_user)
    service = RegistrationService(db)
    clubs = await service.get_pending_clubs_with_users()
    return [PendingClubWithUserRead(**c) for c in clubs]


@router.post("/update-requested-club")
async def update_requested_club(
    body: UpdateRequestedClubRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    service = RegistrationService(db)
    req = await service.update_requested_club(current_user.user_id, body.club_id)
    return {"id": str(req.id), "club_id": str(req.club_id), "status": req.status}


@router.post("/approve")
async def approve_registration(
    body: ApproveRegistrationRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    # Verify the admin is authorized for this club
    result = await db.execute(
        select(RegistrationRequest).where(
            RegistrationRequest.id == body.registration_id
        )
    )
    req = result.scalar_one_or_none()
    if req:
        require_admin(current_user, req.club_id)

    service = RegistrationService(db)
    member = await service.approve_registration(
        body.registration_id, current_user.user_id, body.role
    )
    return {
        "member_id": str(member.id),
        "user_id": str(member.user_id),
        "club_id": str(member.club_id),
        "role": member.role,
    }


@router.post("/reject")
async def reject_registration(
    body: RejectRegistrationRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    result = await db.execute(
        select(RegistrationRequest).where(
            RegistrationRequest.id == body.registration_id
        )
    )
    req = result.scalar_one_or_none()
    if req:
        require_admin(current_user, req.club_id)

    service = RegistrationService(db)
    rejected = await service.reject_registration(
        body.registration_id, current_user.user_id, body.reason
    )
    return {"id": str(rejected.id), "status": rejected.status}


@router.post("/submit-club")
async def submit_club(
    body: SubmitClubRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    service = RegistrationService(db)
    pcr = await service.submit_club(current_user.user_id, body.club_name)
    return {
        "id": str(pcr.id),
        "club_name": pcr.club_name,
        "club_slug": pcr.club_slug,
        "status": pcr.status,
    }


@router.post("/approve-club")
async def approve_club(
    body: ApproveClubRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    require_platform_admin(current_user)
    service = RegistrationService(db)
    result = await service.approve_club(body.pending_club_id, current_user.user_id)
    return result


@router.post("/reject-club")
async def reject_club(
    body: RejectClubRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    require_platform_admin(current_user)
    service = RegistrationService(db)
    rejected = await service.reject_club(
        body.pending_club_id, current_user.user_id, body.reason
    )
    return {"id": str(rejected.id), "status": rejected.status}


# Club-scoped pending registrations
@club_registrations_router.get(
    "/clubs/{club_id}/pending-registrations",
    response_model=list[RegistrationRequestRead],
)
async def get_pending_for_club(
    club_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[RegistrationRequestRead]:
    require_admin(current_user, club_id)
    service = RegistrationService(db)
    requests = await service.get_pending_for_club(club_id)
    return [RegistrationRequestRead(**r) for r in requests]
