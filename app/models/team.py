import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, ClubScopedMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.club import Club
    from app.models.match import Match
    from app.models.player import Player


class Team(Base, ClubScopedMixin, TimestampMixin):
    __tablename__ = "teams"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    division: Mapped[str | None] = mapped_column(String(100))
    division_number: Mapped[int | None] = mapped_column(Integer)
    division_group: Mapped[str | None] = mapped_column(String(1))
    captain_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("players.id", ondelete="SET NULL", use_alter=True, name="fk_teams_captain_id"),
    )
    vice_captain_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "players.id", ondelete="SET NULL", use_alter=True, name="fk_teams_vice_captain_id"
        ),
    )
    season_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("seasons.id", ondelete="SET NULL")
    )
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    club: Mapped["Club"] = relationship(back_populates="teams")
    captain: Mapped["Player | None"] = relationship(foreign_keys=[captain_id])
    vice_captain: Mapped["Player | None"] = relationship(foreign_keys=[vice_captain_id])
    matches: Mapped[list["Match"]] = relationship(back_populates="team")

    __table_args__ = (
        CheckConstraint(
            "division_number IS NULL OR (division_number >= 1 AND division_number <= 10)",
            name="ck_team_division_number",
        ),
        CheckConstraint(
            "division_group IS NULL OR division_group IN ('A', 'B', 'C', 'D')",
            name="ck_team_division_group",
        ),
    )
