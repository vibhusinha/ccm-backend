from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


# --- Opposition Players ---

class OppositionPlayerCreate(BaseModel):
    name: str
    role: str | None = None
    batting_position: int | None = None
    bowling_position: int | None = None


class OppositionPlayerRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    match_id: UUID
    name: str
    role: str | None
    batting_position: int | None
    bowling_position: int | None


# --- Innings ---

class SaveInningsInput(BaseModel):
    innings_number: int
    batting_team: str
    total_runs: int = 0
    total_wickets: int = 0
    total_overs: Decimal = Decimal("0")
    extras_byes: int = 0
    extras_leg_byes: int = 0
    extras_wides: int = 0
    extras_no_balls: int = 0
    extras_penalty: int = 0
    declared: bool = False
    all_out: bool = False


class InningsRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    match_id: UUID
    innings_number: int
    batting_team: str
    total_runs: int
    total_wickets: int
    total_overs: Decimal
    extras_byes: int
    extras_leg_byes: int
    extras_wides: int
    extras_no_balls: int
    extras_penalty: int
    declared: bool
    all_out: bool


# --- Fall of Wickets ---

class SaveFallOfWicketInput(BaseModel):
    wicket_number: int
    score_at_fall: int
    overs_at_fall: Decimal | None = None
    batsman_out_player_id: UUID | None = None
    batsman_out_opposition_id: UUID | None = None


class FallOfWicketRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    innings_id: UUID
    wicket_number: int
    score_at_fall: int
    overs_at_fall: Decimal | None
    batsman_out_player_id: UUID | None
    batsman_out_opposition_id: UUID | None


# --- Batting / Bowling Entries ---

class BattingEntryRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    innings_id: UUID
    player_id: UUID | None
    opposition_player_id: UUID | None
    batting_position: int | None
    runs_scored: int
    balls_faced: int
    fours: int
    sixes: int
    dismissal_type: str | None
    how_out: str | None
    not_out: bool
    strike_rate: Decimal


class BowlingEntryRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    innings_id: UUID
    player_id: UUID | None
    opposition_player_id: UUID | None
    bowling_position: int | None
    overs_bowled: Decimal
    maidens: int
    runs_conceded: int
    wickets_taken: int
    wides: int
    no_balls: int
    economy: Decimal


# --- Home Player Stats Input ---

class SaveHomePlayerStatsInput(BaseModel):
    player_id: UUID
    innings_id: UUID | None = None
    runs_scored: int | None = None
    balls_faced: int | None = None
    fours: int | None = None
    sixes: int | None = None
    dismissal_type: str | None = None
    how_out: str | None = None
    batting_position: int | None = None
    not_out: bool | None = None
    overs_bowled: Decimal | None = None
    runs_conceded: int | None = None
    wickets_taken: int | None = None
    maidens: int | None = None
    wides: int | None = None
    no_balls: int | None = None
    bowling_position: int | None = None


# --- Opposition Player Stats Input ---

class SaveOppositionStatsInput(BaseModel):
    opposition_player_id: UUID
    innings_id: UUID | None = None
    runs_scored: int | None = None
    balls_faced: int | None = None
    fours: int | None = None
    sixes: int | None = None
    dismissal_type: str | None = None
    batting_position: int | None = None
    overs_bowled: Decimal | None = None
    runs_conceded: int | None = None
    wickets_taken: int | None = None
    maidens: int | None = None
    wides: int | None = None
    no_balls: int | None = None
    bowling_position: int | None = None


# --- Match Result ---

class UpdateMatchResultInput(BaseModel):
    result: str
    result_margin: int | None = None
    result_margin_type: str | None = None
    our_score: str | None = None
    opponent_score: str | None = None
    toss_won_by: str | None = None
    toss_decision: str | None = None
    home_batted_first: bool | None = None
    man_of_match_id: UUID | None = None
    match_report: str | None = None


# --- Scorecard (composite read) ---

class ScorecardMatchInfo(BaseModel):
    id: UUID
    date: str
    time: str | None
    opponent: str
    venue: str
    fixture_type: str | None
    team_name: str | None
    our_score: str | None
    opponent_score: str | None
    result: str | None
    result_margin: int | None
    result_margin_type: str | None
    toss_won_by: str | None
    toss_decision: str | None
    home_batted_first: bool | None
    man_of_match_id: str | None
    man_of_match_name: str | None
    match_report: str | None
    status: str


class MatchScorecardRead(BaseModel):
    match: ScorecardMatchInfo
    innings: list[InningsRead]
    home_batting: list[BattingEntryRead]
    home_bowling: list[BowlingEntryRead]
    opposition_players: list[OppositionPlayerRead]
    opposition_batting: list[BattingEntryRead]
    opposition_bowling: list[BowlingEntryRead]


# --- Matches for Scoring list ---

class MatchForScoringRead(BaseModel):
    match_id: UUID
    match_date: str
    match_time: str | None
    opponent: str
    venue: str
    fixture_type: str | None
    team_name: str | None
    our_score: str | None
    opponent_score: str | None
    result: str | None
    has_scorecard: bool
