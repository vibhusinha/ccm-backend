import uuid

from sqlalchemy import Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class FeeConfig(Base, TimestampMixin):
    __tablename__ = "fee_configs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    club_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        unique=True,
        index=True,
    )
    membership_fee: Mapped[float] = mapped_column(Numeric(10, 2), default=150.00)
    match_fee: Mapped[float] = mapped_column(Numeric(10, 2), default=15.00)
    nets_fee: Mapped[float] = mapped_column(Numeric(10, 2), default=5.00)
    meeting_fee: Mapped[float] = mapped_column(Numeric(10, 2), default=10.00)
    event_fee: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00)
    merchandise_fee: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00)
