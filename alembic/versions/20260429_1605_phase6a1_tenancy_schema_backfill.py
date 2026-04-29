"""phase6a1 tenancy schema + default workspace backfill

Revision ID: 20260429_1605
Revises:
Create Date: 2026-04-29

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260429_1605"
down_revision = None
branch_labels = None
depends_on = None


DEFAULT_WORKSPACE_ID = "00000000-0000-0000-0000-000000000001"
DEFAULT_WORKSPACE_NAME = "Default Workspace"


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)

    # 1) Core tenancy tables
    op.create_table(
        "workspaces",
        sa.Column("workspace_id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.Date(), nullable=True),
    )

    op.create_table(
        "users",
        sa.Column("user_id", sa.String(), primary_key=True),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("display_name", sa.String(), nullable=True),
        sa.Column("created_at", sa.Date(), nullable=True),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "workspace_memberships",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("workspace_id", sa.String(), sa.ForeignKey("workspaces.workspace_id"), nullable=False),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("created_at", sa.Date(), nullable=True),
    )
    op.create_index("ix_workspace_memberships_workspace_id", "workspace_memberships", ["workspace_id"])
    op.create_index("ix_workspace_memberships_user_id", "workspace_memberships", ["user_id"])

    # 2) Create deterministic default workspace
    op.execute(
        sa.text(
            """
            INSERT INTO workspaces (workspace_id, name, status)
            VALUES (:workspace_id, :name, 'ACTIVE')
            """
        ).bindparams(workspace_id=DEFAULT_WORKSPACE_ID, name=DEFAULT_WORKSPACE_NAME)
    )

    # 3) Add workspace_id columns to existing tables (if they exist)
    if insp.has_table("documents"):
        op.add_column("documents", sa.Column("workspace_id", sa.String(), nullable=True))
        op.create_index("ix_documents_workspace_id", "documents", ["workspace_id"])
        op.execute(sa.text("UPDATE documents SET workspace_id = :wid WHERE workspace_id IS NULL").bindparams(wid=DEFAULT_WORKSPACE_ID))

    if insp.has_table("extractions"):
        op.add_column("extractions", sa.Column("workspace_id", sa.String(), nullable=True))
        op.create_index("ix_extractions_workspace_id", "extractions", ["workspace_id"])
        op.execute(sa.text("UPDATE extractions SET workspace_id = :wid WHERE workspace_id IS NULL").bindparams(wid=DEFAULT_WORKSPACE_ID))

    if insp.has_table("evaluations"):
        op.add_column("evaluations", sa.Column("workspace_id", sa.String(), nullable=True))
        op.create_index("ix_evaluations_workspace_id", "evaluations", ["workspace_id"])
        op.execute(sa.text("UPDATE evaluations SET workspace_id = :wid WHERE workspace_id IS NULL").bindparams(wid=DEFAULT_WORKSPACE_ID))

    # 4) Convert insights from global singleton to per-workspace.
    # SQLite cannot drop/alter PK constraints easily, so we rebuild the table safely.
    if insp.has_table("insights"):
        cols = {c["name"] for c in insp.get_columns("insights")}
        has_new_shape = "workspace_id" in cols

        if not has_new_shape:
            op.rename_table("insights", "insights_old")

            op.create_table(
                "insights",
                sa.Column("workspace_id", sa.String(), primary_key=True),
                sa.Column("id", sa.String(), primary_key=True),
                sa.Column("total_revenue_usd", sa.Float(), server_default="0.0"),
                sa.Column("overdue_count", sa.Integer(), server_default="0"),
                sa.Column("high_risk_count", sa.Integer(), server_default="0"),
                sa.Column("document_count", sa.Integer(), server_default="0"),
                sa.Column("last_updated", sa.Date(), nullable=True),
            )

            # Best-effort migrate prior singleton row(s) into the default workspace.
            # Old schema: (id PK) with typically id="current"
            op.execute(
                sa.text(
                    """
                    INSERT INTO insights (workspace_id, id, total_revenue_usd, overdue_count, high_risk_count, document_count, last_updated)
                    SELECT :wid, id, total_revenue_usd, overdue_count, high_risk_count, document_count, last_updated
                    FROM insights_old
                    """
                ).bindparams(wid=DEFAULT_WORKSPACE_ID)
            )

            op.drop_table("insights_old")
    else:
        # Fresh installs may not have insights yet; create in the new shape.
        op.create_table(
            "insights",
            sa.Column("workspace_id", sa.String(), primary_key=True),
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("total_revenue_usd", sa.Float(), server_default="0.0"),
            sa.Column("overdue_count", sa.Integer(), server_default="0"),
            sa.Column("high_risk_count", sa.Integer(), server_default="0"),
            sa.Column("document_count", sa.Integer(), server_default="0"),
            sa.Column("last_updated", sa.Date(), nullable=True),
        )


def downgrade() -> None:
    # Downgrade is intentionally limited; this phase introduces fundamental schema changes.
    # For portfolio use, forward-only migrations are acceptable; enterprise teams would implement full downgrade.
    op.drop_table("workspace_memberships")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    op.drop_table("workspaces")

