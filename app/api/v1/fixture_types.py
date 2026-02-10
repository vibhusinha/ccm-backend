from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path
from pydantic import BaseModel
from sqlalchemy import select, update as sql_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import NotFoundError
from app.core.permissions import require_admin, require_member
from app.models.match import Match
from app.schemas.auth import CurrentUser
from app.schemas.fixture_type import FixtureTypeCreate, FixtureTypeRead, FixtureTypeUpdate
from app.services.fixture_type_service import FixtureTypeService

router = APIRouter(prefix="/clubs/{club_id}/fixture-types", tags=["fixture-types"])
type_action_router = APIRouter(prefix="/fixture-types/{fixture_type_id}", tags=["fixture-types"])


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


class BulkUpdateFixturesInput(BaseModel):
    updates: dict  # fields to update on all matches of this type


@type_action_router.post("/bulk-update")
async def bulk_update_fixtures(
    fixture_type_id: Annotated[UUID, Path()],
    body: BulkUpdateFixturesInput,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    # Get fixture type to determine club_id
    from app.models.fixture_type import FixtureType as FTModel

    stmt = select(FTModel.club_id).where(FTModel.id == fixture_type_id)
    result = await db.execute(stmt)
    club_id = result.scalar_one_or_none()
    if club_id is None:
        raise NotFoundError("Fixture type not found")
    require_admin(current_user, club_id)

    # Bulk update all matches of this fixture type
    allowed_fields = {"venue", "time", "fee_amount", "status"}
    update_data = {k: v for k, v in body.updates.items() if k in allowed_fields}
    if not update_data:
        return {"updated": 0}

    stmt = (
        sql_update(Match)
        .where(Match.fixture_type_id == fixture_type_id, Match.club_id == club_id)
        .values(**update_data)
    )
    result = await db.execute(stmt)
    await db.flush()
    return {"updated": result.rowcount}


@type_action_router.get("/fixtures")
async def list_fixtures_by_type(
    fixture_type_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[dict]:
    from app.models.fixture_type import FixtureType as FTModel
    from app.schemas.match import MatchRead

    stmt = select(FTModel.club_id).where(FTModel.id == fixture_type_id)
    result = await db.execute(stmt)
    club_id = result.scalar_one_or_none()
    if club_id is None:
        raise NotFoundError("Fixture type not found")
    require_member(current_user, club_id)

    stmt = (
        select(Match)
        .where(Match.fixture_type_id == fixture_type_id, Match.club_id == club_id)
        .order_by(Match.date.asc())
    )
    result = await db.execute(stmt)
    matches = list(result.scalars().all())
    return [MatchRead.model_validate(m).model_dump() for m in matches]
