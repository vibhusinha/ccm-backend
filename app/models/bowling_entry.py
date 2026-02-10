import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class BowlingEntry(Base):
    __tablename__ = "bowling_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    innings_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("match_innings.id", ondelete="CASCADE"), nullable=False
    )
    player_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("players.id", ondelete="SET NULL")
    )
    opposition_player_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("match_opposition_players.id", ondelete="SET NULL")
    )
    bowling_position: Mapped[int | None] = mapped_column(Integer)
    overs_bowled: Mapped[Decimal] = mapped_column(Numeric(5, 1), default=Decimal("0"))
    maidens: Mapped[int] = mapped_column(Integer, default=0)
    runs_conceded: Mapped[int] = mapped_column(Integer, default=0)
    wickets_taken: Mapped[int] = mapped_column(Integer, default=0)
    wides: Mapped[int] = mapped_column(Integer, default=0)
    no_balls: Mapped[int] = mapped_column(Integer, default=0)
    economy: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.00"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
