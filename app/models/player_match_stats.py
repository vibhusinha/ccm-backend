import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class PlayerMatchStats(Base, TimestampMixin):
    __tablename__ = "player_match_stats"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    runs_scored: Mapped[int] = mapped_column(Integer, default=0)
    balls_faced: Mapped[int] = mapped_column(Integer, default=0)
    fours: Mapped[int] = mapped_column(Integer, default=0)
    sixes: Mapped[int] = mapped_column(Integer, default=0)
    not_out: Mapped[bool] = mapped_column(Boolean, default=False)
    batting_position: Mapped[int | None] = mapped_column(Integer)
    how_out: Mapped[str | None] = mapped_column(String(100))
    overs_bowled: Mapped[Decimal] = mapped_column(Numeric(5, 1), default=Decimal("0"))
    runs_conceded: Mapped[int] = mapped_column(Integer, default=0)
    wickets: Mapped[int] = mapped_column(Integer, default=0)
    maidens: Mapped[int] = mapped_column(Integer, default=0)
    wides: Mapped[int] = mapped_column(Integer, default=0)
    no_balls: Mapped[int] = mapped_column(Integer, default=0)
    bowling_position: Mapped[int | None] = mapped_column(Integer)
    catches: Mapped[int] = mapped_column(Integer, default=0)
    run_outs: Mapped[int] = mapped_column(Integer, default=0)
    stumpings: Mapped[int] = mapped_column(Integer, default=0)

    __table_args__ = (
        UniqueConstraint("player_id", "match_id", name="uq_player_match_stats"),
    )
