from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import NotFoundError
from app.core.permissions import require_admin_or_captain, require_member
from app.models.match import Match
from app.schemas.auth import CurrentUser
from app.schemas.lifecycle import (
    AbandonedInput,
    AuditLogEntryRead,
    ConfirmParticipationInput,
    DeadlineAlertRead,
    ParticipationRead,
    PlayerFixtureLifecycleRead,
    SubstituteInput,
    WithdrawalInput,
)
from app.services.lifecycle_service import LifecycleService

# Match-scoped routes
router = APIRouter(prefix="/matches/{match_id}", tags=["lifecycle"])

# Club-scoped routes
club_router = APIRouter(prefix="/clubs/{club_id}", tags=["lifecycle"])

# Player-scoped routes
player_router = APIRouter(prefix="/players/{player_id}", tags=["lifecycle"])


async def _get_match_club_id(match_id: UUID, db: AsyncSession) -> UUID:
    from sqlalchemy import select
    stmt = select(Match.club_id).where(Match.id == match_id)
    result = await db.execute(stmt)
    club_id = result.scalar_one_or_none()
    if club_id is None:
        raise NotFoundError("Match not found")
    return club_id


@router.get("/lifecycle", response_model=list[PlayerFixtureLifecycleRead])
async def get_match_lifecycle(
    match_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[PlayerFixtureLifecycleRead]:
    club_id = await _get_match_club_id(match_id, db)
    require_member(current_user, club_id)
    service = LifecycleService(db, club_id)
    return await service.get_match_lifecycle(match_id)


@club_router.get("/deadline-alerts", response_model=list[DeadlineAlertRead])
async def get_deadline_alerts(
    club_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[DeadlineAlertRead]:
    require_member(current_user, club_id)
    service = LifecycleService(db, club_id)
    return await service.get_deadline_alerts()


@router.get("/audit-log", response_model=list[AuditLogEntryRead])
async def get_match_audit_log(
    match_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[AuditLogEntryRead]:
    club_id = await _get_match_club_id(match_id, db)
    require_member(current_user, club_id)
    service = LifecycleService(db, club_id)
    return await service.get_audit_log(match_id, limit=limit, offset=offset)


@router.get("/participation", response_model=list[ParticipationRead])
async def get_match_participation(
    match_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[ParticipationRead]:
    club_id = await _get_match_club_id(match_id, db)
    require_member(current_user, club_id)
    service = LifecycleService(db, club_id)
    return await service.get_participation(match_id)


@player_router.get("/played-match-ids")
async def get_played_match_ids(
    player_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[str]:
    # Look up player to get club_id for permission check
    from sqlalchemy import select
    from app.models.player import Player
    stmt = select(Player.club_id).where(Player.id == player_id)
    result = await db.execute(stmt)
    club_id = result.scalar_one_or_none()
    if club_id is None:
        raise NotFoundError("Player not found")

    require_member(current_user, club_id)
    service = LifecycleService(db, club_id)
    return await service.get_played_match_ids(player_id)


@router.post("/confirm-participation")
async def confirm_participation(
    match_id: Annotated[UUID, Path()],
    body: ConfirmParticipationInput,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    club_id = await _get_match_club_id(match_id, db)
    require_admin_or_captain(current_user, club_id)
    service = LifecycleService(db, club_id)
    return await service.confirm_participation(
        match_id,
        [p.model_dump() for p in body.participations],
        actor_id=current_user.user_id,
    )


@router.post("/withdrawal")
async def record_withdrawal(
    match_id: Annotated[UUID, Path()],
    body: WithdrawalInput,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    club_id = await _get_match_club_id(match_id, db)
    require_member(current_user, club_id)
    service = LifecycleService(db, club_id)
    return await service.record_withdrawal(
        match_id, body.player_id, body.reason, actor_id=current_user.user_id
    )


@router.post("/substitute")
async def add_substitute(
    match_id: Annotated[UUID, Path()],
    body: SubstituteInput,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    club_id = await _get_match_club_id(match_id, db)
    require_admin_or_captain(current_user, club_id)
    service = LifecycleService(db, club_id)
    return await service.add_substitute(
        match_id, body.player_id, body.replaces_player_id, actor_id=current_user.user_id
    )


@router.post("/finalize-selection")
async def finalize_selection(
    match_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    club_id = await _get_match_club_id(match_id, db)
    require_admin_or_captain(current_user, club_id)
    service = LifecycleService(db, club_id)
    return await service.finalize_selection(match_id, actor_id=current_user.user_id)


@router.post("/abandoned")
async def record_abandoned(
    match_id: Annotated[UUID, Path()],
    body: AbandonedInput,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    club_id = await _get_match_club_id(match_id, db)
    require_admin_or_captain(current_user, club_id)
    service = LifecycleService(db, club_id)
    return await service.record_abandoned(match_id, body.reason, actor_id=current_user.user_id)
