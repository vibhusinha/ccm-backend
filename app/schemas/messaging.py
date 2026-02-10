from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


# --- Channels ---

class ChannelRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    club_id: UUID
    name: str
    description: str | None
    channel_type: str
    is_default: bool
    created_by: UUID | None


class ChannelCreate(BaseModel):
    name: str
    description: str | None = None
    channel_type: str = "general"


# --- Messages ---

class MessageRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    channel_id: UUID
    sender_id: UUID | None
    content: str
    is_pinned: bool
    is_deleted: bool
    created_at: datetime | None = None
    sender_name: str | None = None
    reactions: list[dict] | None = None


class MessageCreate(BaseModel):
    content: str


class MessageTogglePin(BaseModel):
    is_pinned: bool


# --- Polls ---

class PollOptionInput(BaseModel):
    text: str


class PollCreate(BaseModel):
    question: str
    options: list[PollOptionInput]
    allow_multiple: bool = False


class PollOptionRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    text: str
    display_order: int
    vote_count: int = 0
    voted_by_me: bool = False


class PollRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    channel_id: UUID
    club_id: UUID
    created_by: UUID | None
    question: str
    is_closed: bool
    allow_multiple: bool
    created_at: datetime | None = None
    options: list[PollOptionRead] = []
    creator_name: str | None = None


# --- Reactions ---

class ReactionCreate(BaseModel):
    emoji: str
