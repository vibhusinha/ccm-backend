from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import NotFoundError
from app.core.permissions import require_admin, require_member
from app.schemas.auth import CurrentUser
from app.schemas.club_member import ClubMemberCreate, ClubMemberRead, ClubMemberUpdate
from app.services.member_service import MemberService

router = APIRouter(prefix="/clubs/{club_id}/members", tags=["members"])


@router.get("/", response_model=list[ClubMemberRead])
async def list_members(
    club_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> list[ClubMemberRead]:
    require_member(current_user, club_id)
    service = MemberService(db, club_id)
    members = await service.get_all(offset=offset, limit=limit)
    return [ClubMemberRead.model_validate(m) for m in members]


@router.post("/", response_model=ClubMemberRead, status_code=201)
async def add_member(
    club_id: Annotated[UUID, Path()],
    body: ClubMemberCreate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ClubMemberRead:
    require_admin(current_user, club_id)
    service = MemberService(db, club_id)
    member = await service.add_member(user_id=body.user_id, role=body.role)
    return ClubMemberRead.model_validate(member)


@router.patch("/{member_id}", response_model=ClubMemberRead)
async def update_member_role(
    club_id: Annotated[UUID, Path()],
    member_id: Annotated[UUID, Path()],
    body: ClubMemberUpdate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ClubMemberRead:
    require_admin(current_user, club_id)
    service = MemberService(db, club_id)
    member = await service.update_role(member_id, body.role)
    return ClubMemberRead.model_validate(member)


@router.delete("/{member_id}", status_code=204)
async def remove_member(
    club_id: Annotated[UUID, Path()],
    member_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    require_admin(current_user, club_id)
    service = MemberService(db, club_id)
    if not await service.remove_member(member_id):
        raise NotFoundError("Member not found")
