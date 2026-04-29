import uuid
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from bdis.core.auth import RequestContext, role_allows_admin
from bdis.frameworks.api.dependencies import get_request_context, get_repository, audit_event
from bdis.infrastructure.persistence.models import WorkspaceMembershipModel, WorkspaceModel, UserModel


router = APIRouter(prefix="/workspaces", tags=["workspaces"])


class AddMemberRequest(BaseModel):
    user_id: str
    email: str | None = None
    role: str = "ANALYST"


class CreateWorkspaceRequest(BaseModel):
    name: str


@router.get("/me")
async def list_my_workspaces(ctx: RequestContext = Depends(get_request_context)):
    repo = get_repository()
    with repo.SessionLocal() as session:  # type: ignore[attr-defined]
        memberships = session.query(WorkspaceMembershipModel).filter_by(user_id=ctx.user_id).all()
        results = []
        for m in memberships:
            ws = session.query(WorkspaceModel).filter_by(workspace_id=m.workspace_id).first()
            results.append(
                {
                    "workspace_id": m.workspace_id,
                    "role": m.role,
                    "name": ws.name if ws else None,
                    "status": ws.status if ws else None,
                }
            )
        return results


@router.post("", status_code=201)
async def create_workspace(body: CreateWorkspaceRequest, ctx: RequestContext = Depends(get_request_context)):
    """
    Creates a new workspace and adds the caller as OWNER.

    Enterprise rule: only an OWNER can create additional workspaces.
    (In dev, initial workspace creation is handled by the bootstrap script.)
    """
    if not role_allows_admin(ctx.role):
        raise HTTPException(status_code=403, detail="Role is not permitted to create workspaces.")

    new_workspace_id = str(uuid.uuid4())

    repo = get_repository()
    with repo.SessionLocal() as session:  # type: ignore[attr-defined]
        session.add(WorkspaceModel(workspace_id=new_workspace_id, name=body.name, status="ACTIVE", created_at=date.today()))
        session.add(
            WorkspaceMembershipModel(
                id=str(uuid.uuid4()),
                workspace_id=new_workspace_id,
                user_id=ctx.user_id,
                role="OWNER",
                created_at=date.today(),
            )
        )
        session.commit()

    audit_event(ctx, event_type="workspace.created", resource_type="workspace", resource_id=new_workspace_id, metadata={"name": body.name})
    return {"workspace_id": new_workspace_id, "name": body.name}


@router.get("/{workspace_id}/members")
async def list_members(workspace_id: str, ctx: RequestContext = Depends(get_request_context)):
    if workspace_id != ctx.workspace_id:
        raise HTTPException(status_code=403, detail="Route workspace_id does not match authenticated workspace.")
    if not role_allows_admin(ctx.role):
        raise HTTPException(status_code=403, detail="Role is not permitted to view membership list.")

    repo = get_repository()
    with repo.SessionLocal() as session:  # type: ignore[attr-defined]
        members = session.query(WorkspaceMembershipModel).filter_by(workspace_id=workspace_id).all()
        return [{"user_id": m.user_id, "role": m.role} for m in members]


@router.post("/{workspace_id}/members", status_code=201)
async def add_member(workspace_id: str, body: AddMemberRequest, ctx: RequestContext = Depends(get_request_context)):
    if workspace_id != ctx.workspace_id:
        raise HTTPException(status_code=403, detail="Route workspace_id does not match authenticated workspace.")
    if not role_allows_admin(ctx.role):
        raise HTTPException(status_code=403, detail="Role is not permitted to add members.")

    repo = get_repository()
    with repo.SessionLocal() as session:  # type: ignore[attr-defined]
        # Ensure workspace exists
        ws = session.query(WorkspaceModel).filter_by(workspace_id=workspace_id).first()
        if not ws:
            raise HTTPException(status_code=404, detail="Workspace not found.")

        # Ensure user exists (create minimal user record if provided)
        user = session.query(UserModel).filter_by(user_id=body.user_id).first()
        if not user:
            session.add(
                UserModel(
                    user_id=body.user_id,
                    email=body.email or f"{body.user_id}@example.com",
                    display_name=(body.email or body.user_id).split("@")[0],
                    created_at=date.today(),
                )
            )

        existing = (
            session.query(WorkspaceMembershipModel)
            .filter_by(workspace_id=workspace_id, user_id=body.user_id)
            .first()
        )
        if existing:
            existing.role = body.role
        else:
            session.add(
                WorkspaceMembershipModel(
                    id=str(uuid.uuid4()),
                    workspace_id=workspace_id,
                    user_id=body.user_id,
                    role=body.role,
                    created_at=date.today(),
                )
            )
        session.commit()

    audit_event(ctx, event_type="membership.added", resource_type="workspace", resource_id=workspace_id, metadata={"user_id": body.user_id, "role": body.role})
    return {"ok": True}

