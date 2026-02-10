from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.auth import CurrentUser
from app.schemas.notification import NotificationRead, PushTokenRegister, PushTokenRemove
from app.services.notification_service import NotificationService
from app.services.push_token_service import PushTokenService

router = APIRouter(prefix="/users/{user_id}/notifications", tags=["notifications"])
notification_actions_router = APIRouter(
    prefix="/notifications/{notification_id}", tags=["notifications"]
)
reminders_router = APIRouter(prefix="/reminders", tags=["notifications"])
push_tokens_router = APIRouter(prefix="/push-tokens", tags=["notifications"])


@router.get("/", response_model=list[NotificationRead])
async def get_notifications(
    user_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[NotificationRead]:
    # Users can only see their own notifications
    if current_user.user_id != user_id and not current_user.is_platform_admin:
        from app.core.exceptions import ForbiddenError

        raise ForbiddenError("Can only view own notifications")
    service = NotificationService(db)
    notifications = await service.get_for_user(user_id)
    return [NotificationRead.model_validate(n) for n in notifications]


@router.get("/unread-count")
async def get_unread_count(
    user_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    if current_user.user_id != user_id and not current_user.is_platform_admin:
        from app.core.exceptions import ForbiddenError

        raise ForbiddenError("Can only view own notifications")
    service = NotificationService(db)
    count = await service.get_unread_count(user_id)
    return {"count": count}


@notification_actions_router.post("/mark-read")
async def mark_notification_read(
    notification_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    service = NotificationService(db)
    success = await service.mark_read(notification_id)
    return {"success": success}


@router.post("/mark-all-read")
async def mark_all_read(
    user_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    if current_user.user_id != user_id and not current_user.is_platform_admin:
        from app.core.exceptions import ForbiddenError

        raise ForbiddenError("Can only modify own notifications")
    service = NotificationService(db)
    success = await service.mark_all_read(user_id)
    return {"success": success}


@reminders_router.post("/generate")
async def generate_reminders(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    service = NotificationService(db)
    match_reminders = await service.generate_match_reminders()
    payment_reminders = await service.generate_payment_reminders()
    return {
        "matchReminders": match_reminders,
        "paymentReminders": payment_reminders,
    }


@push_tokens_router.post("/")
async def register_push_token(
    body: PushTokenRegister,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    service = PushTokenService(db)
    success = await service.register(current_user.user_id, body.token, body.platform)
    return {"success": success}


@push_tokens_router.post("/remove")
async def remove_push_token(
    body: PushTokenRemove,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    service = PushTokenService(db)
    success = await service.remove(current_user.user_id, body.token)
    return {"success": success}
