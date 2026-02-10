from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class PlayerFixtureLifecycleRead(BaseModel):
    player_id: UUID
    player_name: str
    player_role: str
    availability_status: str | None
    availability_reason: str | None
    is_selected: bool
    selection_status: str | None
    not_selected_reason: str | None
    participation_status: str | None
    was_substitute: bool
    has_payment: bool
    payment_status: str | None
    payment_reference: str | None


class DeadlineAlertRead(BaseModel):
    alert_id: str
    match_id: UUID
    match_date: str
    match_description: str
    opponent_name: str | None
    team_name: str | None
    deadline_at: str
    hours_until_deadline: float
    available_count: int
    selected_count: int
    target_players: int


class AuditLogEntryRead(BaseModel):
    id: UUID
    player_id: UUID | None
    player_name: str | None
    action: str
    previous_state: str | None
    new_state: str | None
    actor_id: UUID | None
    actor_name: str | None
    actor_type: str
    reason: str | None
    details: dict | None
    created_at: datetime


class ParticipationRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    match_id: UUID
    player_id: UUID
    player_name: str | None = None
    player_role: str | None = None
    status: str
    was_substitute: bool
    substitute_for_player_id: UUID | None
    substitute_for_player_name: str | None = None
    withdrawal_reason: str | None
    no_show_reason: str | None
    confirmed_at: datetime


class ParticipationInput(BaseModel):
    player_id: UUID
    status: str
    was_substitute: bool = False
    substitute_for_player_id: UUID | None = None
    no_show_reason: str | None = None


class ConfirmParticipationInput(BaseModel):
    participations: list[ParticipationInput]


class WithdrawalInput(BaseModel):
    player_id: UUID
    reason: str


class SubstituteInput(BaseModel):
    player_id: UUID
    replaces_player_id: UUID | None = None


class AbandonedInput(BaseModel):
    reason: str | None = None


class PlayerSelectionStatsRead(BaseModel):
    player_id: UUID
    matches_available: int
    matches_selected: int
    matches_played: int
    selection_rate: float
    no_shows: int
    withdrawals: int
    late_withdrawals: int


class MemberAvailabilitySummaryRead(BaseModel):
    player_id: UUID
    player_name: str
    player_role: str
    team_name: str | None
    availability_status: str | None
    is_selected: bool
