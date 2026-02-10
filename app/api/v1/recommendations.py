from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import NotFoundError
from app.core.permissions import require_admin, require_admin_or_captain, require_member
from app.models.match import Match
from app.models.player import Player
from app.schemas.auth import CurrentUser
from app.schemas.recommendation import (
    PlayerMatchHistoryRead,
    PlayerMatchStatsRead,
    PlayerRecommendationRead,
    PlayerSelectionOverrideCreate,
    PlayerSelectionOverrideRead,
    RecommendationResultRead,
    RecordPracticeAttendanceInput,
    SavePlayerMatchStatsInput,
    SelectionWithdrawalInput,
    SimulationStatusRead,
    TeamSelectionConfigRead,
    TeamSelectionConfigUpdate,
)
from app.services.recommendation_service import RecommendationService

# Match-scoped routes
match_router = APIRouter(prefix="/matches/{match_id}", tags=["recommendations"])

# Club-scoped routes
club_router = APIRouter(prefix="/clubs/{club_id}", tags=["recommendations"])

# Player-scoped routes
player_router = APIRouter(prefix="/players/{player_id}", tags=["recommendations"])

# Override-scoped routes
override_router = APIRouter(prefix="/player-selection-overrides", tags=["recommendations"])

# Fixture-scoped routes
fixture_router = APIRouter(prefix="/fixtures/{fixture_id}", tags=["recommendations"])


async def _get_match_club_id(match_id: UUID, db: AsyncSession) -> UUID:
    from sqlalchemy import select
    stmt = select(Match.club_id).where(Match.id == match_id)
    result = await db.execute(stmt)
    club_id = result.scalar_one_or_none()
    if club_id is None:
        raise NotFoundError("Match not found")
    return club_id


async def _get_player_club_id(player_id: UUID, db: AsyncSession) -> UUID:
    from sqlalchemy import select
    stmt = select(Player.club_id).where(Player.id == player_id)
    result = await db.execute(stmt)
    club_id = result.scalar_one_or_none()
    if club_id is None:
        raise NotFoundError("Player not found")
    return club_id


async def _get_fixture_club_id(fixture_id: UUID, db: AsyncSession) -> UUID:
    from sqlalchemy import select
    stmt = select(Match.club_id).where(Match.id == fixture_id)
    result = await db.execute(stmt)
    club_id = result.scalar_one_or_none()
    if club_id is None:
        raise NotFoundError("Fixture not found")
    return club_id


