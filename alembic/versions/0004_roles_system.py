"""Roles and permissions system with seed data

Revision ID: 0004
Revises: 0003
Create Date: 2026-02-06
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # roles
    op.create_table(
        "roles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(50), unique=True, nullable=False),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("hierarchy_level", sa.Integer, nullable=False, server_default="100"),
        sa.Column("is_system_role", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_roles_name", "roles", ["name"])
    op.create_index("idx_roles_hierarchy", "roles", ["hierarchy_level"])

    # role_permissions
    op.create_table(
        "role_permissions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("role_id", UUID(as_uuid=True), sa.ForeignKey("roles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("permission_key", sa.String(100), nullable=False),
        sa.Column("granted", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("role_id", "permission_key", name="uq_role_permission"),
    )
    op.create_index("idx_role_permissions_role", "role_permissions", ["role_id"])

    # Seed system roles and permissions
    op.execute("""
        INSERT INTO roles (name, display_name, description, hierarchy_level, is_system_role) VALUES
        ('clubadmin', 'Club Administrator', 'Full access to all club features and member management', 10, true),
        ('captain', 'Team Captain', 'Team selection, match management, and player communication', 20, true),
        ('vice_captain', 'Vice Captain', 'Assists captain with team selection and management', 25, true),
        ('treasurer', 'Club Treasurer', 'Manages club finances and payment tracking', 30, true),
        ('secretary', 'Club Secretary', 'Manages communications and administrative tasks', 35, true),
        ('player', 'Player', 'Club member with availability and personal stats access', 50, true),
        ('sponsor', 'Sponsor', 'View-only access to club information', 90, true);

        -- Admin permissions
        INSERT INTO role_permissions (role_id, permission_key)
        SELECT r.id, p.key FROM roles r,
        (VALUES
            ('manage_club'), ('manage_subscription'), ('manage_members'), ('assign_roles'),
            ('manage_teams'), ('manage_matches'), ('edit_matches'), ('manage_payments'),
            ('manage_merchandise'), ('manage_messages'), ('manage_tasks'),
            ('view_reports'), ('export_data'), ('view_availability'), ('set_availability'),
            ('view_stats'), ('send_messages'), ('view_messages'), ('select_team')
        ) AS p(key)
        WHERE r.name = 'clubadmin';

        -- Captain permissions
        INSERT INTO role_permissions (role_id, permission_key)
        SELECT r.id, p.key FROM roles r,
        (VALUES
            ('select_team'), ('edit_matches'), ('view_availability'), ('manage_tasks'),
            ('send_messages'), ('set_availability'), ('view_stats'), ('view_messages')
        ) AS p(key)
        WHERE r.name = 'captain';

        -- Vice Captain permissions
        INSERT INTO role_permissions (role_id, permission_key)
        SELECT r.id, p.key FROM roles r,
        (VALUES
            ('select_team'), ('edit_matches'), ('view_availability'), ('manage_tasks'),
            ('send_messages'), ('set_availability'), ('view_stats'), ('view_messages')
        ) AS p(key)
        WHERE r.name = 'vice_captain';

        -- Treasurer permissions
        INSERT INTO role_permissions (role_id, permission_key)
        SELECT r.id, p.key FROM roles r,
        (VALUES
            ('manage_payments'), ('view_reports'), ('send_messages'),
            ('set_availability'), ('view_stats'), ('view_messages')
        ) AS p(key)
        WHERE r.name = 'treasurer';

        -- Secretary permissions
        INSERT INTO role_permissions (role_id, permission_key)
        SELECT r.id, p.key FROM roles r,
        (VALUES
            ('manage_messages'), ('send_messages'), ('view_reports'),
            ('set_availability'), ('view_stats'), ('view_messages')
        ) AS p(key)
        WHERE r.name = 'secretary';

        -- Player permissions
        INSERT INTO role_permissions (role_id, permission_key)
        SELECT r.id, p.key FROM roles r,
        (VALUES ('set_availability'), ('view_stats'), ('send_messages'), ('view_messages')) AS p(key)
        WHERE r.name = 'player';

        -- Sponsor permissions
        INSERT INTO role_permissions (role_id, permission_key)
        SELECT r.id, p.key FROM roles r,
        (VALUES ('view_stats'), ('view_messages'), ('set_availability')) AS p(key)
        WHERE r.name = 'sponsor';
    """)


def downgrade() -> None:
    op.drop_table("role_permissions")
    op.drop_table("roles")
