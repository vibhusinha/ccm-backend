import uuid
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, Numeric, SmallInteger, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class MatchInnings(Base, TimestampMixin):
    __tablename__ = "match_innings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("matches.id", ondelete="CASCADE"), nullable=False
    )
    innings_number: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    batting_team: Mapped[str] = mapped_column(String(20), nullable=False)
    total_runs: Mapped[int] = mapped_column(Integer, default=0)
    total_wickets: Mapped[int] = mapped_column(Integer, default=0)
    total_overs: Mapped[Decimal] = mapped_column(Numeric(5, 1), default=Decimal("0"))
    extras_byes: Mapped[int] = mapped_column(Integer, default=0)
    extras_leg_byes: Mapped[int] = mapped_column(Integer, default=0)
    extras_wides: Mapped[int] = mapped_column(Integer, default=0)
    extras_no_balls: Mapped[int] = mapped_column(Integer, default=0)
    extras_penalty: Mapped[int] = mapped_column(Integer, default=0)
    declared: Mapped[bool] = mapped_column(Boolean, default=False)
    all_out: Mapped[bool] = mapped_column(Boolean, default=False)

    __table_args__ = (
        UniqueConstraint("match_id", "innings_number", name="uq_innings_match_number"),
        CheckConstraint("innings_number IN (1, 2)", name="ck_innings_number"),
        CheckConstraint("batting_team IN ('home', 'opposition')", name="ck_innings_batting_team"),
    )
