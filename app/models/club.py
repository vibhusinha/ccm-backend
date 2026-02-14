import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.season import Season
    from app.models.team import Team


class Club(Base, TimestampMixin):
    __tablename__ = "clubs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    logo_url: Mapped[str | None] = mapped_column(Text)
    primary_color: Mapped[str] = mapped_column(String(7), default="#1a7f5f")
    secondary_color: Mapped[str] = mapped_column(String(7), default="#f0f7f4")
    accent_color: Mapped[str] = mapped_column(String(7), default="#e6f4ef")
    logo_storage_path: Mapped[str | None] = mapped_column(Text)
    subscription_tier: Mapped[str] = mapped_column(String(20), default="free")
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(20), server_default="active", nullable=False)
    suspended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    suspension_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    play_cricket_id: Mapped[int | None] = mapped_column(Integer, unique=True)

    seasons: Mapped[list["Season"]] = relationship(back_populates="club")
    teams: Mapped[list["Team"]] = relationship(back_populates="club")

    __table_args__ = (
        CheckConstraint(
            "subscription_tier IN ('free', 'pro', 'enterprise')",
            name="ck_club_subscription_tier",
        ),
    )
