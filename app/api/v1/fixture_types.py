from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import NotFoundError
from app.core.permissions import require_admin, require_member
from app.schemas.auth import CurrentUser
from app.schemas.fixture_type import FixtureTypeCreate, FixtureTypeRead, FixtureTypeUpdate
from app.services.fixture_type_service import FixtureTypeService

router = APIRouter(prefix="/clubs/{club_id}/fixture-types", tags=["fixture-types"])


@router.get("/", response_model=list[FixtureTypeRead])
async def list_fixture_types(
    club_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[FixtureTypeRead]:
    require_member(current_user, club_id)
    service = FixtureTypeService(db, club_id)
    fixture_types = await service.get_all()
    return [FixtureTypeRead.model_validate(ft) for ft in fixture_types]


@router.post("/", response_model=FixtureTypeRead, status_code=201)
async def create_fixture_type(
    club_id: Annotated[UUID, Path()],
    body: FixtureTypeCreate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FixtureTypeRead:
    require_admin(current_user, club_id)
    service = FixtureTypeService(db, club_id)
    fixture_type = await service.create(**body.model_dump())
    return FixtureTypeRead.model_validate(fixture_type)


@router.patch("/{id}", response_model=FixtureTypeRead)
async def update_fixture_type(
    club_id: Annotated[UUID, Path()],
    id: Annotated[UUID, Path()],
    body: FixtureTypeUpdate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FixtureTypeRead:
    require_admin(current_user, club_id)
    service = FixtureTypeService(db, club_id)
    fixture_type = await service.update(id, **body.model_dump(exclude_unset=True))
    if not fixture_type:
        raise NotFoundError("Fixture type not found")
    return FixtureTypeRead.model_validate(fixture_type)


@router.delete("/{id}", status_code=204)
async def delete_fixture_type(
    club_id: Annotated[UUID, Path()],
    id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    require_admin(current_user, club_id)
    service = FixtureTypeService(db, club_id)
    if not await service.delete(id):
        raise NotFoundError("Fixture type not found")
