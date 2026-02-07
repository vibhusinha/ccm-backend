import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, Date, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, ClubScopedMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.club import Club


class Season(Base, ClubScopedMixin, TimestampMixin):
    __tablename__ = "seasons"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)

    club: Mapped["Club"] = relationship(back_populates="seasons")

    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'active', 'completed')",
            name="ck_season_status",
        ),
    )
