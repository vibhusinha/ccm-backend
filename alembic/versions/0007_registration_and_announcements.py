"""Registration system and announcements tables

Revision ID: 0007
Revises: 0006
Create Date: 2026-02-09
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # registration_requests
    op.create_table(
        "registration_requests",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "club_id",
            UUID(as_uuid=True),
            sa.ForeignKey("clubs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column(
            "requested_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "reviewed_by",
            UUID(as_uuid=True),
            sa.ForeignKey("profiles.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "status IN ('pending', 'approved', 'rejected')",
            name="ck_registration_request_status",
        ),
    )
    op.create_index(
        "ix_registration_requests_user_id", "registration_requests", ["user_id"]
    )
    op.create_index(
        "ix_registration_requests_club_id", "registration_requests", ["club_id"]
    )

    # pending_club_registrations
    op.create_table(
        "pending_club_registrations",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "requested_by",
            UUID(as_uuid=True),
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("club_name", sa.String(255), nullable=False),
        sa.Column("club_slug", sa.String(100), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column(
            "requested_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "reviewed_by",
            UUID(as_uuid=True),
            sa.ForeignKey("profiles.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "status IN ('pending', 'approved', 'rejected')",
            name="ck_pending_club_registration_status",
        ),
    )
    op.create_index(
        "ix_pending_club_registrations_requested_by",
        "pending_club_registrations",
        ["requested_by"],
    )

    # announcements
    op.create_table(
        "announcements",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "club_id",
            UUID(as_uuid=True),
            sa.ForeignKey("clubs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("type", sa.String(30), nullable=False, server_default="general"),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column(
            "target_team_id",
            UUID(as_uuid=True),
            sa.ForeignKey("teams.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "match_id",
            UUID(as_uuid=True),
            sa.ForeignKey("matches.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_by",
            UUID(as_uuid=True),
            sa.ForeignKey("profiles.id", ondelete="SET NULL"),
            nullable=False,
        ),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "type IN ('general', 'match', 'team', 'urgent', 'event')",
            name="ck_announcement_type",
        ),
    )
    op.create_index("ix_announcements_club_id", "announcements", ["club_id"])
    op.create_index("ix_announcements_created_at", "announcements", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_announcements_created_at", table_name="announcements")
    op.drop_index("ix_announcements_club_id", table_name="announcements")
    op.drop_table("announcements")
    op.drop_index(
        "ix_pending_club_registrations_requested_by",
        table_name="pending_club_registrations",
    )
    op.drop_table("pending_club_registrations")
    op.drop_index(
        "ix_registration_requests_club_id", table_name="registration_requests"
    )
    op.drop_index(
        "ix_registration_requests_user_id", table_name="registration_requests"
    )
    op.drop_table("registration_requests")
