from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.permissions import require_admin_or_captain, require_member
from app.schemas.auth import CurrentUser
from app.schemas.team_selection import SelectionCreate, SelectionRead
from app.services.selection_service import SelectionService

router = APIRouter(
    prefix="/clubs/{club_id}/matches/{match_id}/selections",
    tags=["selections"],
)


@router.get("/", response_model=list[SelectionRead])
async def get_selections(
    club_id: Annotated[UUID, Path()],
    match_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[SelectionRead]:
    require_member(current_user, club_id)
    service = SelectionService(db)
    selections = await service.get_for_match(match_id)
    return [SelectionRead.model_validate(s) for s in selections]


@router.post("/", response_model=list[SelectionRead])
async def set_selections(
    club_id: Annotated[UUID, Path()],
    match_id: Annotated[UUID, Path()],
    body: list[SelectionCreate],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[SelectionRead]:
    require_admin_or_captain(current_user, club_id)
    service = SelectionService(db)
    selections = await service.set_selections(
        match_id, [s.model_dump() for s in body]
    )
    return [SelectionRead.model_validate(s) for s in selections]
