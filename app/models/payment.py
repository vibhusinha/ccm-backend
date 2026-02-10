import uuid
from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, ForeignKey, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, ClubScopedMixin, TimestampMixin


class Payment(Base, ClubScopedMixin, TimestampMixin):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    player_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("players.id", ondelete="CASCADE"), nullable=False
    )
    match_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("matches.id", ondelete="SET NULL")
    )
    type: Mapped[str] = mapped_column(String(30), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'pending'")
    )
    due_date: Mapped[date | None] = mapped_column(Date)
    paid_date: Mapped[date | None] = mapped_column(Date)
    waived_reason: Mapped[str | None] = mapped_column(Text)
    reduced_from: Mapped[float | None] = mapped_column(Numeric(10, 2))
    reduce_reason: Mapped[str | None] = mapped_column(Text)
    bank_reference: Mapped[str | None] = mapped_column(String(255))
    received_date: Mapped[date | None] = mapped_column(Date)
    season_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("seasons.id", ondelete="SET NULL")
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'paid', 'overdue', 'waived')",
            name="ck_payment_status",
        ),
        CheckConstraint(
            "type IN ('membership', 'match', 'nets', 'meeting', 'event', 'merchandise')",
            name="ck_payment_type",
        ),
    )
