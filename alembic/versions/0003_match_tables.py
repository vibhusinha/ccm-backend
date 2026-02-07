"""Match tables: matches, match_availability, team_selections, fixture_types, fixture_series

Revision ID: 0003
Revises: 0002
Create Date: 2026-02-06
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # fixture_types
    op.create_table(
        "fixture_types",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("club_id", UUID(as_uuid=True), sa.ForeignKey("clubs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("color", sa.Text, server_default="'#1a7f5f'"),
        sa.Column("icon", sa.Text, server_default="'📅'"),
        sa.Column("display_order", sa.Integer, server_default="0"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("club_id", "name", name="uq_fixture_type_club_name"),
    )
    op.create_index("idx_fixture_types_club_id", "fixture_types", ["club_id"])

    # fixture_series
    op.create_table(
        "fixture_series",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("club_id", UUID(as_uuid=True), sa.ForeignKey("clubs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("fixture_type_id", UUID(as_uuid=True), sa.ForeignKey("fixture_types.id", ondelete="SET NULL")),
        sa.Column("season_id", UUID(as_uuid=True), sa.ForeignKey("seasons.id", ondelete="CASCADE")),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("recurrence_rule", sa.Text),
        sa.Column("start_date", sa.Date, nullable=False),
        sa.Column("end_date", sa.Date, nullable=False),
        sa.Column("default_time", sa.Time, server_default="'18:30'"),
        sa.Column("default_venue", sa.Text),
        sa.Column("default_is_home", sa.Boolean, server_default="true"),
        sa.Column("default_team_id", UUID(as_uuid=True), sa.ForeignKey("teams.id", ondelete="SET NULL")),
        sa.Column("default_fee_amount", sa.Numeric(10, 2), server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_fixture_series_club_id", "fixture_series", ["club_id"])
    op.create_index("idx_fixture_series_season_id", "fixture_series", ["season_id"])

    # matches
    op.create_table(
        "matches",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("club_id", UUID(as_uuid=True), sa.ForeignKey("clubs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("season_id", UUID(as_uuid=True), sa.ForeignKey("seasons.id", ondelete="SET NULL")),
        sa.Column("team_id", UUID(as_uuid=True), sa.ForeignKey("teams.id", ondelete="CASCADE")),
        sa.Column("fixture_type_id", UUID(as_uuid=True), sa.ForeignKey("fixture_types.id", ondelete="SET NULL")),
        sa.Column("series_id", UUID(as_uuid=True), sa.ForeignKey("fixture_series.id", ondelete="SET NULL")),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("time", sa.Time, nullable=False),
        sa.Column("opponent", sa.String(255), nullable=False),
        sa.Column("venue", sa.String(10), nullable=False),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), server_default="'upcoming'"),
        sa.Column("fee_amount", sa.Numeric(10, 2), server_default="0"),
        sa.Column("our_score", sa.String(50)),
        sa.Column("opponent_score", sa.String(50)),
        sa.Column("man_of_match_id", UUID(as_uuid=True), sa.ForeignKey("players.id", ondelete="SET NULL")),
        sa.Column("match_report", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("venue IN ('Home', 'Away')", name="ck_match_venue"),
        sa.CheckConstraint("type IN ('League', 'Friendly', 'T20', 'Net Session')", name="ck_match_type"),
        sa.CheckConstraint("status IN ('upcoming', 'in-progress', 'completed', 'cancelled')", name="ck_match_status"),
    )
    op.create_index("idx_matches_club_id", "matches", ["club_id"])
    op.create_index("idx_matches_date", "matches", ["date"])
    op.create_index("idx_matches_team_id", "matches", ["team_id"])

    # match_availability
    op.create_table(
        "match_availability",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("match_id", UUID(as_uuid=True), sa.ForeignKey("matches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("player_id", UUID(as_uuid=True), sa.ForeignKey("players.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("match_id", "player_id", name="uq_availability_match_player"),
        sa.CheckConstraint("status IN ('available', 'unavailable', 'pending')", name="ck_availability_status"),
    )
    op.create_index("idx_match_availability_match_id", "match_availability", ["match_id"])
    op.create_index("idx_match_availability_player_id", "match_availability", ["player_id"])

    # team_selections
    op.create_table(
        "team_selections",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("match_id", UUID(as_uuid=True), sa.ForeignKey("matches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("player_id", UUID(as_uuid=True), sa.ForeignKey("players.id", ondelete="CASCADE"), nullable=False),
        sa.Column("batting_position", sa.Integer),
        sa.Column("is_captain", sa.Boolean, server_default="false"),
        sa.Column("is_wicketkeeper", sa.Boolean, server_default="false"),
        sa.Column("confirmed", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("match_id", "player_id", name="uq_selection_match_player"),
    )


def downgrade() -> None:
    op.drop_table("team_selections")
    op.drop_table("match_availability")
    op.drop_table("matches")
    op.drop_table("fixture_series")
    op.drop_table("fixture_types")
