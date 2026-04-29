"""phase6c1 durable jobs table

Revision ID: 20260429_1710
Revises: 20260429_1650
Create Date: 2026-04-29

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260429_1710"
down_revision = "20260429_1650"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # SQLite: index names may persist across rebuilds; drop defensively.
    op.execute(sa.text("DROP INDEX IF EXISTS ix_jobs_workspace_id"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_jobs_document_id"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_jobs_status"))

    op.create_table(
        "jobs",
        sa.Column("job_id", sa.String(), primary_key=True),  # celery task id
        sa.Column("workspace_id", sa.String(), index=True, nullable=False),
        sa.Column("document_id", sa.String(), index=True, nullable=False),
        sa.Column("trace_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(), index=True, nullable=False),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("jobs")

