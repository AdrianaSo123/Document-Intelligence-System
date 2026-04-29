"""phase6b audit events table

Revision ID: 20260429_1650
Revises: 20260429_1635
Create Date: 2026-04-29

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260429_1650"
down_revision = "20260429_1635"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # SQLite: index names may persist across table rebuilds/renames in other migrations/tests.
    op.execute(sa.text("DROP INDEX IF EXISTS ix_audit_events_workspace_id"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_audit_events_actor_user_id"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_audit_events_event_type"))

    op.create_table(
        "audit_events",
        sa.Column("event_id", sa.String(), primary_key=True),
        sa.Column("workspace_id", sa.String(), index=True, nullable=False),
        sa.Column("actor_user_id", sa.String(), index=True, nullable=False),
        sa.Column("event_type", sa.String(), index=True, nullable=False),
        sa.Column("resource_type", sa.String(), nullable=True),
        sa.Column("resource_id", sa.String(), nullable=True),
        sa.Column("trace_id", sa.String(), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("audit_events")