@match_router.get("/recommendation", response_model=list[PlayerRecommendationRead])
async def get_recommendation(
    match_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[PlayerRecommendationRead]:
    club_id = await _get_match_club_id(match_id, db)
    require_member(current_user, club_id)
    service = RecommendationService(db, club_id)
    return await service.get_recommendation(match_id)


@match_router.get("/player-stats", response_model=list[PlayerMatchStatsRead])
async def get_match_player_stats(
    match_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[PlayerMatchStatsRead]:
    club_id = await _get_match_club_id(match_id, db)
    require_member(current_user, club_id)
    service = RecommendationService(db, club_id)
    return await service.get_match_stats(match_id)


@match_router.post("/player-stats")
async def record_match_stats(
    match_id: Annotated[UUID, Path()],
    body: SavePlayerMatchStatsInput,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    club_id = await _get_match_club_id(match_id, db)
    require_admin_or_captain(current_user, club_id)
    service = RecommendationService(db, club_id)
    await service.save_match_stats(match_id, body.player_id, body.stats)
    return {"success": True}


@match_router.post("/selection-withdrawal")
async def record_selection_withdrawal(
    match_id: Annotated[UUID, Path()],
    body: SelectionWithdrawalInput,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    club_id = await _get_match_club_id(match_id, db)
    require_member(current_user, club_id)
    service = RecommendationService(db, club_id)
    await service.record_selection_withdrawal(
        match_id, body.player_id, body.match_time, body.reason
    )
    return {"success": True}


@match_router.post("/clear-selections")
async def clear_selections(
    match_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    club_id = await _get_match_club_id(match_id, db)
    require_admin_or_captain(current_user, club_id)
    service = RecommendationService(db, club_id)
    count = await service.clear_selections(match_id)
    return {"cleared": count}


@player_router.get("/match-history", response_model=list[PlayerMatchHistoryRead])
async def get_player_match_history(
    player_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(10, ge=1, le=50),
) -> list[PlayerMatchHistoryRead]:
    club_id = await _get_player_club_id(player_id, db)
    require_member(current_user, club_id)
    service = RecommendationService(db, club_id)
    return await service.get_player_match_history(player_id, limit=limit)


@club_router.get("/team-selection-config", response_model=TeamSelectionConfigRead | None)
async def get_team_selection_config(
    club_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TeamSelectionConfigRead | None:
    require_member(current_user, club_id)
    service = RecommendationService(db, club_id)
    config = await service.get_config()
    if not config:
        return None
    return TeamSelectionConfigRead.model_validate(config)


@club_router.post("/team-selection-config", response_model=TeamSelectionConfigRead)
async def update_team_selection_config(
    club_id: Annotated[UUID, Path()],
    body: TeamSelectionConfigUpdate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TeamSelectionConfigRead:
    require_admin(current_user, club_id)
    service = RecommendationService(db, club_id)
    config = await service.upsert_config(**body.model_dump(exclude_unset=True))
    return TeamSelectionConfigRead.model_validate(config)


@club_router.get(
    "/player-selection-overrides", response_model=list[PlayerSelectionOverrideRead]
)
async def get_player_selection_overrides(
    club_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[PlayerSelectionOverrideRead]:
    require_member(current_user, club_id)
    service = RecommendationService(db, club_id)
    return await service.get_overrides()


@club_router.post(
    "/player-selection-overrides", response_model=PlayerSelectionOverrideRead
)
async def upsert_player_selection_override(
    club_id: Annotated[UUID, Path()],
    body: PlayerSelectionOverrideCreate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PlayerSelectionOverrideRead:
    require_admin(current_user, club_id)
    service = RecommendationService(db, club_id)
    override = await service.upsert_override(
        body.player_id, body.base_score_override, body.notes
    )
    return PlayerSelectionOverrideRead.model_validate(override)


@override_router.delete("/{override_id}", status_code=204)
async def delete_player_selection_override(
    override_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    # Look up override to get club_id
    from sqlalchemy import select
    from app.models.player_selection_override import PlayerSelectionOverride

    stmt = select(PlayerSelectionOverride.club_id).where(
        PlayerSelectionOverride.id == override_id
    )
    result = await db.execute(stmt)
    club_id = result.scalar_one_or_none()
    if club_id is None:
        raise NotFoundError("Override not found")

    require_admin(current_user, club_id)
    service = RecommendationService(db, club_id)
    await service.delete_override(override_id)
    return Response(status_code=204)


@club_router.get("/simulation-status", response_model=SimulationStatusRead)
async def get_simulation_status(
    club_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SimulationStatusRead:
    require_member(current_user, club_id)
    service = RecommendationService(db, club_id)
    return await service.get_simulation_status()


@fixture_router.post("/practice-attendance")
async def record_practice_attendance(
    fixture_id: Annotated[UUID, Path()],
    body: RecordPracticeAttendanceInput,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    club_id = await _get_fixture_club_id(fixture_id, db)
    require_admin_or_captain(current_user, club_id)
    service = RecommendationService(db, club_id)
    result = await service.record_practice_attendance(
        fixture_id, [a.model_dump() for a in body.attendances], current_user.user_id
    )
    return {"success": result}


@club_router.post(
    "/reset-selections-first-match", response_model=RecommendationResultRead
)
async def reset_selections_first_match(
    club_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RecommendationResultRead:
    require_admin_or_captain(current_user, club_id)
    service = RecommendationService(db, club_id)
    return await service.reset_selections_first_match()


@club_router.post("/recommend-next-match", response_model=RecommendationResultRead)
async def recommend_next_match(
    club_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    after_date: str | None = None,
) -> RecommendationResultRead:
    require_admin_or_captain(current_user, club_id)
    service = RecommendationService(db, club_id)
    return await service.recommend_next_match(after_date)
