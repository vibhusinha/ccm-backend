from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import NotFoundError
from app.core.permissions import require_admin, require_member
from app.models.club_key_person import ClubKeyPerson
from app.schemas.auth import CurrentUser
from app.schemas.club import ClubKeyPersonRead, ClubRead, ClubUpdate
from app.services.club_service import ClubService

router = APIRouter(prefix="/clubs", tags=["clubs"])


@router.get("/", response_model=list[ClubRead])
async def list_my_clubs(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[ClubRead]:
    service = ClubService(db)
    clubs = await service.get_clubs_for_user(current_user.user_id)
    return [ClubRead.model_validate(c) for c in clubs]


@router.get("/{club_id}", response_model=ClubRead)
async def get_club(
    club_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ClubRead:
    require_member(current_user, club_id)
    service = ClubService(db)
    club = await service.get_by_id(club_id)
    if not club:
        raise NotFoundError("Club not found")
    return ClubRead.model_validate(club)


@router.patch("/{club_id}", response_model=ClubRead)
async def update_club(
    club_id: Annotated[UUID, Path()],
    body: ClubUpdate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ClubRead:
    require_admin(current_user, club_id)
    service = ClubService(db)
    club = await service.update(club_id, **body.model_dump(exclude_unset=True))
    if not club:
        raise NotFoundError("Club not found")
    return ClubRead.model_validate(club)


@router.get("/{club_id}/key-people", response_model=list[ClubKeyPersonRead])
async def get_key_people(
    club_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[ClubKeyPersonRead]:
    require_member(current_user, club_id)
    stmt = (
        select(ClubKeyPerson)
        .where(ClubKeyPerson.club_id == club_id)
        .order_by(ClubKeyPerson.display_order, ClubKeyPerson.position)
    )
    result = await db.execute(stmt)
    people = list(result.scalars().all())
    return [ClubKeyPersonRead.model_validate(p) for p in people]
