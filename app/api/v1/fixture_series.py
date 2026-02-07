from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import NotFoundError
from app.core.permissions import require_admin, require_member
from app.schemas.auth import CurrentUser
from app.schemas.fixture_series import (
    FixtureSeriesCreate,
    FixtureSeriesRead,
    FixtureSeriesUpdate,
)
from app.services.fixture_series_service import FixtureSeriesService

router = APIRouter(prefix="/clubs/{club_id}/fixture-series", tags=["fixture-series"])


@router.get("/", response_model=list[FixtureSeriesRead])
async def list_fixture_series(
    club_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[FixtureSeriesRead]:
    require_member(current_user, club_id)
    service = FixtureSeriesService(db, club_id)
    series_list = await service.get_all()
    return [FixtureSeriesRead.model_validate(s) for s in series_list]


@router.post("/", response_model=FixtureSeriesRead, status_code=201)
async def create_fixture_series(
    club_id: Annotated[UUID, Path()],
    body: FixtureSeriesCreate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FixtureSeriesRead:
    require_admin(current_user, club_id)
    service = FixtureSeriesService(db, club_id)
    series = await service.create(**body.model_dump())
    return FixtureSeriesRead.model_validate(series)


@router.patch("/{id}", response_model=FixtureSeriesRead)
async def update_fixture_series(
    club_id: Annotated[UUID, Path()],
    id: Annotated[UUID, Path()],
    body: FixtureSeriesUpdate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FixtureSeriesRead:
    require_admin(current_user, club_id)
    service = FixtureSeriesService(db, club_id)
    series = await service.update(id, **body.model_dump(exclude_unset=True))
    if not series:
        raise NotFoundError("Fixture series not found")
    return FixtureSeriesRead.model_validate(series)


@router.delete("/{id}", status_code=204)
async def delete_fixture_series(
    club_id: Annotated[UUID, Path()],
    id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    require_admin(current_user, club_id)
    service = FixtureSeriesService(db, club_id)
    if not await service.delete(id):
        raise NotFoundError("Fixture series not found")
