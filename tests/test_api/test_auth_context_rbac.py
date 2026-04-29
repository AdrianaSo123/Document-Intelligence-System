import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def temp_db(tmp_path: Path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    # Tests run without applying Alembic migrations; enable explicit schema auto-create.
    monkeypatch.setenv("BDIS_DB_AUTO_CREATE", "1")
    yield db_path


def _bootstrap_membership(db_url: str, user_id: str, workspace_id: str, role: str):
    import uuid
    from datetime import date
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from bdis.infrastructure.persistence.models import Base, WorkspaceModel, UserModel, WorkspaceMembershipModel

    engine = create_engine(db_url, connect_args={"check_same_thread": False} if "sqlite" in db_url else {})
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autoflush=False, bind=engine)
    with SessionLocal() as session:
        if not session.query(WorkspaceModel).filter_by(workspace_id=workspace_id).first():
            session.add(WorkspaceModel(workspace_id=workspace_id, name="WS", status="ACTIVE", created_at=date.today()))
        if not session.query(UserModel).filter_by(user_id=user_id).first():
            session.add(UserModel(user_id=user_id, email=f"{user_id}@example.com", display_name=user_id, created_at=date.today()))
        if not session.query(WorkspaceMembershipModel).filter_by(workspace_id=workspace_id, user_id=user_id).first():
            session.add(
                WorkspaceMembershipModel(
                    id=str(uuid.uuid4()),
                    workspace_id=workspace_id,
                    user_id=user_id,
                    role=role,
                    created_at=date.today(),
                )
            )
        session.commit()


def test_headers_rejected_when_auth_mode_off(temp_db, monkeypatch):
    monkeypatch.setenv("BDIS_AUTH_MODE", "none")
    from bdis.frameworks.api.main import create_app

    client = TestClient(create_app())
    r = client.get("/documents", headers={"X-BDIS-User-Id": "u", "X-BDIS-Workspace-Id": "w"})
    assert r.status_code in (400, 401)


