from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class PaymentRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    club_id: UUID
    player_id: UUID
    match_id: UUID | None
    type: str
    amount: Decimal
    status: str
    due_date: date | None
    paid_date: date | None
    waived_reason: str | None
    reduced_from: Decimal | None
    reduce_reason: str | None
    bank_reference: str | None
    received_date: date | None
    season_id: UUID | None
    created_at: datetime
    updated_at: datetime


class PaymentWaive(BaseModel):
    reason: str


class PaymentReduce(BaseModel):
    new_amount: Decimal
    reason: str


class PaymentReconcile(BaseModel):
    bank_reference: str
    received_date: date


class PaymentStatusUpdate(BaseModel):
    status: str
    paid_date: date | None = None


class ClubFinanceSummary(BaseModel):
    total_received: Decimal
    total_pending: Decimal
    total_overdue: Decimal
    total_waived: Decimal
    player_count: int
    paid_player_count: int


class PlayerPaymentSummary(BaseModel):
    player_id: UUID
    player_name: str
    total_paid: Decimal
    total_pending: Decimal
    total_overdue: Decimal
    last_payment_date: date | None
