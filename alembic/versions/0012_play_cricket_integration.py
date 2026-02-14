"""Add play_cricket_id columns for Play-Cricket integration

Revision ID: 0012
Revises: 0011
Create Date: 2026-02-13
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0012"
down_revision: Union[str, None] = "0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("clubs", sa.Column("play_cricket_id", sa.Integer(), nullable=True))
    op.create_unique_constraint("uq_clubs_play_cricket_id", "clubs", ["play_cricket_id"])

    op.add_column("teams", sa.Column("play_cricket_id", sa.Integer(), nullable=True))

    op.add_column("players", sa.Column("play_cricket_id", sa.Integer(), nullable=True))
    op.create_unique_constraint("uq_players_play_cricket_id", "players", ["play_cricket_id"])

    op.add_column("matches", sa.Column("play_cricket_id", sa.Integer(), nullable=True))
    op.create_unique_constraint("uq_matches_play_cricket_id", "matches", ["play_cricket_id"])


def downgrade() -> None:
    op.drop_constraint("uq_matches_play_cricket_id", "matches", type_="unique")
    op.drop_column("matches", "play_cricket_id")

    op.drop_constraint("uq_players_play_cricket_id", "players", type_="unique")
    op.drop_column("players", "play_cricket_id")

    op.drop_column("teams", "play_cricket_id")

    op.drop_constraint("uq_clubs_play_cricket_id", "clubs", type_="unique")
    op.drop_column("clubs", "play_cricket_id")
