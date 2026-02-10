import datetime as dt
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class MatchRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    club_id: UUID
    season_id: UUID | None
    team_id: UUID | None
    fixture_type_id: UUID | None
    series_id: UUID | None
    date: dt.date
    time: dt.time
    opponent: str
    venue: str
    type: str
    status: str
    fee_amount: Decimal
    our_score: str | None
    opponent_score: str | None
    man_of_match_id: UUID | None
    match_report: str | None
    result: str | None = None
    result_margin: int | None = None
    result_margin_type: str | None = None
    toss_won_by: str | None = None
    toss_decision: str | None = None
    home_batted_first: bool | None = None
    location_name: str | None = None
    location_address: str | None = None
    location_postcode: str | None = None
    created_at: dt.datetime
    updated_at: dt.datetime


class MatchCreate(BaseModel):
    team_id: UUID
    date: dt.date
    time: dt.time = dt.time(14, 0)
    opponent: str = Field(..., max_length=255)
    venue: str = Field(..., pattern="^(Home|Away)$")
    type: str = Field(..., pattern="^(League|Friendly|T20|Net Session)$")
    season_id: UUID | None = None
    fixture_type_id: UUID | None = None
    fee_amount: Decimal = Decimal("0.00")


class MatchUpdate(BaseModel):
    team_id: UUID | None = None
    date: dt.date | None = None
    time: dt.time | None = None
    opponent: str | None = None
    venue: str | None = Field(None, pattern="^(Home|Away)$")
    type: str | None = Field(None, pattern="^(League|Friendly|T20|Net Session)$")
    season_id: UUID | None = None
    fixture_type_id: UUID | None = None
    series_id: UUID | None = None
    fee_amount: Decimal | None = None
    status: str | None = None
    our_score: str | None = None
    opponent_score: str | None = None
    man_of_match_id: UUID | None = None
    match_report: str | None = None
