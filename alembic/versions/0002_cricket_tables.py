"""Cricket tables: seasons, teams, players

Revision ID: 0002
Revises: 0001
Create Date: 2026-02-06
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # seasons
    op.create_table(
        "seasons",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("club_id", UUID(as_uuid=True), sa.ForeignKey("clubs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("start_date", sa.Date, nullable=False),
        sa.Column("end_date", sa.Date, nullable=False),
        sa.Column("status", sa.String(20), server_default="'draft'"),
        sa.Column("is_current", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('draft', 'active', 'completed')", name="ck_season_status"),
    )
    op.create_index("idx_seasons_club_id", "seasons", ["club_id"])

    # teams (captain_id/vice_captain_id added later after players exists)
    op.create_table(
        "teams",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("club_id", UUID(as_uuid=True), sa.ForeignKey("clubs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("division", sa.String(100)),
        sa.Column("division_number", sa.Integer),
        sa.Column("division_group", sa.String(1)),
        sa.Column("season_id", UUID(as_uuid=True), sa.ForeignKey("seasons.id", ondelete="SET NULL")),
        sa.Column("display_order", sa.Integer, server_default="0"),
        sa.Column("description", sa.Text),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint(
            "division_number IS NULL OR (division_number >= 1 AND division_number <= 10)",
            name="ck_team_division_number",
        ),
        sa.CheckConstraint(
            "division_group IS NULL OR division_group IN ('A', 'B', 'C', 'D')",
            name="ck_team_division_group",
        ),
    )
    op.create_index("idx_teams_club_id", "teams", ["club_id"])
    op.create_index("idx_teams_season_id", "teams", ["season_id"])

    # players
    op.create_table(
        "players",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("club_id", UUID(as_uuid=True), sa.ForeignKey("clubs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("profiles.id", ondelete="SET NULL")),
        sa.Column("club_member_id", UUID(as_uuid=True), sa.ForeignKey("club_members.id", ondelete="SET NULL")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255)),
        sa.Column("phone", sa.String(50)),
        sa.Column("address", sa.Text),
        sa.Column("date_of_birth", sa.Date),
        sa.Column("role", sa.String(30), nullable=False),
        sa.Column("team_id", UUID(as_uuid=True), sa.ForeignKey("teams.id", ondelete="SET NULL")),
        sa.Column("is_core", sa.Boolean, server_default="false"),
        sa.Column("member_since", sa.Date, server_default=sa.text("CURRENT_DATE")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint(
            "role IN ('Batter', 'Bowler', 'All-rounder', 'Wicket-keeper')",
            name="ck_player_role",
        ),
    )
    op.create_index("idx_players_club_id", "players", ["club_id"])
    op.create_index("idx_players_team_id", "players", ["team_id"])

    # Now add captain_id and vice_captain_id to teams
    op.add_column("teams", sa.Column("captain_id", UUID(as_uuid=True)))
    op.add_column("teams", sa.Column("vice_captain_id", UUID(as_uuid=True)))
    op.create_foreign_key(
        "fk_team_captain", "teams", "players", ["captain_id"], ["id"], ondelete="SET NULL"
    )
    op.create_foreign_key(
        "fk_team_vice_captain", "teams", "players", ["vice_captain_id"], ["id"], ondelete="SET NULL"
    )


def downgrade() -> None:
    op.drop_constraint("fk_team_vice_captain", "teams", type_="foreignkey")
    op.drop_constraint("fk_team_captain", "teams", type_="foreignkey")
    op.drop_column("teams", "vice_captain_id")
    op.drop_column("teams", "captain_id")
    op.drop_table("players")
    op.drop_table("teams")
    op.drop_table("seasons")
