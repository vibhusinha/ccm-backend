from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


# --- Player Recommendation ---

class PlayerRecommendationRead(BaseModel):
    player_id: UUID
    player_name: str
    player_role: str
    is_paid: bool
    availability_status: str | None
    performance_score: float
    fairness_score: float
    attendance_score: float
    reliability_score: float
    season_distribution_score: float
    composite_score: float
    batting_score: float
    bowling_score: float
    recommended_batting_position: int | None
    recommended_bowling_position: int | None
    is_recommended: bool
    recommendation_reason: str | None
    is_reserve: bool
    reserve_priority: int | None
    base_score: float
    is_captain: bool
    is_vice_captain: bool


# --- Player Match Stats ---

class PlayerMatchStatsRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    player_id: UUID
    match_id: UUID
    player_name: str | None = None
    player_role: str | None = None
    runs_scored: int
    balls_faced: int
    fours: int
    sixes: int
    not_out: bool
    batting_position: int | None
    how_out: str | None
    overs_bowled: Decimal
    runs_conceded: int
    wickets: int
    maidens: int
    wides: int
    no_balls: int
    bowling_position: int | None
    catches: int
    run_outs: int
    stumpings: int


class SavePlayerMatchStatsInput(BaseModel):
    player_id: UUID
    stats: dict


# --- Player Match History ---

class PlayerMatchHistoryRead(BaseModel):
    id: UUID
    player_id: UUID
    match_id: UUID
    match_date: str
    opponent: str
    venue: str
    runs_scored: int
    balls_faced: int
    fours: int
    sixes: int
    not_out: bool
    batting_position: int | None
    how_out: str | None
    overs_bowled: Decimal
    runs_conceded: int
    wickets: int
    maidens: int
    catches: int
    run_outs: int
    stumpings: int


# --- Team Selection Config ---

class TeamSelectionConfigRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    club_id: UUID
    performance_weight: Decimal
    fairness_weight: Decimal
    attendance_weight: Decimal
    reliability_weight: Decimal
    season_distribution_weight: Decimal
    late_withdrawal_hours: int
    late_withdrawal_penalty: Decimal
    max_late_withdrawal_penalty: Decimal
    min_attendance_score: Decimal
    max_attendance_bonus: Decimal
    default_match_overs: int
    min_keepers: int
    max_keepers: int
    min_batters: int
    max_batters: int
    min_allrounders: int
    max_allrounders: int
    min_bowlers: int
    max_bowlers: int
    min_bowling_options: int
    auto_select_captain: bool
    auto_select_vice_captain: bool
    default_base_score: Decimal
    performance_bonus_runs_threshold: int
    performance_bonus_runs_points: Decimal
    performance_bonus_wickets_threshold: int
    performance_bonus_wickets_points: Decimal
    absence_penalty_points: Decimal


class TeamSelectionConfigUpdate(BaseModel):
    performance_weight: Decimal | None = None
    fairness_weight: Decimal | None = None
    attendance_weight: Decimal | None = None
    reliability_weight: Decimal | None = None
    season_distribution_weight: Decimal | None = None
    late_withdrawal_hours: int | None = None
    late_withdrawal_penalty: Decimal | None = None
    max_late_withdrawal_penalty: Decimal | None = None
    min_attendance_score: Decimal | None = None
    max_attendance_bonus: Decimal | None = None
    default_match_overs: int | None = None
    min_keepers: int | None = None
    max_keepers: int | None = None
    min_batters: int | None = None
    max_batters: int | None = None
    min_allrounders: int | None = None
    max_allrounders: int | None = None
    min_bowlers: int | None = None
    max_bowlers: int | None = None
    min_bowling_options: int | None = None
    auto_select_captain: bool | None = None
    auto_select_vice_captain: bool | None = None
    default_base_score: Decimal | None = None
    performance_bonus_runs_threshold: int | None = None
    performance_bonus_runs_points: Decimal | None = None
    performance_bonus_wickets_threshold: int | None = None
    performance_bonus_wickets_points: Decimal | None = None
    absence_penalty_points: Decimal | None = None


# --- Player Selection Override ---

class PlayerSelectionOverrideRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    player_id: UUID
    club_id: UUID
    base_score_override: Decimal
    notes: str | None
    player_name: str | None = None
    player_role: str | None = None
    is_core: bool | None = None


class PlayerSelectionOverrideCreate(BaseModel):
    player_id: UUID
    base_score_override: Decimal
    notes: str | None = None


# --- Practice Attendance ---

class PracticeAttendanceInput(BaseModel):
    player_id: UUID
    status: str
    notes: str | None = None


class RecordPracticeAttendanceInput(BaseModel):
    attendances: list[PracticeAttendanceInput]


# --- Selection Withdrawal ---

class SelectionWithdrawalInput(BaseModel):
    player_id: UUID
    match_time: str
    reason: str | None = None


# --- Simulation Status ---

class SimulationStatusRead(BaseModel):
    total_upcoming_matches: int
    matches_with_selections: int
    matches_without_selections: int
    next_match_date: str | None
    next_match_opponent: str | None
    next_match_has_selections: bool


# --- Recommendation Result ---

class RecommendationResultRead(BaseModel):
    match_id: UUID | None
    match_date: str | None
    opponent: str | None
    team_name: str | None
    players_recommended: int
    message: str | None = None
