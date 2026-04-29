import os
import sys
from pathlib import Path

import sqlalchemy as sa


def _ensure_src_on_path():
    repo_root = Path(__file__).resolve().parents[2]
    src = repo_root / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))


def test_alembic_upgrade_backfills_default_workspace(tmp_path: Path):
    """
    Simulates an existing pre-Phase-6 database, then upgrades to head and asserts:
    - Default Workspace is created
    - tenant-bearing rows get workspace_id backfilled
    - insights table is rebuilt into per-workspace shape
    """
    _ensure_src_on_path()

    db_path = tmp_path / "legacy.db"
    engine = sa.create_engine(f"sqlite:///{db_path}")

    # Create legacy schema (pre-Phase-6A1)
    with engine.begin() as conn:
        conn.execute(sa.text("""
            CREATE TABLE documents (
                id VARCHAR PRIMARY KEY,
                document_id VARCHAR UNIQUE,
                s3_uri VARCHAR,
                created_at DATE
            );
        """))
        conn.execute(sa.text("""
            CREATE TABLE extractions (
                id VARCHAR PRIMARY KEY,
                document_id VARCHAR,
                trace_id VARCHAR,
                company_name VARCHAR,
                amount_usd FLOAT DEFAULT 0.0 NOT NULL,
                currency VARCHAR DEFAULT 'USD' NOT NULL,
                status VARCHAR NOT NULL,
                due_date DATE,
                confidence FLOAT DEFAULT 0.0,
                error_message VARCHAR,
                extracted_data_json JSON,
                raw_text VARCHAR,
                created_at DATE
            );
        """))
        conn.execute(sa.text("""
            CREATE TABLE evaluations (
                id VARCHAR PRIMARY KEY,
                document_id VARCHAR,
                accuracy FLOAT,
                field_scores_json JSON,
                confidence_score FLOAT,
                created_at DATE
            );
        """))
        conn.execute(sa.text("""
            CREATE TABLE insights (
                id VARCHAR PRIMARY KEY,
                total_revenue_usd FLOAT DEFAULT 0.0,
                overdue_count INTEGER DEFAULT 0,
                high_risk_count INTEGER DEFAULT 0,
                document_count INTEGER DEFAULT 0,
                last_updated DATE
            );
        """))

        # Insert one legacy row in each table
        conn.execute(sa.text("INSERT INTO documents (id, document_id, s3_uri) VALUES ('d1', 'doc_1', NULL)"))
        conn.execute(sa.text("INSERT INTO extractions (id, document_id, trace_id, status) VALUES ('e1', 'doc_1', 't1', 'VALIDATED')"))
        conn.execute(sa.text("INSERT INTO evaluations (id, document_id, accuracy) VALUES ('v1', 'doc_1', 1.0)"))
        conn.execute(sa.text("INSERT INTO insights (id, total_revenue_usd, document_count) VALUES ('current', 123.0, 1)"))

    # Run alembic upgrade head
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

    from alembic import command  # noqa: WPS433
    from alembic.config import Config  # noqa: WPS433

    repo_root = Path(__file__).resolve().parents[2]
    cfg = Config(str(repo_root / "alembic.ini"))
    command.upgrade(cfg, "head")

    # Assert backfill
    with engine.connect() as conn:
        default_ws = conn.execute(
            sa.text("SELECT workspace_id, name FROM workspaces WHERE workspace_id = :wid"),
            {"wid": "00000000-0000-0000-0000-000000000001"},
        ).fetchone()
        assert default_ws is not None
        assert default_ws.name == "Default Workspace"

        docs = conn.execute(sa.text("SELECT workspace_id FROM documents WHERE document_id='doc_1'")).fetchone()
        assert docs is not None
        assert docs.workspace_id == "00000000-0000-0000-0000-000000000001"

        ext = conn.execute(sa.text("SELECT workspace_id FROM extractions WHERE id='e1'")).fetchone()
        assert ext is not None
        assert ext.workspace_id == "00000000-0000-0000-0000-000000000001"

        ev = conn.execute(sa.text("SELECT workspace_id FROM evaluations WHERE id='v1'")).fetchone()
        assert ev is not None
        assert ev.workspace_id == "00000000-0000-0000-0000-000000000001"

        # New insights shape: (workspace_id, id) composite key
        ins = conn.execute(
            sa.text("SELECT workspace_id, id, total_revenue_usd, document_count FROM insights WHERE id='current'")
        ).fetchone()
        assert ins is not None
        assert ins.workspace_id == "00000000-0000-0000-0000-000000000001"
        assert ins.total_revenue_usd == 123.0
        assert ins.document_count == 1

