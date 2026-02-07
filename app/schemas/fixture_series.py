from datetime import date, datetime, time
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class FixtureSeriesRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    club_id: UUID
    fixture_type_id: UUID | None
    season_id: UUID | None
    name: str
    recurrence_rule: str | None
    start_date: date
    end_date: date
    default_time: time
    default_venue: str | None
    default_is_home: bool
    default_team_id: UUID | None
    default_fee_amount: Decimal
    created_at: datetime
    updated_at: datetime


class FixtureSeriesCreate(BaseModel):
    fixture_type_id: UUID | None = None
    season_id: UUID | None = None
    name: str
    recurrence_rule: str | None = None
    start_date: date
    end_date: date
    default_time: time = time(18, 30)
    default_venue: str | None = None
    default_is_home: bool = True
    default_team_id: UUID | None = None
    default_fee_amount: Decimal = Decimal("0")


class FixtureSeriesUpdate(BaseModel):
    fixture_type_id: UUID | None = None
    season_id: UUID | None = None
    name: str | None = None
    recurrence_rule: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    default_time: time | None = None
    default_venue: str | None = None
    default_is_home: bool | None = None
    default_team_id: UUID | None = None
    default_fee_amount: Decimal | None = None
