from uuid import UUID

from pydantic import BaseModel


class ClubMatchStatisticsRead(BaseModel):
    total_matches: int
    completed_matches: int
    won: int
    lost: int
    tied: int
    drawn: int
    abandoned: int
    no_result: int
    win_percentage: float
    total_runs_scored: int
    total_runs_conceded: int


class TeamMatchStatisticsRead(BaseModel):
    team_id: UUID
    team_name: str
    total_matches: int
    won: int
    lost: int
    tied: int
    drawn: int
    win_percentage: float
    recent_form: str


class MatchTypeStatisticsRead(BaseModel):
    fixture_type_id: UUID | None
    fixture_type_name: str | None
    total_matches: int
    won: int
    lost: int
    tied: int
    drawn: int
    win_percentage: float


class PlayerMatchRecordRead(BaseModel):
    player_id: UUID
    player_name: str
    team_name: str | None
    matches_played: int
    wins: int
    losses: int
    ties: int
    draws: int
    win_percentage: float


class RecentMatchResultRead(BaseModel):
    match_id: UUID
    match_date: str
    team_name: str | None
    opponent: str
    venue: str
    our_score: str | None
    opponent_score: str | None
    result: str | None
    result_margin: int | None
    result_margin_type: str | None
    fixture_type_name: str | None
