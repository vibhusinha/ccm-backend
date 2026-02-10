"""Team recommendation tables

Revision ID: 0010
Revises: 0009
Create Date: 2026-02-09
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSON, UUID

revision: str = "0010"
down_revision: Union[str, None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # player_match_stats
    op.create_table(
        "player_match_stats",
        sa.Column(
            "id", UUID(as_uuid=True), primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "player_id", UUID(as_uuid=True),
            sa.ForeignKey("players.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "match_id", UUID(as_uuid=True),
            sa.ForeignKey("matches.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("runs_scored", sa.Integer(), server_default="0"),
        sa.Column("balls_faced", sa.Integer(), server_default="0"),
        sa.Column("fours", sa.Integer(), server_default="0"),
        sa.Column("sixes", sa.Integer(), server_default="0"),
        sa.Column("not_out", sa.Boolean(), server_default="false"),
        sa.Column("batting_position", sa.Integer(), nullable=True),
        sa.Column("how_out", sa.String(100), nullable=True),
        sa.Column("overs_bowled", sa.Numeric(5, 1), server_default="0"),
        sa.Column("runs_conceded", sa.Integer(), server_default="0"),
        sa.Column("wickets", sa.Integer(), server_default="0"),
        sa.Column("maidens", sa.Integer(), server_default="0"),
        sa.Column("wides", sa.Integer(), server_default="0"),
        sa.Column("no_balls", sa.Integer(), server_default="0"),
        sa.Column("bowling_position", sa.Integer(), nullable=True),
        sa.Column("catches", sa.Integer(), server_default="0"),
        sa.Column("run_outs", sa.Integer(), server_default="0"),
        sa.Column("stumpings", sa.Integer(), server_default="0"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("player_id", "match_id", name="uq_player_match_stats"),
    )
    op.create_index("idx_player_match_stats_player", "player_match_stats", ["player_id"])
    op.create_index("idx_player_match_stats_match", "player_match_stats", ["match_id"])

    # team_selection_config
    op.create_table(
        "team_selection_config",
        sa.Column(
            "id", UUID(as_uuid=True), primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "club_id", UUID(as_uuid=True),
            sa.ForeignKey("clubs.id", ondelete="CASCADE"), nullable=False, unique=True,
        ),
        sa.Column("performance_weight", sa.Numeric(4, 2), server_default="0.30"),
        sa.Column("fairness_weight", sa.Numeric(4, 2), server_default="0.25"),
        sa.Column("attendance_weight", sa.Numeric(4, 2), server_default="0.20"),
        sa.Column("reliability_weight", sa.Numeric(4, 2), server_default="0.15"),
        sa.Column("season_distribution_weight", sa.Numeric(4, 2), server_default="0.10"),
        sa.Column("late_withdrawal_hours", sa.Integer(), server_default="48"),
        sa.Column("late_withdrawal_penalty", sa.Numeric(4, 2), server_default="0.10"),
        sa.Column("max_late_withdrawal_penalty", sa.Numeric(4, 2), server_default="0.50"),
        sa.Column("min_attendance_score", sa.Numeric(4, 2), server_default="0.00"),
        sa.Column("max_attendance_bonus", sa.Numeric(4, 2), server_default="0.20"),
        sa.Column("default_match_overs", sa.Integer(), server_default="50"),
        sa.Column("min_keepers", sa.Integer(), server_default="1"),
        sa.Column("max_keepers", sa.Integer(), server_default="1"),
        sa.Column("min_batters", sa.Integer(), server_default="4"),
        sa.Column("max_batters", sa.Integer(), server_default="6"),
        sa.Column("min_allrounders", sa.Integer(), server_default="1"),
        sa.Column("max_allrounders", sa.Integer(), server_default="3"),
        sa.Column("min_bowlers", sa.Integer(), server_default="3"),
        sa.Column("max_bowlers", sa.Integer(), server_default="5"),
        sa.Column("min_bowling_options", sa.Integer(), server_default="5"),
        sa.Column("auto_select_captain", sa.Boolean(), server_default="false"),
        sa.Column("auto_select_vice_captain", sa.Boolean(), server_default="false"),
        sa.Column("default_base_score", sa.Numeric(6, 2), server_default="50.00"),
        sa.Column("performance_bonus_runs_threshold", sa.Integer(), server_default="50"),
        sa.Column("performance_bonus_runs_points", sa.Numeric(6, 2), server_default="5.00"),
        sa.Column("performance_bonus_wickets_threshold", sa.Integer(), server_default="3"),
        sa.Column("performance_bonus_wickets_points", sa.Numeric(6, 2), server_default="5.00"),
        sa.Column("absence_penalty_points", sa.Numeric(6, 2), server_default="2.00"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
        ),
    )

    # player_selection_overrides
    op.create_table(
        "player_selection_overrides",
        sa.Column(
            "id", UUID(as_uuid=True), primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "player_id", UUID(as_uuid=True),
            sa.ForeignKey("players.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "club_id", UUID(as_uuid=True),
            sa.ForeignKey("clubs.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("base_score_override", sa.Numeric(6, 2), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("player_id", "club_id", name="uq_override_player_club"),
    )

    # practice_attendance
    op.create_table(
        "practice_attendance",
        sa.Column(
            "id", UUID(as_uuid=True), primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "fixture_id", UUID(as_uuid=True),
            sa.ForeignKey("matches.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "player_id", UUID(as_uuid=True),
            sa.ForeignKey("players.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "recorded_by", UUID(as_uuid=True),
            sa.ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("player_id", "fixture_id", name="uq_practice_player_fixture"),
        sa.CheckConstraint(
            "status IN ('attended', 'absent', 'excused')",
            name="ck_practice_status",
        ),
    )
    op.create_index("idx_practice_attendance_fixture", "practice_attendance", ["fixture_id"])

    # selection_withdrawals
    op.create_table(
        "selection_withdrawals",
        sa.Column(
            "id", UUID(as_uuid=True), primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "match_id", UUID(as_uuid=True),
            sa.ForeignKey("matches.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "player_id", UUID(as_uuid=True),
            sa.ForeignKey("players.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("match_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("withdrawal_time", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("is_late", sa.Boolean(), server_default="false"),
        sa.Column("penalty_applied", sa.Numeric(4, 2), server_default="0.00"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("player_id", "match_id", name="uq_withdrawal_player_match"),
    )
    op.create_index("idx_selection_withdrawals_match", "selection_withdrawals", ["match_id"])


def downgrade() -> None:
    op.drop_index("idx_selection_withdrawals_match", table_name="selection_withdrawals")
    op.drop_table("selection_withdrawals")
    op.drop_index("idx_practice_attendance_fixture", table_name="practice_attendance")
    op.drop_table("practice_attendance")
    op.drop_table("player_selection_overrides")
    op.drop_table("team_selection_config")
    op.drop_index("idx_player_match_stats_match", table_name="player_match_stats")
    op.drop_index("idx_player_match_stats_player", table_name="player_match_stats")
    op.drop_table("player_match_stats")
