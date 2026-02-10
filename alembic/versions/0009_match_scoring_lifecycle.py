"""Match scoring and lifecycle tables

Revision ID: 0009
Revises: 0008
Create Date: 2026-02-09
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSON, UUID

revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add scoring columns to matches
    op.add_column("matches", sa.Column("result", sa.String(20), nullable=True))
    op.add_column("matches", sa.Column("result_margin", sa.Integer(), nullable=True))
    op.add_column("matches", sa.Column("result_margin_type", sa.String(10), nullable=True))
    op.add_column("matches", sa.Column("toss_won_by", sa.String(20), nullable=True))
    op.add_column("matches", sa.Column("toss_decision", sa.String(10), nullable=True))
    op.add_column("matches", sa.Column("home_batted_first", sa.Boolean(), nullable=True))

    # match_opposition_players
    op.create_table(
        "match_opposition_players",
        sa.Column(
            "id", UUID(as_uuid=True), primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "match_id", UUID(as_uuid=True),
            sa.ForeignKey("matches.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("role", sa.String(30), nullable=True),
        sa.Column("batting_position", sa.Integer(), nullable=True),
        sa.Column("bowling_position", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "idx_opp_players_match_id", "match_opposition_players", ["match_id"]
    )

    # match_innings
    op.create_table(
        "match_innings",
        sa.Column(
            "id", UUID(as_uuid=True), primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "match_id", UUID(as_uuid=True),
            sa.ForeignKey("matches.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("innings_number", sa.SmallInteger(), nullable=False),
        sa.Column("batting_team", sa.String(20), nullable=False),
        sa.Column("total_runs", sa.Integer(), server_default="0"),
        sa.Column("total_wickets", sa.Integer(), server_default="0"),
        sa.Column("total_overs", sa.Numeric(5, 1), server_default="0"),
        sa.Column("extras_byes", sa.Integer(), server_default="0"),
        sa.Column("extras_leg_byes", sa.Integer(), server_default="0"),
        sa.Column("extras_wides", sa.Integer(), server_default="0"),
        sa.Column("extras_no_balls", sa.Integer(), server_default="0"),
        sa.Column("extras_penalty", sa.Integer(), server_default="0"),
        sa.Column("declared", sa.Boolean(), server_default="false"),
        sa.Column("all_out", sa.Boolean(), server_default="false"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("match_id", "innings_number", name="uq_innings_match_number"),
        sa.CheckConstraint("innings_number IN (1, 2)", name="ck_innings_number"),
        sa.CheckConstraint(
            "batting_team IN ('home', 'opposition')", name="ck_innings_batting_team"
        ),
    )
    op.create_index("idx_match_innings_match_id", "match_innings", ["match_id"])

    # batting_entries
    op.create_table(
        "batting_entries",
        sa.Column(
            "id", UUID(as_uuid=True), primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "innings_id", UUID(as_uuid=True),
            sa.ForeignKey("match_innings.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "player_id", UUID(as_uuid=True),
            sa.ForeignKey("players.id", ondelete="SET NULL"), nullable=True,
        ),
        sa.Column(
            "opposition_player_id", UUID(as_uuid=True),
            sa.ForeignKey("match_opposition_players.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("batting_position", sa.Integer(), nullable=True),
        sa.Column("runs_scored", sa.Integer(), server_default="0"),
        sa.Column("balls_faced", sa.Integer(), server_default="0"),
        sa.Column("fours", sa.Integer(), server_default="0"),
        sa.Column("sixes", sa.Integer(), server_default="0"),
        sa.Column("dismissal_type", sa.String(30), nullable=True),
        sa.Column("how_out", sa.Text(), nullable=True),
        sa.Column("not_out", sa.Boolean(), server_default="false"),
        sa.Column("strike_rate", sa.Numeric(6, 2), server_default="0.00"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
        ),
    )
    op.create_index("idx_batting_entries_innings_id", "batting_entries", ["innings_id"])
    op.create_index("idx_batting_entries_player_id", "batting_entries", ["player_id"])

    # bowling_entries
    op.create_table(
        "bowling_entries",
        sa.Column(
            "id", UUID(as_uuid=True), primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "innings_id", UUID(as_uuid=True),
            sa.ForeignKey("match_innings.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "player_id", UUID(as_uuid=True),
            sa.ForeignKey("players.id", ondelete="SET NULL"), nullable=True,
        ),
        sa.Column(
            "opposition_player_id", UUID(as_uuid=True),
            sa.ForeignKey("match_opposition_players.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("bowling_position", sa.Integer(), nullable=True),
        sa.Column("overs_bowled", sa.Numeric(5, 1), server_default="0"),
        sa.Column("maidens", sa.Integer(), server_default="0"),
        sa.Column("runs_conceded", sa.Integer(), server_default="0"),
        sa.Column("wickets_taken", sa.Integer(), server_default="0"),
        sa.Column("wides", sa.Integer(), server_default="0"),
        sa.Column("no_balls", sa.Integer(), server_default="0"),
        sa.Column("economy", sa.Numeric(5, 2), server_default="0.00"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
        ),
    )
    op.create_index("idx_bowling_entries_innings_id", "bowling_entries", ["innings_id"])
    op.create_index("idx_bowling_entries_player_id", "bowling_entries", ["player_id"])

    # fall_of_wickets
    op.create_table(
        "fall_of_wickets",
        sa.Column(
            "id", UUID(as_uuid=True), primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "innings_id", UUID(as_uuid=True),
            sa.ForeignKey("match_innings.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("wicket_number", sa.Integer(), nullable=False),
        sa.Column("score_at_fall", sa.Integer(), nullable=False),
        sa.Column("overs_at_fall", sa.Numeric(5, 1), nullable=True),
        sa.Column(
            "batsman_out_player_id", UUID(as_uuid=True),
            sa.ForeignKey("players.id", ondelete="SET NULL"), nullable=True,
        ),
        sa.Column(
            "batsman_out_opposition_id", UUID(as_uuid=True),
            sa.ForeignKey("match_opposition_players.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
        ),
    )
    op.create_index("idx_fow_innings_id", "fall_of_wickets", ["innings_id"])

    # match_participation
    op.create_table(
        "match_participation",
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
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("was_substitute", sa.Boolean(), server_default="false"),
        sa.Column(
            "substitute_for_player_id", UUID(as_uuid=True),
            sa.ForeignKey("players.id", ondelete="SET NULL"), nullable=True,
        ),
        sa.Column("withdrawal_reason", sa.Text(), nullable=True),
        sa.Column("no_show_reason", sa.Text(), nullable=True),
        sa.Column(
            "confirmed_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("match_id", "player_id", name="uq_participation_match_player"),
        sa.CheckConstraint(
            "status IN ('played', 'no_show', 'withdrawn', 'substitute', 'match_abandoned')",
            name="ck_participation_status",
        ),
    )
    op.create_index(
        "idx_match_participation_match_id", "match_participation", ["match_id"]
    )
    op.create_index(
        "idx_match_participation_player_id", "match_participation", ["player_id"]
    )

    # match_audit_log
    op.create_table(
        "match_audit_log",
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
            sa.ForeignKey("players.id", ondelete="SET NULL"), nullable=True,
        ),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("previous_state", sa.String(50), nullable=True),
        sa.Column("new_state", sa.String(50), nullable=True),
        sa.Column(
            "actor_id", UUID(as_uuid=True),
            sa.ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True,
        ),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("details", JSON(), server_default=sa.text("'{}'::jsonb")),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "idx_match_audit_log_match_id", "match_audit_log", ["match_id"]
    )
    op.create_index(
        "idx_match_audit_log_created_at", "match_audit_log", ["created_at"]
    )


def downgrade() -> None:
    op.drop_index("idx_match_audit_log_created_at", table_name="match_audit_log")
    op.drop_index("idx_match_audit_log_match_id", table_name="match_audit_log")
    op.drop_table("match_audit_log")
    op.drop_index("idx_match_participation_player_id", table_name="match_participation")
    op.drop_index("idx_match_participation_match_id", table_name="match_participation")
    op.drop_table("match_participation")
    op.drop_index("idx_fow_innings_id", table_name="fall_of_wickets")
    op.drop_table("fall_of_wickets")
    op.drop_index("idx_bowling_entries_player_id", table_name="bowling_entries")
    op.drop_index("idx_bowling_entries_innings_id", table_name="bowling_entries")
    op.drop_table("bowling_entries")
    op.drop_index("idx_batting_entries_player_id", table_name="batting_entries")
    op.drop_index("idx_batting_entries_innings_id", table_name="batting_entries")
    op.drop_table("batting_entries")
    op.drop_index("idx_match_innings_match_id", table_name="match_innings")
    op.drop_table("match_innings")
    op.drop_index("idx_opp_players_match_id", table_name="match_opposition_players")
    op.drop_table("match_opposition_players")
    op.drop_column("matches", "home_batted_first")
    op.drop_column("matches", "toss_decision")
    op.drop_column("matches", "toss_won_by")
    op.drop_column("matches", "result_margin_type")
    op.drop_column("matches", "result_margin")
    op.drop_column("matches", "result")
