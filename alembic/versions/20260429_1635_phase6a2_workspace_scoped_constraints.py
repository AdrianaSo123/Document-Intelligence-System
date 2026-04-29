"""phase6a2 workspace-scoped constraints and composite FKs

Revision ID: 20260429_1635
Revises: 20260429_1605
Create Date: 2026-04-29

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260429_1635"
down_revision = "20260429_1605"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)

    # SQLite-safe rebuild to remove global uniqueness on documents.document_id
    # and enforce unique(workspace_id, document_id) + composite FKs.
    if not insp.has_table("documents"):
        return

    # When rebuilding tables on SQLite, pre-existing index names can survive renames.
    # Drop them defensively to avoid "index already exists" errors.
    op.execute(sa.text("DROP INDEX IF EXISTS ix_documents_workspace_id"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_documents_document_id"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_extractions_workspace_id"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_evaluations_workspace_id"))

    # 1) documents
    op.rename_table("documents", "documents_old")
    op.create_table(
        "documents",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("document_id", sa.String(), nullable=False),
        sa.Column("workspace_id", sa.String(), nullable=False),
        sa.Column("s3_uri", sa.String(), nullable=True),
        sa.Column("created_at", sa.Date(), nullable=True),
        sa.UniqueConstraint("workspace_id", "document_id", name="uq_documents_workspace_document_id"),
    )
    op.create_index("ix_documents_workspace_id", "documents", ["workspace_id"])
    op.create_index("ix_documents_document_id", "documents", ["document_id"])

    op.execute(sa.text("""
        INSERT INTO documents (id, document_id, workspace_id, s3_uri, created_at)
        SELECT id, document_id, workspace_id, s3_uri, created_at
        FROM documents_old
    """))

    # 2) extractions
    if insp.has_table("extractions"):
        op.rename_table("extractions", "extractions_old")
        op.create_table(
            "extractions",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("document_id", sa.String(), nullable=False),
            sa.Column("workspace_id", sa.String(), nullable=False),
            sa.Column("trace_id", sa.String(), nullable=True),
            sa.Column("company_name", sa.String(), nullable=True),
            sa.Column("amount_usd", sa.Float(), nullable=False, server_default="0.0"),
            sa.Column("currency", sa.String(), nullable=False, server_default="USD"),
            sa.Column("status", sa.String(), nullable=False),
            sa.Column("due_date", sa.Date(), nullable=True),
            sa.Column("confidence", sa.Float(), server_default="0.0"),
            sa.Column("error_message", sa.String(), nullable=True),
            sa.Column("extracted_data_json", sa.JSON(), nullable=True),
            sa.Column("raw_text", sa.String(), nullable=True),
            sa.Column("created_at", sa.Date(), nullable=True),
            sa.ForeignKeyConstraint(
                ["workspace_id", "document_id"],
                ["documents.workspace_id", "documents.document_id"],
                name="fk_extractions_documents_workspace_document",
            ),
        )
        op.create_index("ix_extractions_workspace_id", "extractions", ["workspace_id"])
        op.execute(sa.text("""
            INSERT INTO extractions (
              id, document_id, workspace_id, trace_id, company_name, amount_usd, currency, status, due_date,
              confidence, error_message, extracted_data_json, raw_text, created_at
            )
            SELECT
              id, document_id, workspace_id, trace_id, company_name, amount_usd, currency, status, due_date,
              confidence, error_message, extracted_data_json, raw_text, created_at
            FROM extractions_old
        """))
        op.drop_table("extractions_old")

    # 3) evaluations
    if insp.has_table("evaluations"):
        op.rename_table("evaluations", "evaluations_old")
        op.create_table(
            "evaluations",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("document_id", sa.String(), nullable=False),
            sa.Column("workspace_id", sa.String(), nullable=False),
            sa.Column("accuracy", sa.Float(), nullable=True),
            sa.Column("field_scores_json", sa.JSON(), nullable=True),
            sa.Column("confidence_score", sa.Float(), nullable=True),
            sa.Column("created_at", sa.Date(), nullable=True),
            sa.ForeignKeyConstraint(
                ["workspace_id", "document_id"],
                ["documents.workspace_id", "documents.document_id"],
                name="fk_evaluations_documents_workspace_document",
            ),
        )
        op.create_index("ix_evaluations_workspace_id", "evaluations", ["workspace_id"])
        op.execute(sa.text("""
            INSERT INTO evaluations (
              id, document_id, workspace_id, accuracy, field_scores_json, confidence_score, created_at
            )
            SELECT
              id, document_id, workspace_id, accuracy, field_scores_json, confidence_score, created_at
            FROM evaluations_old
        """))
        op.drop_table("evaluations_old")

    op.drop_table("documents_old")


def downgrade() -> None:
    # Forward-only for this portfolio phase.
    pass

