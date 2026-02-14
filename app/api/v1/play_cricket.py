from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import NotFoundError
from app.core.permissions import require_admin
from app.integrations.play_cricket_client import PlayCricketClient
from app.models.club import Club
from app.models.match import Match
from app.schemas.auth import CurrentUser
from app.schemas.play_cricket import (
    PlayCricketScorecardSyncRequest,
    PlayCricketSyncRequest,
    SyncAllResult,
    SyncResult,
)
from app.services.play_cricket_sync_service import PlayCricketSyncService

router = APIRouter(prefix="/clubs/{club_id}/play-cricket", tags=["play-cricket"])


async def _get_club_site_id(db: AsyncSession, club_id: UUID) -> tuple[Club, int]:
    from sqlalchemy import select

    result = await db.execute(select(Club).where(Club.id == club_id))
    club = result.scalar_one_or_none()
    if not club:
        raise NotFoundError("Club not found")
    if not club.play_cricket_id:
        raise HTTPException(
            status_code=400,
            detail="Club does not have a Play-Cricket site ID configured. "
            "Set play_cricket_id on the club first.",
        )
    return club, club.play_cricket_id


def _create_client() -> PlayCricketClient:
    settings = get_settings()
    if not settings.play_cricket_api_token:
        raise HTTPException(
            status_code=400,
            detail="Play-Cricket API token not configured. "
            "Set PLAY_CRICKET_API_TOKEN environment variable.",
        )
    return PlayCricketClient(
        base_url=settings.play_cricket_api_url,
        api_token=settings.play_cricket_api_token,
    )


@router.post("/sync/teams", response_model=SyncResult)
async def sync_teams(
    club_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SyncResult:
    require_admin(current_user, club_id)
    _, site_id = await _get_club_site_id(db, club_id)
    client = _create_client()
    async with client:
        service = PlayCricketSyncService(db, club_id, client)
        return await service.sync_teams(site_id)


@router.post("/sync/players", response_model=SyncResult)
async def sync_players(
    club_id: Annotated[UUID, Path()],
    body: PlayCricketSyncRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SyncResult:
    require_admin(current_user, club_id)
    _, site_id = await _get_club_site_id(db, club_id)
    client = _create_client()
    async with client:
        service = PlayCricketSyncService(db, club_id, client)
        return await service.sync_players(site_id, body.season)


@router.post("/sync/matches", response_model=SyncResult)
async def sync_matches(
    club_id: Annotated[UUID, Path()],
    body: PlayCricketSyncRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SyncResult:
    require_admin(current_user, club_id)
    _, site_id = await _get_club_site_id(db, club_id)
    client = _create_client()
    async with client:
        service = PlayCricketSyncService(db, club_id, client)
        return await service.sync_matches(site_id, body.season)


@router.post("/sync/scorecard", response_model=SyncResult)
async def sync_scorecard(
    club_id: Annotated[UUID, Path()],
    body: PlayCricketScorecardSyncRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SyncResult:
    require_admin(current_user, club_id)
    _, site_id = await _get_club_site_id(db, club_id)

    from sqlalchemy import select

    result = await db.execute(
        select(Match).where(Match.id == body.match_id, Match.club_id == club_id)
    )
    match = result.scalar_one_or_none()
    if not match:
        raise NotFoundError("Match not found")

    client = _create_client()
    async with client:
        service = PlayCricketSyncService(db, club_id, client)
        return await service.sync_match_scorecard(site_id, match)


@router.post("/sync/all", response_model=SyncAllResult)
async def sync_all(
    club_id: Annotated[UUID, Path()],
    body: PlayCricketSyncRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SyncAllResult:
    require_admin(current_user, club_id)
    _, site_id = await _get_club_site_id(db, club_id)
    client = _create_client()
    async with client:
        service = PlayCricketSyncService(db, club_id, client)
        return await service.sync_all(site_id, body.season)
