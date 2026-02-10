from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import NotFoundError
from app.core.permissions import require_admin, require_member
from app.schemas.auth import CurrentUser
from app.schemas.messaging import (
    ChannelRead,
    MessageCreate,
    MessageRead,
    MessageTogglePin,
    PollCreate,
    PollRead,
    ReactionCreate,
)
from app.services.messaging_service import MessagingService

# Club-scoped channel routes
channel_router = APIRouter(prefix="/clubs/{club_id}", tags=["messaging"])

# Channel-scoped message routes
message_channel_router = APIRouter(prefix="/channels/{channel_id}", tags=["messaging"])

# Message action routes
message_action_router = APIRouter(prefix="/messages/{message_id}", tags=["messaging"])

# Poll action routes
poll_option_router = APIRouter(prefix="/poll-options/{option_id}", tags=["messaging"])
poll_action_router = APIRouter(prefix="/polls/{poll_id}", tags=["messaging"])


async def _get_channel_club_id(channel_id: UUID, db: AsyncSession) -> UUID:
    club_id = await MessagingService.get_channel_club_id(db, channel_id)
    if club_id is None:
        raise NotFoundError("Channel not found")
    return club_id


async def _get_message_club_id(message_id: UUID, db: AsyncSession) -> UUID:
    from app.models.channel import Channel
    from app.models.message import Message
    from sqlalchemy import select

    stmt = (
        select(Channel.club_id)
        .join(Message, Message.channel_id == Channel.id)
        .where(Message.id == message_id)
    )
    result = await db.execute(stmt)
    club_id = result.scalar_one_or_none()
    if club_id is None:
        raise NotFoundError("Message not found")
    return club_id


async def _get_poll_club_id(poll_id: UUID, db: AsyncSession) -> UUID:
    from app.models.poll import Poll
    from sqlalchemy import select

    stmt = select(Poll.club_id).where(Poll.id == poll_id)
    result = await db.execute(stmt)
    club_id = result.scalar_one_or_none()
    if club_id is None:
        raise NotFoundError("Poll not found")
    return club_id


async def _get_option_club_id(option_id: UUID, db: AsyncSession) -> UUID:
    from app.models.poll import Poll
    from app.models.poll_option import PollOption
    from sqlalchemy import select

    stmt = (
        select(Poll.club_id)
        .join(PollOption, PollOption.poll_id == Poll.id)
        .where(PollOption.id == option_id)
    )
    result = await db.execute(stmt)
    club_id = result.scalar_one_or_none()
    if club_id is None:
        raise NotFoundError("Poll option not found")
    return club_id


@channel_router.get("/channels", response_model=list[ChannelRead])
async def list_channels(
    club_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[ChannelRead]:
    require_member(current_user, club_id)
    service = MessagingService(db, club_id)
    channels = await service.get_channels()
    return [ChannelRead.model_validate(c) for c in channels]


@channel_router.get("/polls", response_model=list[PollRead])
async def list_club_polls(
    club_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[PollRead]:
    require_member(current_user, club_id)
    service = MessagingService(db, club_id)
    polls = await service.get_polls(current_user.user_id)
    return [PollRead(**p) for p in polls]


@message_channel_router.get("/messages", response_model=list[MessageRead])
async def list_messages(
    channel_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> list[MessageRead]:
    club_id = await _get_channel_club_id(channel_id, db)
    require_member(current_user, club_id)
    service = MessagingService(db, club_id)
    messages = await service.get_messages(channel_id, offset=offset, limit=limit)
    return [MessageRead(**m) for m in messages]


@message_channel_router.post("/messages", response_model=MessageRead)
async def send_message(
    channel_id: Annotated[UUID, Path()],
    body: MessageCreate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageRead:
    club_id = await _get_channel_club_id(channel_id, db)
    require_member(current_user, club_id)
    service = MessagingService(db, club_id)
    msg = await service.send_message(channel_id, current_user.user_id, body.content)
    return MessageRead.model_validate(msg)


@message_channel_router.post("/polls", response_model=PollRead)
async def create_poll(
    channel_id: Annotated[UUID, Path()],
    body: PollCreate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PollRead:
    club_id = await _get_channel_club_id(channel_id, db)
    require_member(current_user, club_id)
    service = MessagingService(db, club_id)
    poll = await service.create_poll(
        channel_id, current_user.user_id, body.question,
        [opt.model_dump() for opt in body.options], body.allow_multiple,
    )
    return PollRead(**poll)


@message_action_router.patch("/", response_model=MessageRead)
async def toggle_pin(
    message_id: Annotated[UUID, Path()],
    body: MessageTogglePin,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageRead:
    club_id = await _get_message_club_id(message_id, db)
    require_admin(current_user, club_id)
    service = MessagingService(db, club_id)
    msg = await service.toggle_pin(message_id, body.is_pinned)
    if not msg:
        raise NotFoundError("Message not found")
    return MessageRead.model_validate(msg)


@message_action_router.delete("/", status_code=204)
async def delete_message(
    message_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    club_id = await _get_message_club_id(message_id, db)
    require_member(current_user, club_id)
    service = MessagingService(db, club_id)
    if not await service.delete_message(message_id):
        raise NotFoundError("Message not found")


@message_action_router.post("/reactions")
async def add_reaction(
    message_id: Annotated[UUID, Path()],
    body: ReactionCreate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    club_id = await _get_message_club_id(message_id, db)
    require_member(current_user, club_id)
    service = MessagingService(db, club_id)
    return await service.add_reaction(message_id, current_user.user_id, body.emoji)


@poll_option_router.post("/vote")
async def vote_on_poll(
    option_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    club_id = await _get_option_club_id(option_id, db)
    require_member(current_user, club_id)
    service = MessagingService(db, club_id)
    return await service.vote_on_poll(option_id, current_user.user_id)


@poll_action_router.post("/close")
async def close_poll(
    poll_id: Annotated[UUID, Path()],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    club_id = await _get_poll_club_id(poll_id, db)
    require_admin(current_user, club_id)
    service = MessagingService(db, club_id)
    poll = await service.close_poll(poll_id)
    if not poll:
        raise NotFoundError("Poll not found")
    return {"success": True}
