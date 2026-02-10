"""Add platform features: club status, audit_log, platform_settings

Revision ID: 0006
Revises: 0005
Create Date: 2026-02-08
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add status/suspension columns to clubs
    op.add_column("clubs", sa.Column("status", sa.String(20), server_default="active", nullable=False))
    op.add_column("clubs", sa.Column("suspended_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("clubs", sa.Column("suspension_reason", sa.Text(), nullable=True))

    # Create audit_log table
    op.create_table(
        "audit_log",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), primary_key=True),
        sa.Column("admin_id", UUID(as_uuid=True), sa.ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("target_type", sa.String(50), nullable=False),
        sa.Column("target_id", UUID(as_uuid=True), nullable=True),
        sa.Column("details", sa.JSON(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_audit_log_admin_id", "audit_log", ["admin_id"])
    op.create_index("ix_audit_log_created_at", "audit_log", ["created_at"])

    # Create platform_settings table
    op.create_table(
        "platform_settings",
        sa.Column("key", sa.String(100), primary_key=True),
        sa.Column("value", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Seed default platform name
    op.execute(
        "INSERT INTO platform_settings (key, value) VALUES ('platform_name', 'Cricket Club Manager')"
    )


def downgrade() -> None:
    op.drop_table("platform_settings")
    op.drop_index("ix_audit_log_created_at", table_name="audit_log")
    op.drop_index("ix_audit_log_admin_id", table_name="audit_log")
    op.drop_table("audit_log")
    op.drop_column("clubs", "suspension_reason")
    op.drop_column("clubs", "suspended_at")
    op.drop_column("clubs", "status")
