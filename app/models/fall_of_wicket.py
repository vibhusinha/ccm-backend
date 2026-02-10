import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class FallOfWicket(Base):
    __tablename__ = "fall_of_wickets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    innings_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("match_innings.id", ondelete="CASCADE"), nullable=False
    )
    wicket_number: Mapped[int] = mapped_column(Integer, nullable=False)
    score_at_fall: Mapped[int] = mapped_column(Integer, nullable=False)
    overs_at_fall: Mapped[Decimal | None] = mapped_column(Numeric(5, 1))
    batsman_out_player_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), index=True
    )
    batsman_out_opposition_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("match_opposition_players.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
