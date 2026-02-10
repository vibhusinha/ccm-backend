import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class MatchParticipation(Base):
    __tablename__ = "match_participation"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("matches.id", ondelete="CASCADE"), nullable=False
    )
    player_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("players.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    was_substitute: Mapped[bool] = mapped_column(Boolean, default=False)
    substitute_for_player_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("players.id", ondelete="SET NULL")
    )
    withdrawal_reason: Mapped[str | None] = mapped_column(Text)
    no_show_reason: Mapped[str | None] = mapped_column(Text)
    confirmed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("match_id", "player_id", name="uq_participation_match_player"),
        CheckConstraint(
            "status IN ('played', 'no_show', 'withdrawn', 'substitute', 'match_abandoned')",
            name="ck_participation_status",
        ),
    )
