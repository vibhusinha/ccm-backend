import uuid
from datetime import date, time
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Date, ForeignKey, Numeric, String, Text, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, ClubScopedMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.match_availability import MatchAvailability
    from app.models.team import Team
    from app.models.team_selection import TeamSelection


class Match(Base, ClubScopedMixin, TimestampMixin):
    __tablename__ = "matches"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    season_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("seasons.id", ondelete="SET NULL")
    )
    team_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), index=True
    )
    fixture_type_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("fixture_types.id", ondelete="SET NULL")
    )
    series_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("fixture_series.id", ondelete="SET NULL")
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    time: Mapped[time] = mapped_column(Time, nullable=False)
    opponent: Mapped[str] = mapped_column(String(255), nullable=False)
    venue: Mapped[str] = mapped_column(String(10), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="upcoming")
    fee_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
    our_score: Mapped[str | None] = mapped_column(String(50))
    opponent_score: Mapped[str | None] = mapped_column(String(50))
    man_of_match_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("players.id", ondelete="SET NULL")
    )
    match_report: Mapped[str | None] = mapped_column(Text)
    result: Mapped[str | None] = mapped_column(String(20))
    result_margin: Mapped[int | None] = mapped_column()
    result_margin_type: Mapped[str | None] = mapped_column(String(10))
    toss_won_by: Mapped[str | None] = mapped_column(String(20))
    toss_decision: Mapped[str | None] = mapped_column(String(10))
    home_batted_first: Mapped[bool | None] = mapped_column()
    location_name: Mapped[str | None] = mapped_column(String(200))
    location_address: Mapped[str | None] = mapped_column(Text)
    location_postcode: Mapped[str | None] = mapped_column(String(20))

    team: Mapped["Team | None"] = relationship(back_populates="matches")
    availability: Mapped[list["MatchAvailability"]] = relationship(back_populates="match")
    selections: Mapped[list["TeamSelection"]] = relationship(back_populates="match")

    __table_args__ = (
        CheckConstraint("venue IN ('Home', 'Away')", name="ck_match_venue"),
        CheckConstraint(
            "type IN ('League', 'Friendly', 'T20', 'Net Session')",
            name="ck_match_type",
        ),
        CheckConstraint(
            "status IN ('upcoming', 'in-progress', 'completed', 'cancelled')",
            name="ck_match_status",
        ),
    )
