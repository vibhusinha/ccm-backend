import uuid
from datetime import date, time
from decimal import Decimal

from sqlalchemy import Boolean, Date, ForeignKey, Numeric, Text, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, ClubScopedMixin, TimestampMixin


class FixtureSeries(Base, ClubScopedMixin, TimestampMixin):
    __tablename__ = "fixture_series"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fixture_type_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("fixture_types.id", ondelete="SET NULL")
    )
    season_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), index=True
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    recurrence_rule: Mapped[str | None] = mapped_column(Text)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    default_time: Mapped[time] = mapped_column(Time, default=time(18, 30))
    default_venue: Mapped[str | None] = mapped_column(Text)
    default_is_home: Mapped[bool] = mapped_column(Boolean, default=True)
    default_team_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), index=True
    )
    default_fee_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
