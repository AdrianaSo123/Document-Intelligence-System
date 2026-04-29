import os
import uuid
from datetime import datetime, timezone
from fastapi import Header, HTTPException
from bdis.core.config import settings
from bdis.adapters.repositories import SQLDocumentRepository
from bdis.adapters.s3_storage import S3StorageAdapter
from bdis.frameworks.openai_extractor import OpenAIExtractor
from bdis.usecases.fetch_documents import FetchDocumentsUseCase
from bdis.usecases.processing_pipeline import ProcessingPipeline
from bdis.domain.normalization import DocumentNormalizer
from bdis.adapters.evaluator_adapter import ExactMatchEvaluator
from bdis.adapters.sanitizer_adapter import RegexPIISanitizer
from bdis.core.resilience import resilience_wrapper

from bdis.infrastructure.database import init_database
from bdis.core.tenancy import DEFAULT_WORKSPACE_ID
from bdis.core.auth import RequestContext, ROLE_AUDITOR, ROLE_ANALYST, ROLE_OWNER

# Cache the session factory to avoid re-initializing on every call
_session_factory = None
_session_factory_db_url = None

def get_repository():
    global _session_factory, _session_factory_db_url
    db_url = os.getenv("DATABASE_URL", settings.DATABASE_URL)
    if _session_factory is None or _session_factory_db_url != db_url:
        _, _session_factory = init_database(db_url)
        _session_factory_db_url = db_url
    return SQLDocumentRepository(_session_factory)

def get_storage():
    return S3StorageAdapter()

def get_extractor():
    extractor = OpenAIExtractor(settings.OPENAI_API_KEY)
    # Apply shared resilience policy for the "openai_service"
    extractor.extract_schema = resilience_wrapper("openai_service")(extractor.extract_schema)
    return extractor

def get_processing_pipeline():
    """
    Composition Root: Wires up the ProcessingPipeline with its required Adapters.
    """
    return ProcessingPipeline(
        extractor=get_extractor(),
        normalizer=DocumentNormalizer(),
        repository=get_repository(),
        evaluator=ExactMatchEvaluator(),
        sanitizer=RegexPIISanitizer(),
        storage=get_storage()
    )

def get_fetch_documents_usecase():
    return FetchDocumentsUseCase(get_repository())


def get_default_workspace_id() -> str:
    """
    Temporary wiring for Phase 6A2: until auth context (Sprint 6B) exists,
    we operate against the migrated Default Workspace.
    """
    return DEFAULT_WORKSPACE_ID


