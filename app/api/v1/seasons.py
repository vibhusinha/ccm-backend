from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import NotFoundError
from app.core.permissions import require_admin, require_member
from app.schemas.auth import CurrentUser
from app.schemas.season import SeasonCreate, SeasonRead, SeasonUpdate
from app.services.season_service import SeasonService

router = APIRouter(prefix="/clubs/{club_id}/seasons", tags=["seasons"])


@router.get("/", response_model=list[SeasonRead])
async def list_seasons(
    club_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[SeasonRead]:
    require_member(current_user, club_id)
    service = SeasonService(db, club_id)
    seasons = await service.get_all()
    return [SeasonRead.model_validate(s) for s in seasons]


@router.post("/", response_model=SeasonRead, status_code=201)
async def create_season(
    club_id: Annotated[UUID, Path()],
    body: SeasonCreate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SeasonRead:
    require_admin(current_user, club_id)
    service = SeasonService(db, club_id)
    season = await service.create(**body.model_dump())
    return SeasonRead.model_validate(season)


@router.patch("/{season_id}", response_model=SeasonRead)
async def update_season(
    club_id: Annotated[UUID, Path()],
    season_id: Annotated[UUID, Path()],
    body: SeasonUpdate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SeasonRead:
    require_admin(current_user, club_id)
    service = SeasonService(db, club_id)
    season = await service.update(season_id, **body.model_dump(exclude_unset=True))
    if not season:
        raise NotFoundError("Season not found")
    return SeasonRead.model_validate(season)


@router.delete("/{season_id}", status_code=204)
async def delete_season(
    club_id: Annotated[UUID, Path()],
    season_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    require_admin(current_user, club_id)
    service = SeasonService(db, club_id)
    if not await service.delete(season_id):
        raise NotFoundError("Season not found")


@router.post("/{season_id}/set-current", response_model=SeasonRead)
async def set_current_season(
    club_id: Annotated[UUID, Path()],
    season_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SeasonRead:
    require_admin(current_user, club_id)
    service = SeasonService(db, club_id)
    season = await service.set_current(season_id)
    if not season:
        raise NotFoundError("Season not found")
    return SeasonRead.model_validate(season)
