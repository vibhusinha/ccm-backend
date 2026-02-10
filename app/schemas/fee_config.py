from decimal import Decimal

from pydantic import BaseModel


class FeeConfigRead(BaseModel):
    model_config = {"from_attributes": True}

    membership: Decimal
    match: Decimal
    nets: Decimal
    meeting: Decimal
    event: Decimal
    merchandise: Decimal


class FeeConfigUpdate(BaseModel):
    membership_fee: Decimal | None = None
    match_fee: Decimal | None = None
    nets_fee: Decimal | None = None
    meeting_fee: Decimal | None = None
    event_fee: Decimal | None = None
    merchandise_fee: Decimal | None = None
