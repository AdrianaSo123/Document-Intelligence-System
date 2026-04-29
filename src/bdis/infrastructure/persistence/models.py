import sqlalchemy as sa
from sqlalchemy import Column, String, Float, Date, JSON, ForeignKey, Integer, UniqueConstraint, ForeignKeyConstraint
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class WorkspaceModel(Base):
    __tablename__ = "workspaces"
    workspace_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    status = Column(String, nullable=False, default="ACTIVE")
    created_at = Column(Date)

    memberships = relationship("WorkspaceMembershipModel", back_populates="workspace")


class UserModel(Base):
    __tablename__ = "users"
    user_id = Column(String, primary_key=True)
    email = Column(String, nullable=False, index=True)
    display_name = Column(String, nullable=True)
    created_at = Column(Date)

    memberships = relationship("WorkspaceMembershipModel", back_populates="user")


class WorkspaceMembershipModel(Base):
    __tablename__ = "workspace_memberships"
    id = Column(String, primary_key=True)
    workspace_id = Column(String, ForeignKey("workspaces.workspace_id"), index=True, nullable=False)
    user_id = Column(String, ForeignKey("users.user_id"), index=True, nullable=False)
    role = Column(String, nullable=False)
    created_at = Column(Date)

    workspace = relationship("WorkspaceModel", back_populates="memberships")
    user = relationship("UserModel", back_populates="memberships")


class DocumentModel(Base):
    __tablename__ = "documents"
    __table_args__ = (
        UniqueConstraint("workspace_id", "document_id", name="uq_documents_workspace_document_id"),
    )
    id = Column(String, primary_key=True)
    document_id = Column(String, index=True, nullable=False)
    workspace_id = Column(String, index=True, nullable=False)
    s3_uri = Column(String, nullable=True)
    created_at = Column(Date)

    extractions = relationship("ExtractionModel", back_populates="document")
    evaluations = relationship("EvaluationModel", back_populates="document")


class ExtractionModel(Base):
    __tablename__ = "extractions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["workspace_id", "document_id"],
            ["documents.workspace_id", "documents.document_id"],
            name="fk_extractions_documents_workspace_document",
        ),
    )
    id = Column(String, primary_key=True)
    document_id = Column(String, nullable=False)
    workspace_id = Column(String, index=True, nullable=False)
    trace_id = Column(String)
    company_name = Column(String, nullable=True)
    amount_usd = Column(Float, nullable=False, default=0.0)
    currency = Column(String, nullable=False, default="USD")
    status = Column(String, nullable=False)
    due_date = Column(Date, nullable=True)
    confidence = Column(Float, default=0.0)
    error_message = Column(String, nullable=True)
    extracted_data_json = Column(JSON, nullable=True)
    raw_text = Column(String, nullable=True)
    created_at = Column(Date)

    document = relationship("DocumentModel", back_populates="extractions")


class EvaluationModel(Base):
    __tablename__ = "evaluations"
    __table_args__ = (
        ForeignKeyConstraint(
            ["workspace_id", "document_id"],
            ["documents.workspace_id", "documents.document_id"],
            name="fk_evaluations_documents_workspace_document",
        ),
    )
    id = Column(String, primary_key=True)
    document_id = Column(String, nullable=False)
    workspace_id = Column(String, index=True, nullable=False)
    accuracy = Column(Float)
    field_scores_json = Column(JSON)
    confidence_score = Column(Float)
    created_at = Column(Date)

    document = relationship("DocumentModel", back_populates="evaluations")


class InsightsModel(Base):
    __tablename__ = "insights"
    workspace_id = Column(String, primary_key=True)
    id = Column(String, primary_key=True)  # typically "current"
    total_revenue_usd = Column(Float, default=0.0)
    overdue_count = Column(Integer, default=0)
    high_risk_count = Column(Integer, default=0)
    document_count = Column(Integer, default=0)
    last_updated = Column(Date)


class AuditEventModel(Base):
    __tablename__ = "audit_events"
    event_id = Column(String, primary_key=True)
    workspace_id = Column(String, index=True, nullable=False)
    actor_user_id = Column(String, index=True, nullable=False)
    event_type = Column(String, index=True, nullable=False)
    resource_type = Column(String, nullable=True)
    resource_id = Column(String, nullable=True)
    trace_id = Column(String, nullable=True)
    timestamp = Column(sa.DateTime(), nullable=False)
    metadata_json = Column(JSON, nullable=True)


class JobModel(Base):
    __tablename__ = "jobs"
    job_id = Column(String, primary_key=True)
    workspace_id = Column(String, index=True, nullable=False)
    document_id = Column(String, index=True, nullable=False)
    trace_id = Column(String, nullable=False)
    status = Column(String, index=True, nullable=False)
    error_message = Column(String, nullable=True)
    created_at = Column(sa.DateTime(), nullable=False)
    updated_at = Column(sa.DateTime(), nullable=False)

