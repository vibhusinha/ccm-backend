from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import NotFoundError
from app.core.permissions import require_admin, require_member
from app.schemas.auth import CurrentUser
from app.schemas.lifecycle import PlayerSelectionStatsRead
from app.schemas.player import PlayerCreate, PlayerRead, PlayerUpdate
from app.services.lifecycle_service import LifecycleService
from app.services.player_service import PlayerService

router = APIRouter(prefix="/clubs/{club_id}/players", tags=["players"])


@router.get("/me", response_model=PlayerRead)
async def get_my_player(
    club_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PlayerRead:
    require_member(current_user, club_id)
    service = PlayerService(db, club_id)
    player = await service.get_by_user_id(current_user.user_id)
    if not player:
        raise NotFoundError("Player profile not found for this club")
    return PlayerRead.model_validate(player)


@router.get("/", response_model=list[PlayerRead])
async def list_players(
    club_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[PlayerRead]:
    require_member(current_user, club_id)
    service = PlayerService(db, club_id)
    players = await service.get_all()
    return [PlayerRead.model_validate(p) for p in players]


@router.post("/", response_model=PlayerRead, status_code=201)
async def create_player(
    club_id: Annotated[UUID, Path()],
    body: PlayerCreate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PlayerRead:
    require_admin(current_user, club_id)
    service = PlayerService(db, club_id)
    player = await service.create(**body.model_dump())
    return PlayerRead.model_validate(player)


@router.get("/{player_id}", response_model=PlayerRead)
async def get_player(
    club_id: Annotated[UUID, Path()],
    player_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PlayerRead:
    require_member(current_user, club_id)
    service = PlayerService(db, club_id)
    player = await service.get_by_id(player_id)
    if not player:
        raise NotFoundError("Player not found")
    return PlayerRead.model_validate(player)


@router.get("/{player_id}/selection-stats", response_model=PlayerSelectionStatsRead)
async def get_player_selection_stats(
    club_id: Annotated[UUID, Path()],
    player_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PlayerSelectionStatsRead:
    require_member(current_user, club_id)
    service = LifecycleService(db, club_id)
    return await service.get_selection_stats(player_id)


@router.patch("/{player_id}", response_model=PlayerRead)
async def update_player(
    club_id: Annotated[UUID, Path()],
    player_id: Annotated[UUID, Path()],
    body: PlayerUpdate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PlayerRead:
    require_admin(current_user, club_id)
    service = PlayerService(db, club_id)
    player = await service.update(player_id, **body.model_dump(exclude_unset=True))
    if not player:
        raise NotFoundError("Player not found")
    return PlayerRead.model_validate(player)


@router.delete("/{player_id}", status_code=204)
async def delete_player(
    club_id: Annotated[UUID, Path()],
    player_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    require_admin(current_user, club_id)
    service = PlayerService(db, club_id)
    if not await service.delete(player_id):
        raise NotFoundError("Player not found")
