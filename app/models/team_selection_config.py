import uuid
from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class TeamSelectionConfig(Base, TimestampMixin):
    __tablename__ = "team_selection_config"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    club_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clubs.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    performance_weight: Mapped[Decimal] = mapped_column(Numeric(4, 2), default=Decimal("0.30"))
    fairness_weight: Mapped[Decimal] = mapped_column(Numeric(4, 2), default=Decimal("0.25"))
    attendance_weight: Mapped[Decimal] = mapped_column(Numeric(4, 2), default=Decimal("0.20"))
    reliability_weight: Mapped[Decimal] = mapped_column(Numeric(4, 2), default=Decimal("0.15"))
    season_distribution_weight: Mapped[Decimal] = mapped_column(Numeric(4, 2), default=Decimal("0.10"))
    late_withdrawal_hours: Mapped[int] = mapped_column(Integer, default=48)
    late_withdrawal_penalty: Mapped[Decimal] = mapped_column(Numeric(4, 2), default=Decimal("0.10"))
    max_late_withdrawal_penalty: Mapped[Decimal] = mapped_column(Numeric(4, 2), default=Decimal("0.50"))
    min_attendance_score: Mapped[Decimal] = mapped_column(Numeric(4, 2), default=Decimal("0.00"))
    max_attendance_bonus: Mapped[Decimal] = mapped_column(Numeric(4, 2), default=Decimal("0.20"))
    default_match_overs: Mapped[int] = mapped_column(Integer, default=50)
    min_keepers: Mapped[int] = mapped_column(Integer, default=1)
    max_keepers: Mapped[int] = mapped_column(Integer, default=1)
    min_batters: Mapped[int] = mapped_column(Integer, default=4)
    max_batters: Mapped[int] = mapped_column(Integer, default=6)
    min_allrounders: Mapped[int] = mapped_column(Integer, default=1)
    max_allrounders: Mapped[int] = mapped_column(Integer, default=3)
    min_bowlers: Mapped[int] = mapped_column(Integer, default=3)
    max_bowlers: Mapped[int] = mapped_column(Integer, default=5)
    min_bowling_options: Mapped[int] = mapped_column(Integer, default=5)
    auto_select_captain: Mapped[bool] = mapped_column(Boolean, default=False)
    auto_select_vice_captain: Mapped[bool] = mapped_column(Boolean, default=False)
    default_base_score: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=Decimal("50.00"))
    performance_bonus_runs_threshold: Mapped[int] = mapped_column(Integer, default=50)
    performance_bonus_runs_points: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=Decimal("5.00"))
    performance_bonus_wickets_threshold: Mapped[int] = mapped_column(Integer, default=3)
    performance_bonus_wickets_points: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=Decimal("5.00"))
    absence_penalty_points: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=Decimal("2.00"))
