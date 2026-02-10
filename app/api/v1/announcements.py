from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import NotFoundError
from app.core.permissions import require_admin, require_member
from app.schemas.announcement import AnnouncementCreate, AnnouncementRead, AnnouncementUpdate
from app.schemas.auth import CurrentUser
from app.services.announcement_service import AnnouncementService

router = APIRouter(prefix="/clubs/{club_id}/announcements", tags=["announcements"])


@router.get("/", response_model=list[AnnouncementRead])
async def list_announcements(
    club_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    include_archived: bool = Query(False),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> list[AnnouncementRead]:
    require_member(current_user, club_id)
    service = AnnouncementService(db, club_id)
    announcements = await service.get_all(
        offset=offset, limit=limit, include_archived=include_archived
    )
    return [AnnouncementRead.model_validate(a) for a in announcements]


@router.post("/", response_model=AnnouncementRead, status_code=201)
async def create_announcement(
    club_id: Annotated[UUID, Path()],
    body: AnnouncementCreate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AnnouncementRead:
    require_admin(current_user, club_id)
    service = AnnouncementService(db, club_id)
    announcement = await service.create(
        created_by=current_user.user_id,
        **body.model_dump(),
    )
    return AnnouncementRead.model_validate(announcement)


@router.patch("/{announcement_id}", response_model=AnnouncementRead)
async def update_announcement(
    club_id: Annotated[UUID, Path()],
    announcement_id: Annotated[UUID, Path()],
    body: AnnouncementUpdate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AnnouncementRead:
    require_admin(current_user, club_id)
    service = AnnouncementService(db, club_id)
    announcement = await service.update(
        announcement_id, **body.model_dump(exclude_unset=True)
    )
    if not announcement:
        raise NotFoundError("Announcement not found")
    return AnnouncementRead.model_validate(announcement)


@router.delete("/{announcement_id}", status_code=204)
async def delete_announcement(
    club_id: Annotated[UUID, Path()],
    announcement_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    require_admin(current_user, club_id)
    service = AnnouncementService(db, club_id)
    if not await service.delete(announcement_id):
        raise NotFoundError("Announcement not found")
