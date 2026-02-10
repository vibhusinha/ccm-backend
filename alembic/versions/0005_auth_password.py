"""Add password_hash to profiles and refresh_tokens table

Revision ID: 0005
Revises: 0004
Create Date: 2026-02-07
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add password_hash column to profiles (nullable for OAuth users)
    op.add_column("profiles", sa.Column("password_hash", sa.String(255), nullable=True))

    # Add unique constraint on email for login lookups
    op.create_unique_constraint("uq_profiles_email", "profiles", ["email"])

    # Add email_verified column to profiles
    op.add_column(
        "profiles",
        sa.Column("email_verified", sa.Boolean(), server_default="false", nullable=False),
    )

    # Create refresh_tokens table for token rotation
    op.create_table(
        "refresh_tokens",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("token_hash", sa.String(255), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("refresh_tokens")
    op.drop_constraint("uq_profiles_email", "profiles", type_="unique")
    op.drop_column("profiles", "email_verified")
    op.drop_column("profiles", "password_hash")
