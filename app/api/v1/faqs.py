from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import NotFoundError
from app.core.permissions import require_admin, require_member
from app.schemas.auth import CurrentUser
from app.schemas.faq import FAQCreate, FAQRead, FAQUpdate
from app.services.faq_service import FAQService

router = APIRouter(prefix="/clubs/{club_id}/faqs", tags=["faqs"])


@router.get("/", response_model=list[FAQRead])
async def list_faqs(
    club_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    published_only: bool = Query(True),
) -> list[FAQRead]:
    require_member(current_user, club_id)
    service = FAQService(db, club_id)
    faqs = await service.get_all(published_only=published_only)
    return [FAQRead.model_validate(f) for f in faqs]


@router.post("/", response_model=FAQRead, status_code=201)
async def create_faq(
    club_id: Annotated[UUID, Path()],
    body: FAQCreate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FAQRead:
    require_admin(current_user, club_id)
    service = FAQService(db, club_id)
    faq = await service.create(**body.model_dump())
    return FAQRead.model_validate(faq)


@router.patch("/{faq_id}", response_model=FAQRead)
async def update_faq(
    club_id: Annotated[UUID, Path()],
    faq_id: Annotated[UUID, Path()],
    body: FAQUpdate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FAQRead:
    require_admin(current_user, club_id)
    service = FAQService(db, club_id)
    faq = await service.update(faq_id, **body.model_dump(exclude_unset=True))
    if not faq:
        raise NotFoundError("FAQ not found")
    return FAQRead.model_validate(faq)


@router.delete("/{faq_id}", status_code=204)
async def delete_faq(
    club_id: Annotated[UUID, Path()],
    faq_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    require_admin(current_user, club_id)
    service = FAQService(db, club_id)
    if not await service.delete(faq_id):
        raise NotFoundError("FAQ not found")
