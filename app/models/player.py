import uuid
from datetime import date

from sqlalchemy import Boolean, CheckConstraint, Date, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, ClubScopedMixin, TimestampMixin


class Player(Base, ClubScopedMixin, TimestampMixin):
    __tablename__ = "players"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), index=True
    )
    club_member_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    address: Mapped[str | None] = mapped_column(Text)
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    role: Mapped[str] = mapped_column(String(30), nullable=False)
    team_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id", ondelete="SET NULL")
    )
    is_core: Mapped[bool] = mapped_column(Boolean, default=False)
    member_since: Mapped[date | None] = mapped_column(Date, server_default=text("CURRENT_DATE"))
    play_cricket_id: Mapped[int | None] = mapped_column(Integer, unique=True)

    __table_args__ = (
        CheckConstraint(
            "role IN ('Batter', 'Bowler', 'All-rounder', 'Wicket-keeper')",
            name="ck_player_role",
        ),
    )
