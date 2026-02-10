import uuid

from sqlalchemy import CheckConstraint, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class PushToken(Base, TimestampMixin):
    __tablename__ = "push_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    token: Mapped[str] = mapped_column(String(255), nullable=False)
    platform: Mapped[str] = mapped_column(String(10), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "token", name="uq_push_tokens_user_token"),
        CheckConstraint(
            "platform IN ('ios', 'android', 'web')",
            name="ck_push_token_platform",
        ),
    )
