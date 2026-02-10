"""Payments, notifications, and club extras tables

Revision ID: 0008
Revises: 0007
Create Date: 2026-02-09
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # fee_configs
    op.create_table(
        "fee_configs",
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
            unique=True,
        ),
        sa.Column(
            "membership_fee", sa.Numeric(10, 2), nullable=False, server_default="150.00"
        ),
        sa.Column("match_fee", sa.Numeric(10, 2), nullable=False, server_default="15.00"),
        sa.Column("nets_fee", sa.Numeric(10, 2), nullable=False, server_default="5.00"),
        sa.Column("meeting_fee", sa.Numeric(10, 2), nullable=False, server_default="10.00"),
        sa.Column("event_fee", sa.Numeric(10, 2), nullable=False, server_default="0.00"),
        sa.Column(
            "merchandise_fee", sa.Numeric(10, 2), nullable=False, server_default="0.00"
        ),
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
    )

    # payments
    op.create_table(
        "payments",
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
        sa.Column(
            "player_id",
            UUID(as_uuid=True),
            sa.ForeignKey("players.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "match_id",
            UUID(as_uuid=True),
            sa.ForeignKey("matches.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("type", sa.String(30), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("paid_date", sa.Date(), nullable=True),
        sa.Column("waived_reason", sa.Text(), nullable=True),
        sa.Column("reduced_from", sa.Numeric(10, 2), nullable=True),
        sa.Column("reduce_reason", sa.Text(), nullable=True),
        sa.Column("bank_reference", sa.String(255), nullable=True),
        sa.Column("received_date", sa.Date(), nullable=True),
        sa.Column(
            "season_id",
            UUID(as_uuid=True),
            sa.ForeignKey("seasons.id", ondelete="SET NULL"),
            nullable=True,
        ),
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
            "status IN ('pending', 'paid', 'overdue', 'waived')",
            name="ck_payment_status",
        ),
        sa.CheckConstraint(
            "type IN ('membership', 'match', 'nets', 'meeting', 'event', 'merchandise')",
            name="ck_payment_type",
        ),
    )
    op.create_index("idx_payments_club_id", "payments", ["club_id"])
    op.create_index("idx_payments_player_id", "payments", ["player_id"])
    op.create_index("idx_payments_match_id", "payments", ["match_id"])
    op.create_index("idx_payments_status", "payments", ["status"])

    # notifications
    op.create_table(
        "notifications",
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
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column(
            "data",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("idx_notifications_user_id", "notifications", ["user_id"])
    op.create_index("idx_notifications_club_id", "notifications", ["club_id"])
    op.create_index("idx_notifications_created_at", "notifications", ["created_at"])
    op.create_index(
        "idx_notifications_user_unread",
        "notifications",
        ["user_id", "is_read"],
        postgresql_where=sa.text("is_read = false"),
    )

    # push_tokens
    op.create_table(
        "push_tokens",
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
        sa.Column("token", sa.String(255), nullable=False),
        sa.Column("platform", sa.String(10), nullable=False),
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
        sa.UniqueConstraint("user_id", "token", name="uq_push_tokens_user_token"),
        sa.CheckConstraint(
            "platform IN ('ios', 'android', 'web')",
            name="ck_push_token_platform",
        ),
    )
    op.create_index("idx_push_tokens_user_id", "push_tokens", ["user_id"])

    # club_key_people
    op.create_table(
        "club_key_people",
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
        sa.Column("position", sa.String(100), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column(
            "member_id",
            UUID(as_uuid=True),
            sa.ForeignKey("club_members.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
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
    )
    op.create_index("idx_club_key_people_club_id", "club_key_people", ["club_id"])


def downgrade() -> None:
    op.drop_index("idx_club_key_people_club_id", table_name="club_key_people")
    op.drop_table("club_key_people")
    op.drop_index("idx_push_tokens_user_id", table_name="push_tokens")
    op.drop_table("push_tokens")
    op.drop_index("idx_notifications_user_unread", table_name="notifications")
    op.drop_index("idx_notifications_created_at", table_name="notifications")
    op.drop_index("idx_notifications_club_id", table_name="notifications")
    op.drop_index("idx_notifications_user_id", table_name="notifications")
    op.drop_table("notifications")
    op.drop_index("idx_payments_status", table_name="payments")
    op.drop_index("idx_payments_match_id", table_name="payments")
    op.drop_index("idx_payments_player_id", table_name="payments")
    op.drop_index("idx_payments_club_id", table_name="payments")
    op.drop_table("payments")
    op.drop_table("fee_configs")
