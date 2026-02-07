from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import NotFoundError
from app.core.permissions import require_admin, require_member
from app.schemas.auth import CurrentUser
from app.schemas.team import TeamCreate, TeamRead, TeamUpdate
from app.services.team_service import TeamService

router = APIRouter(prefix="/clubs/{club_id}/teams", tags=["teams"])


@router.get("/", response_model=list[TeamRead])
async def list_teams(
    club_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[TeamRead]:
    require_member(current_user, club_id)
    service = TeamService(db, club_id)
    teams = await service.get_all()
    return [TeamRead.model_validate(t) for t in teams]


@router.post("/", response_model=TeamRead, status_code=201)
async def create_team(
    club_id: Annotated[UUID, Path()],
    body: TeamCreate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TeamRead:
    require_admin(current_user, club_id)
    service = TeamService(db, club_id)
    team = await service.create(**body.model_dump())
    return TeamRead.model_validate(team)


@router.get("/{team_id}", response_model=TeamRead)
async def get_team(
    club_id: Annotated[UUID, Path()],
    team_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TeamRead:
    require_member(current_user, club_id)
    service = TeamService(db, club_id)
    team = await service.get_by_id(team_id)
    if not team:
        raise NotFoundError("Team not found")
    return TeamRead.model_validate(team)


@router.patch("/{team_id}", response_model=TeamRead)
async def update_team(
    club_id: Annotated[UUID, Path()],
    team_id: Annotated[UUID, Path()],
    body: TeamUpdate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TeamRead:
    require_admin(current_user, club_id)
    service = TeamService(db, club_id)
    team = await service.update(team_id, **body.model_dump(exclude_unset=True))
    if not team:
        raise NotFoundError("Team not found")
    return TeamRead.model_validate(team)


@router.delete("/{team_id}", status_code=204)
async def delete_team(
    club_id: Annotated[UUID, Path()],
    team_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    require_admin(current_user, club_id)
    service = TeamService(db, club_id)
    if not await service.delete(team_id):
        raise NotFoundError("Team not found")