def _make_hs256_jwt(payload: dict, secret: str) -> str:
    import base64
    import json
    import hmac
    import hashlib

    def b64url(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")

    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = b64url(json.dumps(header).encode("utf-8"))
    payload_b64 = b64url(json.dumps(payload).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    sig = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    sig_b64 = b64url(sig)
    return f"{header_b64}.{payload_b64}.{sig_b64}"


def test_oidc_mode_accepts_bearer_token(temp_db, monkeypatch):
    monkeypatch.setenv("BDIS_AUTH_MODE", "oidc")
    monkeypatch.setenv("OIDC_JWT_ALG", "HS256")
    monkeypatch.setenv("OIDC_JWT_SECRET", "secret")

    token = _make_hs256_jwt(
        {"sub": "oidc-user", "workspace_id": "wa", "roles": ["ANALYST"]},
        secret="secret",
    )

    from bdis.frameworks.api.main import create_app

    client = TestClient(create_app())
    r = client.get("/documents", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200


def test_oidc_mode_rejects_x_bdis_headers(temp_db, monkeypatch):
    monkeypatch.setenv("BDIS_AUTH_MODE", "oidc")
    monkeypatch.setenv("OIDC_JWT_ALG", "HS256")
    monkeypatch.setenv("OIDC_JWT_SECRET", "secret")
    token = _make_hs256_jwt({"sub": "u", "workspace_id": "wa", "roles": ["ANALYST"]}, secret="secret")

    from bdis.frameworks.api.main import create_app
    client = TestClient(create_app())
    r = client.get(
        "/documents",
        headers={
            "Authorization": f"Bearer {token}",
            "X-BDIS-User-Id": "u",
            "X-BDIS-Workspace-Id": "wa",
        },
    )
    assert r.status_code == 400


def test_membership_required_in_dev_headers_mode(temp_db, monkeypatch):
    monkeypatch.setenv("BDIS_AUTH_MODE", "dev_headers")
    from bdis.frameworks.api.main import create_app

    client = TestClient(create_app())
    r = client.get("/documents", headers={"X-BDIS-User-Id": "u", "X-BDIS-Workspace-Id": "w"})
    assert r.status_code == 403


def test_auditor_cannot_enqueue_job(temp_db, monkeypatch):
    monkeypatch.setenv("BDIS_AUTH_MODE", "dev_headers")
    db_url = os.getenv("DATABASE_URL")
    _bootstrap_membership(db_url, user_id="auditor", workspace_id="w1", role="AUDITOR")

    from bdis.frameworks.api.main import create_app

    client = TestClient(create_app())
    r = client.post(
        "/jobs/create",
        files={"file": ("x.txt", b"hello", "text/plain")},
        headers={"X-BDIS-User-Id": "auditor", "X-BDIS-Workspace-Id": "w1"},
    )
    assert r.status_code == 403


def test_job_status_is_workspace_scoped(temp_db, monkeypatch):
    """
    Proves durable job lookups cannot cross workspaces.
    """
    monkeypatch.setenv("BDIS_AUTH_MODE", "dev_headers")
    db_url = os.getenv("DATABASE_URL")
    _bootstrap_membership(db_url, user_id="u1", workspace_id="wa", role="ANALYST")
    _bootstrap_membership(db_url, user_id="u2", workspace_id="wb", role="ANALYST")

    # Create a job row in workspace A directly (avoid celery/network/storage concerns).
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from datetime import datetime, timezone
    from bdis.infrastructure.persistence.models import Base, JobModel

    engine = create_engine(db_url, connect_args={"check_same_thread": False} if "sqlite" in db_url else {})
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autoflush=False, bind=engine)

    with SessionLocal() as session:
        now = datetime.now(timezone.utc)
        session.add(
            JobModel(
                job_id="job-1",
                workspace_id="wa",
                document_id="doc-1",
                trace_id="trace-1",
                status="PENDING",
                error_message=None,
                created_at=now,
                updated_at=now,
            )
        )
        session.commit()

    from bdis.frameworks.api.main import create_app

    client = TestClient(create_app())
    # Access with wrong workspace -> 404
    r = client.get("/jobs/job-1", headers={"X-BDIS-User-Id": "u2", "X-BDIS-Workspace-Id": "wb"})
    assert r.status_code == 404

    # Access with correct workspace -> 200
    r2 = client.get("/jobs/job-1", headers={"X-BDIS-User-Id": "u1", "X-BDIS-Workspace-Id": "wa"})
    assert r2.status_code == 200
    body = r2.json()
    assert body["job_id"] == "job-1"
    assert body["workspace_id"] == "wa"


def test_workspace_prefixed_job_route_rejects_mismatch(temp_db, monkeypatch):
    monkeypatch.setenv("BDIS_AUTH_MODE", "dev_headers")
    db_url = os.getenv("DATABASE_URL")
    _bootstrap_membership(db_url, user_id="u1", workspace_id="wa", role="ANALYST")

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from datetime import datetime, timezone
    from bdis.infrastructure.persistence.models import Base, JobModel

    engine = create_engine(db_url, connect_args={"check_same_thread": False} if "sqlite" in db_url else {})
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autoflush=False, bind=engine)

    with SessionLocal() as session:
        now = datetime.now(timezone.utc)
        session.add(
            JobModel(
                job_id="job-2",
                workspace_id="wa",
                document_id="doc-2",
                trace_id="trace-2",
                status="PENDING",
                error_message=None,
                created_at=now,
                updated_at=now,
            )
        )
        session.commit()

    from bdis.frameworks.api.main import create_app

    client = TestClient(create_app())
    # Mismatched route workspace should be rejected (even though ctx is valid).
    r = client.get("/workspaces/wrong/jobs/job-2", headers={"X-BDIS-User-Id": "u1", "X-BDIS-Workspace-Id": "wa"})
    assert r.status_code == 403

    # Correct route workspace should succeed.
    r2 = client.get("/workspaces/wa/jobs/job-2", headers={"X-BDIS-User-Id": "u1", "X-BDIS-Workspace-Id": "wa"})
    assert r2.status_code == 200


def test_workspace_jobs_list_scoped(temp_db, monkeypatch):
    monkeypatch.setenv("BDIS_AUTH_MODE", "dev_headers")
    db_url = os.getenv("DATABASE_URL")
    _bootstrap_membership(db_url, user_id="u1", workspace_id="wa", role="ANALYST")
    _bootstrap_membership(db_url, user_id="u2", workspace_id="wb", role="ANALYST")

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from datetime import datetime, timezone
    from bdis.infrastructure.persistence.models import Base, JobModel

    engine = create_engine(db_url, connect_args={"check_same_thread": False} if "sqlite" in db_url else {})
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autoflush=False, bind=engine)

    with SessionLocal() as session:
        now = datetime.now(timezone.utc)
        session.add(JobModel(job_id="j1", workspace_id="wa", document_id="d1", trace_id="t1", status="PENDING", error_message=None, created_at=now, updated_at=now))
        session.add(JobModel(job_id="j2", workspace_id="wb", document_id="d2", trace_id="t2", status="PENDING", error_message=None, created_at=now, updated_at=now))
        session.commit()

    from bdis.frameworks.api.main import create_app
    client = TestClient(create_app())

    r = client.get("/workspaces/wa/jobs", headers={"X-BDIS-User-Id": "u1", "X-BDIS-Workspace-Id": "wa"})
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, list)
    assert {row["job_id"] for row in body} == {"j1"}


def test_owner_can_create_workspace(temp_db, monkeypatch):
    monkeypatch.setenv("BDIS_AUTH_MODE", "dev_headers")
    db_url = os.getenv("DATABASE_URL")
    _bootstrap_membership(db_url, user_id="owner", workspace_id="wa", role="OWNER")

    from bdis.frameworks.api.main import create_app
    client = TestClient(create_app())

    r = client.post(
        "/workspaces",
        json={"name": "New Workspace"},
        headers={"X-BDIS-User-Id": "owner", "X-BDIS-Workspace-Id": "wa"},
    )
    assert r.status_code == 201
    body = r.json()
    assert "workspace_id" in body
    assert body["name"] == "New Workspace"