def get_request_context(
    x_bdis_user_id: str | None = Header(default=None, alias="X-BDIS-User-Id"),
    x_bdis_workspace_id: str | None = Header(default=None, alias="X-BDIS-Workspace-Id"),
    x_bdis_role: str | None = Header(default=None, alias="X-BDIS-Role"),
    x_bdis_trace_id: str | None = Header(default=None, alias="X-BDIS-Trace-Id"),
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> RequestContext:
    """
    Phase 6B: RequestContext resolver.

    - In dev_headers mode: requires X-BDIS-User-Id and X-BDIS-Workspace-Id.
      Role is derived from the DB membership; X-BDIS-Role is optional but must match if provided.
    - In non-dev mode: reject identity headers to prevent privilege injection.
    """
    auth_mode = os.getenv("BDIS_AUTH_MODE", settings.BDIS_AUTH_MODE)

    if auth_mode == "oidc":
        # In OIDC mode, dev identity headers are forbidden.
        if any([x_bdis_user_id, x_bdis_workspace_id, x_bdis_role, x_bdis_trace_id]):
            raise HTTPException(status_code=400, detail="X-BDIS identity headers are not allowed in OIDC auth mode.")
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing Bearer token.")

        token = authorization.replace("Bearer ", "", 1).strip()
        from bdis.core.oidc import verify_jwt, JwksCache  # noqa: WPS433

        alg = os.getenv("OIDC_JWT_ALG", settings.OIDC_JWT_ALG)
        secret = os.getenv("OIDC_JWT_SECRET", settings.OIDC_JWT_SECRET)
        jwks_url = os.getenv("OIDC_JWKS_URL", settings.OIDC_JWKS_URL)
        issuer = os.getenv("OIDC_ISSUER", settings.OIDC_ISSUER)
        audience = os.getenv("OIDC_AUDIENCE", settings.OIDC_AUDIENCE)

        jwks_cache = JwksCache(jwks_url) if jwks_url else None
        claims = verify_jwt(token, alg=alg, secret=secret, jwks_cache=jwks_cache, issuer=issuer, audience=audience)

        user_id = claims.get("sub")
        workspace_id = claims.get("workspace_id")
        roles = claims.get("roles") or claims.get("role")
        role = None
        if isinstance(roles, list) and roles:
            role = roles[0]
        elif isinstance(roles, str):
            role = roles

        if not user_id or not workspace_id or not role:
            raise HTTPException(status_code=401, detail="Missing required OIDC claims.")

        trace_id = x_bdis_trace_id or str(uuid.uuid4())
        return RequestContext(workspace_id=workspace_id, user_id=user_id, role=role, trace_id=trace_id)

    if auth_mode != "dev_headers":
        if any([x_bdis_user_id, x_bdis_workspace_id, x_bdis_role, x_bdis_trace_id, authorization]):
            raise HTTPException(status_code=400, detail="Identity headers are not allowed in this auth mode.")
        raise HTTPException(status_code=401, detail="Authentication required.")

    if not x_bdis_user_id or not x_bdis_workspace_id:
        raise HTTPException(status_code=401, detail="Missing required identity headers.")

    trace_id = x_bdis_trace_id or str(uuid.uuid4())

    # Membership enforcement (source of truth)
    repo = get_repository()
    # Direct DB query via ORM models for now (still within the Framework boundary).
    from bdis.infrastructure.persistence.models import WorkspaceMembershipModel  # noqa: WPS433

    with repo.SessionLocal() as session:  # type: ignore[attr-defined]
        membership = (
            session.query(WorkspaceMembershipModel)
            .filter_by(workspace_id=x_bdis_workspace_id, user_id=x_bdis_user_id)
            .first()
        )
        if not membership:
            raise HTTPException(status_code=403, detail="User is not a member of this workspace.")

        role = membership.role
        if x_bdis_role and x_bdis_role != role:
            raise HTTPException(status_code=403, detail="Role header does not match workspace membership.")

    return RequestContext(
        workspace_id=x_bdis_workspace_id,
        user_id=x_bdis_user_id,
        role=role,
        trace_id=trace_id,
    )


def audit_event(
    ctx: RequestContext,
    event_type: str,
    resource_type: str | None = None,
    resource_id: str | None = None,
    metadata: dict | None = None,
) -> None:
    """
    Minimal audit writer (Phase 6B).
    Metadata must be non-PII.
    """
    import uuid as _uuid
    from bdis.infrastructure.persistence.models import AuditEventModel  # noqa: WPS433

    repo = get_repository()
    with repo.SessionLocal() as session:  # type: ignore[attr-defined]
        session.add(
            AuditEventModel(
                event_id=str(_uuid.uuid4()),
                workspace_id=ctx.workspace_id,
                actor_user_id=ctx.user_id,
                event_type=event_type,
                resource_type=resource_type,
                resource_id=resource_id,
                trace_id=ctx.trace_id,
                timestamp=datetime.now(timezone.utc),
                metadata_json=metadata or {},
            )
        )
        session.commit()


def jobs_create(ctx: RequestContext, job_id: str, document_id: str, trace_id: str) -> None:
    from bdis.infrastructure.persistence.models import JobModel  # noqa: WPS433

    repo = get_repository()
    now = datetime.now(timezone.utc)
    with repo.SessionLocal() as session:  # type: ignore[attr-defined]
        session.add(
            JobModel(
                job_id=job_id,
                workspace_id=ctx.workspace_id,
                document_id=document_id,
                trace_id=trace_id,
                status="PENDING",
                error_message=None,
                created_at=now,
                updated_at=now,
            )
        )
        session.commit()


def jobs_update_status(ctx: RequestContext, job_id: str, status: str, error_message: str | None = None) -> None:
    from bdis.infrastructure.persistence.models import JobModel  # noqa: WPS433

    repo = get_repository()
    now = datetime.now(timezone.utc)
    with repo.SessionLocal() as session:  # type: ignore[attr-defined]
        job = session.query(JobModel).filter_by(job_id=job_id, workspace_id=ctx.workspace_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found.")
        job.status = status
        job.updated_at = now
        if error_message:
            job.error_message = error_message
        session.commit()


def jobs_get(ctx: RequestContext, job_id: str) -> dict:
    from bdis.infrastructure.persistence.models import JobModel  # noqa: WPS433

    repo = get_repository()
    with repo.SessionLocal() as session:  # type: ignore[attr-defined]
        job = session.query(JobModel).filter_by(job_id=job_id, workspace_id=ctx.workspace_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found.")
        return {
            "job_id": job.job_id,
            "workspace_id": job.workspace_id,
            "document_id": job.document_id,
            "trace_id": job.trace_id,
            "status": job.status,
            "error_message": job.error_message,
            "created_at": job.created_at.isoformat(),
            "updated_at": job.updated_at.isoformat(),
        }


def jobs_list(ctx: RequestContext, limit: int = 50) -> list[dict]:
    from bdis.infrastructure.persistence.models import JobModel  # noqa: WPS433

    repo = get_repository()
    with repo.SessionLocal() as session:  # type: ignore[attr-defined]
        rows = (
            session.query(JobModel)
            .filter_by(workspace_id=ctx.workspace_id)
            .order_by(JobModel.updated_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "job_id": j.job_id,
                "workspace_id": j.workspace_id,
                "document_id": j.document_id,
                "trace_id": j.trace_id,
                "status": j.status,
                "error_message": j.error_message,
                "created_at": j.created_at.isoformat(),
                "updated_at": j.updated_at.isoformat(),
            }
            for j in rows
        ]
