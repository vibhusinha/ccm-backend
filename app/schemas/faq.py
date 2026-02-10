from uuid import UUID

from pydantic import BaseModel


class FAQRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    club_id: UUID
    question: str
    answer: str
    display_order: int
    is_published: bool


class FAQCreate(BaseModel):
    question: str
    answer: str
    display_order: int = 0
    is_published: bool = True


class FAQUpdate(BaseModel):
    question: str | None = None
    answer: str | None = None
    display_order: int | None = None
    is_published: bool | None = None
