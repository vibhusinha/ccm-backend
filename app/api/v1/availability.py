from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import NotFoundError
from app.core.permissions import require_admin_or_captain, require_member
from app.models.player import Player
from app.schemas.auth import CurrentUser
from app.schemas.lifecycle import MemberAvailabilitySummaryRead
from app.schemas.match_availability import (
    AvailabilityRead,
    AvailabilityUpdate,
    BulkAvailabilityUpdate,
)
from app.services.availability_service import AvailabilityService

router = APIRouter(
    prefix="/clubs/{club_id}/matches/{match_id}/availability",
    tags=["availability"],
)

bulk_router = APIRouter(
    prefix="/clubs/{club_id}/availability",
    tags=["availability"],
)


@router.get("/", response_model=list[AvailabilityRead])
async def get_availability(
    club_id: Annotated[UUID, Path()],
    match_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[AvailabilityRead]:
    require_member(current_user, club_id)
    service = AvailabilityService(db, club_id)
    records = await service.get_for_match(match_id)
    return [AvailabilityRead.model_validate(r) for r in records]


@router.put("/", response_model=AvailabilityRead)
async def set_my_availability(
    club_id: Annotated[UUID, Path()],
    match_id: Annotated[UUID, Path()],
    body: AvailabilityUpdate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AvailabilityRead:
    require_member(current_user, club_id)

    # Find the player record for the current user in this club
    result = await db.execute(
        select(Player).where(
            Player.user_id == current_user.user_id,
            Player.club_id == club_id,
        )
    )
    player = result.scalar_one_or_none()
    if not player:
        raise NotFoundError("Player profile not found for this club")

    service = AvailabilityService(db, club_id)
    record = await service.set_availability(match_id, player.id, body.status)
    return AvailabilityRead.model_validate(record)


@router.get("/summary", response_model=list[MemberAvailabilitySummaryRead])
async def get_availability_summary(
    club_id: Annotated[UUID, Path()],
    match_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[MemberAvailabilitySummaryRead]:
    require_member(current_user, club_id)
    service = AvailabilityService(db, club_id)
    return await service.get_availability_summary(match_id)


@router.post("/requests")
async def send_availability_requests(
    club_id: Annotated[UUID, Path()],
    match_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    require_admin_or_captain(current_user, club_id)
    service = AvailabilityService(db, club_id)
    sent = await service.send_availability_requests(match_id)
    return {"sent": sent}


@bulk_router.post("/bulk")
async def bulk_set_availability(
    club_id: Annotated[UUID, Path()],
    body: BulkAvailabilityUpdate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    require_member(current_user, club_id)
    service = AvailabilityService(db, club_id)
    count = await service.bulk_set(body.match_ids, current_user.user_id, body.status)
    return {"updated_count": count}
