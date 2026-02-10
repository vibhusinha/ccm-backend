from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.permissions import require_admin, require_member
from app.schemas.auth import CurrentUser
from app.schemas.fee_config import FeeConfigRead, FeeConfigUpdate
from app.services.fee_config_service import FeeConfigService

router = APIRouter(prefix="/clubs/{club_id}/fee-config", tags=["fee-config"])


@router.get("/", response_model=FeeConfigRead)
async def get_fee_config(
    club_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FeeConfigRead:
    require_member(current_user, club_id)
    service = FeeConfigService(db, club_id)
    config = await service.get_config()
    return FeeConfigRead(**config)


@router.post("/", response_model=FeeConfigRead)
async def update_fee_config(
    club_id: Annotated[UUID, Path()],
    body: FeeConfigUpdate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FeeConfigRead:
    require_admin(current_user, club_id)
    service = FeeConfigService(db, club_id)
    config = await service.upsert_config(**body.model_dump(exclude_unset=True))
    return FeeConfigRead(**config)
