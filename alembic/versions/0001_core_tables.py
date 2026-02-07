"""Core tables: clubs, profiles, club_members, platform_admins

Revision ID: 0001
Revises:
Create Date: 2026-02-06
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # clubs
    op.create_table(
        "clubs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), unique=True, nullable=False),
        sa.Column("logo_url", sa.Text),
        sa.Column("primary_color", sa.String(7), server_default="'#1a7f5f'"),
        sa.Column("secondary_color", sa.String(7), server_default="'#f0f7f4'"),
        sa.Column("accent_color", sa.String(7), server_default="'#e6f4ef'"),
        sa.Column("logo_storage_path", sa.Text),
        sa.Column("subscription_tier", sa.String(20), server_default="'free'"),
        sa.Column("stripe_customer_id", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint(
            "subscription_tier IN ('free', 'pro', 'enterprise')",
            name="ck_club_subscription_tier",
        ),
    )

    # profiles
    op.create_table(
        "profiles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255)),
        sa.Column("avatar_url", sa.Text),
        sa.Column("phone", sa.String(50)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # club_members
    op.create_table(
        "club_members",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("club_id", UUID(as_uuid=True), sa.ForeignKey("clubs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "club_id", name="uq_club_member_user_club"),
        sa.CheckConstraint(
            "role IN ('clubadmin', 'captain', 'vice_captain', 'player', 'sponsor', 'secretary', 'treasurer')",
            name="ck_club_member_role",
        ),
    )
    op.create_index("idx_club_members_user_id", "club_members", ["user_id"])
    op.create_index("idx_club_members_club_id", "club_members", ["club_id"])

    # platform_admins
    op.create_table(
        "platform_admins",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("profiles.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("platform_admins")
    op.drop_table("club_members")
    op.drop_table("profiles")
    op.drop_table("clubs")
