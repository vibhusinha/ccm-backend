import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class BattingEntry(Base):
    __tablename__ = "batting_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    innings_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("match_innings.id", ondelete="CASCADE"), nullable=False
    )
    player_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), index=True
    )
    opposition_player_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("match_opposition_players.id", ondelete="SET NULL")
    )
    batting_position: Mapped[int | None] = mapped_column(Integer)
    runs_scored: Mapped[int] = mapped_column(Integer, default=0)
    balls_faced: Mapped[int] = mapped_column(Integer, default=0)
    fours: Mapped[int] = mapped_column(Integer, default=0)
    sixes: Mapped[int] = mapped_column(Integer, default=0)
    dismissal_type: Mapped[str | None] = mapped_column(String(30))
    how_out: Mapped[str | None] = mapped_column(Text)
    not_out: Mapped[bool] = mapped_column(Boolean, default=False)
    strike_rate: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=Decimal("0.00"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
