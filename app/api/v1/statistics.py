from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.permissions import require_member
from app.schemas.auth import CurrentUser
from app.schemas.statistics import (
    ClubMatchStatisticsRead,
    MatchTypeStatisticsRead,
    PlayerMatchRecordRead,
    RecentMatchResultRead,
    TeamMatchStatisticsRead,
)
from app.services.statistics_service import StatisticsService

router = APIRouter(prefix="/clubs/{club_id}/match-statistics", tags=["statistics"])


@router.get("/", response_model=ClubMatchStatisticsRead)
async def get_club_match_statistics(
    club_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    team_id: UUID | None = Query(None),
    season_id: UUID | None = Query(None),
    fixture_type_id: UUID | None = Query(None),
) -> ClubMatchStatisticsRead:
    require_member(current_user, club_id)
    service = StatisticsService(db, club_id)
    stats = await service.get_club_statistics(
        team_id=team_id, season_id=season_id, fixture_type_id=fixture_type_id
    )
    return stats


@router.get("/teams", response_model=list[TeamMatchStatisticsRead])
async def get_team_match_statistics(
    club_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    season_id: UUID | None = Query(None),
) -> list[TeamMatchStatisticsRead]:
    require_member(current_user, club_id)
    service = StatisticsService(db, club_id)
    return await service.get_team_statistics(season_id=season_id)


@router.get("/types", response_model=list[MatchTypeStatisticsRead])
async def get_match_type_statistics(
    club_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    season_id: UUID | None = Query(None),
    team_id: UUID | None = Query(None),
) -> list[MatchTypeStatisticsRead]:
    require_member(current_user, club_id)
    service = StatisticsService(db, club_id)
    return await service.get_type_statistics(season_id=season_id, team_id=team_id)


@router.get("/players", response_model=list[PlayerMatchRecordRead])
async def get_player_match_records(
    club_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    player_id: UUID | None = Query(None),
    season_id: UUID | None = Query(None),
) -> list[PlayerMatchRecordRead]:
    require_member(current_user, club_id)
    service = StatisticsService(db, club_id)
    return await service.get_player_records(player_id=player_id, season_id=season_id)


@router.get("/recent", response_model=list[RecentMatchResultRead])
async def get_recent_match_results(
    club_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(10, ge=1, le=50),
    team_id: UUID | None = Query(None),
    season_id: UUID | None = Query(None),
) -> list[RecentMatchResultRead]:
    require_member(current_user, club_id)
    service = StatisticsService(db, club_id)
    return await service.get_recent_results(limit=limit, team_id=team_id, season_id=season_id)
