from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import NotFoundError
from app.core.permissions import require_admin_or_captain, require_member
from app.models.match import Match
from app.schemas.auth import CurrentUser
from app.schemas.scoring import (
    FallOfWicketRead,
    InningsRead,
    MatchForScoringRead,
    MatchScorecardRead,
    OppositionPlayerCreate,
    OppositionPlayerRead,
    SaveFallOfWicketInput,
    SaveHomePlayerStatsInput,
    SaveInningsInput,
    SaveOppositionStatsInput,
    UpdateMatchResultInput,
)
from app.schemas.match import MatchRead
from app.services.scoring_service import ScoringService

# Match-scoped scoring routes
router = APIRouter(prefix="/matches/{match_id}", tags=["scoring"])

# Club-scoped routes
club_router = APIRouter(prefix="/clubs/{club_id}", tags=["scoring"])

# Innings-scoped routes
innings_router = APIRouter(prefix="/innings/{innings_id}", tags=["scoring"])


async def _get_match_club_id(match_id: UUID, db: AsyncSession) -> UUID:
    """Helper to look up the club_id for a match."""
    from sqlalchemy import select
    stmt = select(Match.club_id).where(Match.id == match_id)
    result = await db.execute(stmt)
    club_id = result.scalar_one_or_none()
    if club_id is None:
        raise NotFoundError("Match not found")
    return club_id


@router.get("/scorecard", response_model=MatchScorecardRead)
async def get_scorecard(
    match_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MatchScorecardRead:
    club_id = await _get_match_club_id(match_id, db)
    require_member(current_user, club_id)
    service = ScoringService(db)
    scorecard = await service.get_scorecard(match_id)
    if not scorecard:
        raise NotFoundError("Scorecard not found")
    return scorecard


@router.get("/opposition-players", response_model=list[OppositionPlayerRead])
async def get_opposition_players(
    match_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[OppositionPlayerRead]:
    club_id = await _get_match_club_id(match_id, db)
    require_member(current_user, club_id)
    service = ScoringService(db)
    players = await service.get_opposition_players(match_id)
    return [OppositionPlayerRead.model_validate(p) for p in players]


@router.post("/opposition-players", response_model=OppositionPlayerRead, status_code=201)
async def add_opposition_player(
    match_id: Annotated[UUID, Path()],
    body: OppositionPlayerCreate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> OppositionPlayerRead:
    club_id = await _get_match_club_id(match_id, db)
    require_admin_or_captain(current_user, club_id)
    service = ScoringService(db)
    player = await service.add_opposition_player(match_id, **body.model_dump())
    return OppositionPlayerRead.model_validate(player)


@router.post("/innings", response_model=InningsRead, status_code=201)
async def save_innings(
    match_id: Annotated[UUID, Path()],
    body: SaveInningsInput,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InningsRead:
    club_id = await _get_match_club_id(match_id, db)
    require_admin_or_captain(current_user, club_id)
    service = ScoringService(db)
    innings = await service.save_innings(match_id, **body.model_dump())
    return InningsRead.model_validate(innings)


@innings_router.post("/fall-of-wickets", response_model=FallOfWicketRead, status_code=201)
async def save_fall_of_wicket(
    innings_id: Annotated[UUID, Path()],
    body: SaveFallOfWicketInput,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FallOfWicketRead:
    # Look up innings to get match, then club
    from sqlalchemy import select
    from app.models.match_innings import MatchInnings
    stmt = select(MatchInnings.match_id).where(MatchInnings.id == innings_id)
    result = await db.execute(stmt)
    match_id = result.scalar_one_or_none()
    if match_id is None:
        raise NotFoundError("Innings not found")

    club_id = await _get_match_club_id(match_id, db)
    require_admin_or_captain(current_user, club_id)

    service = ScoringService(db)
    fow = await service.save_fall_of_wicket(innings_id, **body.model_dump())
    return FallOfWicketRead.model_validate(fow)


@router.post("/home-player-stats")
async def save_home_player_stats(
    match_id: Annotated[UUID, Path()],
    body: SaveHomePlayerStatsInput,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    club_id = await _get_match_club_id(match_id, db)
    require_admin_or_captain(current_user, club_id)
    service = ScoringService(db)
    record_id = await service.save_home_player_stats(match_id, body.model_dump())
    return {"id": record_id}


@router.post("/opposition-player-stats")
async def save_opposition_stats(
    match_id: Annotated[UUID, Path()],
    body: SaveOppositionStatsInput,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    club_id = await _get_match_club_id(match_id, db)
    require_admin_or_captain(current_user, club_id)
    service = ScoringService(db)
    record_id = await service.save_opposition_stats(match_id, body.model_dump())
    return {"id": record_id}


@router.post("/result", response_model=MatchRead)
async def update_match_result(
    match_id: Annotated[UUID, Path()],
    body: UpdateMatchResultInput,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MatchRead:
    club_id = await _get_match_club_id(match_id, db)
    require_admin_or_captain(current_user, club_id)
    service = ScoringService(db)
    match = await service.update_result(match_id, body.model_dump(exclude_unset=True))
    if not match:
        raise NotFoundError("Match not found")
    return MatchRead.model_validate(match)


@router.delete("/scorecard", status_code=204)
async def delete_scorecard(
    match_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    club_id = await _get_match_club_id(match_id, db)
    require_admin_or_captain(current_user, club_id)
    service = ScoringService(db)
    await service.delete_scorecard(match_id)
    return Response(status_code=204)


@club_router.get("/matches-for-scoring", response_model=list[MatchForScoringRead])
async def get_matches_for_scoring(
    club_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[MatchForScoringRead]:
    require_member(current_user, club_id)
    service = ScoringService(db)
    matches = await service.get_matches_for_scoring(club_id)
    return matches
