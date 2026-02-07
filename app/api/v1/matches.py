from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import NotFoundError
from app.core.permissions import require_admin, require_admin_or_captain, require_member
from app.schemas.auth import CurrentUser
from app.schemas.match import MatchCreate, MatchRead, MatchUpdate
from app.services.match_service import MatchService

router = APIRouter(prefix="/clubs/{club_id}/matches", tags=["matches"])


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
