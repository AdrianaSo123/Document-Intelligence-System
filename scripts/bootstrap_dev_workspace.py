import os
import sys
import uuid
from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def main():
    database_url = os.getenv("DATABASE_URL", "sqlite:///bdis_prod.db")
    user_id = os.getenv("BDIS_BOOTSTRAP_USER_ID", "dev-user")
    user_email = os.getenv("BDIS_BOOTSTRAP_USER_EMAIL", "dev@example.com")
    workspace_id = os.getenv("BDIS_BOOTSTRAP_WORKSPACE_ID", "dev-workspace")
    workspace_name = os.getenv("BDIS_BOOTSTRAP_WORKSPACE_NAME", "Dev Workspace")
    role = os.getenv("BDIS_BOOTSTRAP_ROLE", "OWNER")

    repo_root = os.path.dirname(os.path.dirname(__file__))
    src = os.path.join(repo_root, "src")
    if src not in sys.path:
        sys.path.insert(0, src)

    from bdis.adapters.repositories import (  # noqa: WPS433
        Base,
        WorkspaceModel,
        UserModel,
        WorkspaceMembershipModel,
    )

    engine = create_engine(database_url, connect_args={"check_same_thread": False} if "sqlite" in database_url else {})
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autoflush=False, bind=engine)

    with SessionLocal() as session:
        ws = session.query(WorkspaceModel).filter_by(workspace_id=workspace_id).first()
        if not ws:
            ws = WorkspaceModel(workspace_id=workspace_id, name=workspace_name, status="ACTIVE", created_at=date.today())
            session.add(ws)

        user = session.query(UserModel).filter_by(user_id=user_id).first()
        if not user:
            user = UserModel(user_id=user_id, email=user_email, display_name=user_email.split("@")[0], created_at=date.today())
            session.add(user)

        membership = (
            session.query(WorkspaceMembershipModel)
            .filter_by(workspace_id=workspace_id, user_id=user_id)
            .first()
        )
        if not membership:
            membership = WorkspaceMembershipModel(
                id=str(uuid.uuid4()),
                workspace_id=workspace_id,
                user_id=user_id,
                role=role,
                created_at=date.today(),
            )
            session.add(membership)

        session.commit()

    print("✅ Bootstrapped dev workspace/membership:")
    print(f"  workspace_id={workspace_id} name={workspace_name}")
    print(f"  user_id={user_id} email={user_email}")
    print(f"  role={role}")
    print()
    print("Use these headers in dev_headers mode:")
    print(f"  X-BDIS-User-Id: {user_id}")
    print(f"  X-BDIS-Workspace-Id: {workspace_id}")


if __name__ == "__main__":
    main()

