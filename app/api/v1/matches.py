from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import NotFoundError
from app.core.permissions import require_admin, require_admin_or_captain, require_member
from app.models.fixture_type import FixtureType
from app.models.match import Match
from app.models.season import Season
from app.models.team import Team
from app.schemas.auth import CurrentUser
from app.schemas.match import MatchCreate, MatchRead, MatchUpdate
from app.services.match_service import MatchService

router = APIRouter(prefix="/clubs/{club_id}/matches", tags=["matches"])

# Also create a fixtures router for the enriched endpoint the frontend expects
fixtures_router = APIRouter(prefix="/clubs/{club_id}/fixtures", tags=["fixtures"])


@fixtures_router.get("/")
async def list_fixtures(
    club_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    season_id: UUID | None = Query(None),
    team_id: UUID | None = Query(None),
    fixture_type_id: UUID | None = Query(None),
    month: int | None = Query(None),
    year: int | None = Query(None),
    status: str | None = Query(None),
) -> list[dict]:
    """Return fixtures with joined team/season/fixture_type data for the frontend."""
    require_member(current_user, club_id)

    stmt = (
        select(
            Match,
            Team.name.label("team_name"),
            Season.name.label("season_name"),
            FixtureType.name.label("fixture_type_name"),
            FixtureType.color.label("fixture_type_color"),
            FixtureType.icon.label("fixture_type_icon"),
        )
        .outerjoin(Team, Match.team_id == Team.id)
        .outerjoin(Season, Match.season_id == Season.id)
        .outerjoin(FixtureType, Match.fixture_type_id == FixtureType.id)
        .where(Match.club_id == club_id)
        .order_by(Match.date.asc())
    )

    if season_id:
        stmt = stmt.where(Match.season_id == season_id)
    if team_id:
        stmt = stmt.where(Match.team_id == team_id)
    if fixture_type_id:
        stmt = stmt.where(Match.fixture_type_id == fixture_type_id)
    if status:
        stmt = stmt.where(Match.status == status)
    if month and year:
        from sqlalchemy import extract
        stmt = stmt.where(extract("month", Match.date) == month, extract("year", Match.date) == year)
    elif year:
        from sqlalchemy import extract
        stmt = stmt.where(extract("year", Match.date) == year)

    result = await db.execute(stmt)
    rows = result.all()

    return [
        {
            "id": str(m.id),
            "club_id": str(m.club_id),
            "season_id": str(m.season_id) if m.season_id else None,
            "team_id": str(m.team_id) if m.team_id else None,
            "fixture_type_id": str(m.fixture_type_id) if m.fixture_type_id else None,
            "series_id": str(m.series_id) if m.series_id else None,
            "match_date": m.date.isoformat(),
            "match_time": m.time.isoformat(),
            "opponent": m.opponent,
            "venue": m.venue,
            "is_home": m.venue == "Home",
            "match_type": m.type,
            "match_status": m.status,
            "fee_amount": float(m.fee_amount),
            "our_score": m.our_score,
            "opponent_score": m.opponent_score,
            "result": None,
            "result_margin": None,
            "result_margin_type": None,
            "created_at": m.created_at.isoformat() if m.created_at else None,
            "updated_at": m.updated_at.isoformat() if m.updated_at else None,
            "team_name": team_name,
            "season_name": season_name,
            "fixture_type_name": ft_name,
            "fixture_type_color": ft_color,
            "fixture_type_icon": ft_icon,
            "fixture_type_subtype": "match",
            "location_name": None,
            "location_address": None,
            "location_postcode": None,
            "is_system_default": False,
        }
        for m, team_name, season_name, ft_name, ft_color, ft_icon in rows
    ]


@router.get("/", response_model=list[MatchRead])
async def list_matches(
    club_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[MatchRead]:
    require_member(current_user, club_id)
    service = MatchService(db, club_id)
    matches = await service.get_all()
    return [MatchRead.model_validate(m) for m in matches]


@router.get("/upcoming", response_model=list[MatchRead])
async def list_upcoming(
    club_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[MatchRead]:
    require_member(current_user, club_id)
    service = MatchService(db, club_id)
    matches = await service.get_upcoming()
    return [MatchRead.model_validate(m) for m in matches]


@router.post("/", response_model=MatchRead, status_code=201)
async def create_match(
    club_id: Annotated[UUID, Path()],
    body: MatchCreate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MatchRead:
    require_admin(current_user, club_id)
    service = MatchService(db, club_id)
    match = await service.create(**body.model_dump())
    return MatchRead.model_validate(match)


@router.get("/{match_id}", response_model=MatchRead)
async def get_match(
    club_id: Annotated[UUID, Path()],
    match_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MatchRead:
    require_member(current_user, club_id)
    service = MatchService(db, club_id)
    match = await service.get_with_details(match_id)
    if not match:
        raise NotFoundError("Match not found")
    return MatchRead.model_validate(match)


@router.patch("/{match_id}", response_model=MatchRead)
async def update_match(
    club_id: Annotated[UUID, Path()],
    match_id: Annotated[UUID, Path()],
    body: MatchUpdate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MatchRead:
    require_admin_or_captain(current_user, club_id)
    service = MatchService(db, club_id)
    match = await service.update(match_id, **body.model_dump(exclude_unset=True))
    if not match:
        raise NotFoundError("Match not found")
    return MatchRead.model_validate(match)


@router.delete("/{match_id}", status_code=204)
async def delete_match(
    club_id: Annotated[UUID, Path()],
    match_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    require_admin(current_user, club_id)
    service = MatchService(db, club_id)
    if not await service.delete(match_id):
        raise NotFoundError("Match not found")


@router.post("/{match_id}/cancel", response_model=MatchRead)
async def cancel_match(
    club_id: Annotated[UUID, Path()],
    match_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MatchRead:
    require_admin(current_user, club_id)
    service = MatchService(db, club_id)
    match = await service.cancel(match_id)
    if not match:
        raise NotFoundError("Match not found")
    return MatchRead.model_validate(match)
