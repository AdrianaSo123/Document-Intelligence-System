from sqlalchemy import Column, String, Float, Date, JSON, ForeignKey, Integer
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from bdis.domain.entities import DocumentExtraction, JobStatus
from bdis.domain.value_objects import Money
from bdis.ports.document_repository import IDocumentRepository
from bdis.domain.evaluation import EvaluationResult

Base = declarative_base()

class DocumentModel(Base):
    __tablename__ = "documents"
    id = Column(String, primary_key=True)
    document_id = Column(String, unique=True, index=True)
    s3_uri = Column(String, nullable=True)
    created_at = Column(Date)
    
    extractions = relationship("ExtractionModel", back_populates="document")
    evaluations = relationship("EvaluationModel", back_populates="document")

class ExtractionModel(Base):
    __tablename__ = "extractions"
    id = Column(String, primary_key=True)
    document_id = Column(String, ForeignKey("documents.document_id"))
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
    id = Column(String, primary_key=True)
    document_id = Column(String, ForeignKey("documents.document_id"))
    accuracy = Column(Float)
    field_scores_json = Column(JSON)
    confidence_score = Column(Float)
    created_at = Column(Date)
    
    document = relationship("DocumentModel", back_populates="evaluations")

class InsightsModel(Base):
    """
    Persistent aggregate metrics as required by Section 8 of the Spec.
    """
    __tablename__ = "insights"
    id = Column(String, primary_key=True) # Usually a singleton "current"
    total_revenue_usd = Column(Float, default=0.0)
    overdue_count = Column(Integer, default=0)
    high_risk_count = Column(Integer, default=0)
    document_count = Column(Integer, default=0)
    last_updated = Column(Date)

class SQLDocumentRepository(IDocumentRepository):
    def __init__(self, session_factory):
        self.SessionLocal = session_factory

    def save(self, extraction: DocumentExtraction) -> str:
        import uuid
        from datetime import date
        
        # 1. Prepare JSON data
        extracted_data_json = extraction.extracted_data.copy()
        for k, v in extracted_data_json.items():
            if isinstance(v, (date,)):
                extracted_data_json[k] = v.isoformat()

        # 2. Map to Models
        doc_model = DocumentModel(
            id=str(uuid.uuid4()),
            document_id=extraction.document_id,
            s3_uri=extraction.s3_uri,
            created_at=extraction.created_at
        )
        
        ext_model = ExtractionModel(
            id=str(uuid.uuid4()),
            document_id=extraction.document_id,
            trace_id=extraction.trace_id,
            company_name=extraction.company_name,
            amount_usd=extraction.amount_usd,
            currency=extraction.currency,
            status=extraction.status,
            due_date=extraction.due_date,
            confidence=extraction.confidence,
            error_message=extraction.error_message,
            extracted_data_json=extracted_data_json,
            raw_text=extraction.raw_text,
            created_at=extraction.created_at
        )
        
        eval_model = None
        if extraction.evaluation:
            eval_model = EvaluationModel(
                id=str(uuid.uuid4()),
                document_id=extraction.document_id,
                accuracy=extraction.evaluation.accuracy,
                field_scores_json=extraction.evaluation.field_scores,
                confidence_score=extraction.evaluation.confidence_score,
                created_at=extraction.created_at
            )
        
        # 3. Persist in a single transaction
        with self.SessionLocal() as session:
            try:
                session.add(doc_model)
                session.add(ext_model)
                if eval_model:
                    session.add(eval_model)
                session.commit()
                
                # 4. Final Spec Compliance: Update persistent Insights table
                self._recalculate_insights(session_factory=self.SessionLocal)
            except Exception:
                session.rollback()
                raise
                
        return extraction.document_id

    def _recalculate_insights(self, session_factory):
        """
        Materialized View logic: Recalculates and persists global metrics.
        """
        from bdis.core.financials import convert_to_usd
        from datetime import date
        
        with session_factory() as session:
            all_ext = session.query(ExtractionModel).all()
            
            total_rev = 0.0
            overdue = 0
            high_risk = 0
            
            for e in all_ext:
                if e.status == JobStatus.VALIDATED:
                    total_rev += convert_to_usd(e.amount_usd, e.currency)
                
                if e.status == JobStatus.REVIEW_REQUIRED:
                    overdue += 1
                
                # Logic from entities.py duplicated here for DB efficiency
                # but in a real app we might store is_high_risk in the DB column.
                if e.amount_usd >= 10000.0: high_risk += 1
                elif not e.company_name: high_risk += 1
            
            insights = session.query(InsightsModel).filter_by(id="current").first()
            if not insights:
                insights = InsightsModel(id="current")
                session.add(insights)
                
            insights.total_revenue_usd = total_rev
            insights.overdue_count = overdue
            insights.high_risk_count = high_risk
            insights.document_count = len(all_ext)
            insights.last_updated = date.today()
            
            session.commit()
        
    def get_all(self) -> list[DocumentExtraction]:
        """
        Retrieves normalized records and reconstructs the DocumentExtraction Domain Entity.
        """
        with self.SessionLocal() as session:
            # Query joined data
            records = session.query(ExtractionModel).join(DocumentModel).all()
            
            results = []
            for r in records:
                # Find matching evaluation if any
                evaluation_record = session.query(EvaluationModel).filter_by(document_id=r.document_id).first()
                evaluation_result = None
                if evaluation_record:
                    evaluation_result = EvaluationResult(
                        document_id=r.document_id,
                        accuracy=evaluation_record.accuracy,
                        field_scores=evaluation_record.field_scores_json,
                        confidence_score=evaluation_record.confidence_score
                    )

                results.append(DocumentExtraction(
                    document_id=r.document_id,
                    status=r.status,
                    raw_text=r.raw_text or "",
                    extracted_data=r.extracted_data_json or {},
                    money=Money(r.amount_usd, r.currency or "USD"),
                    company_name=r.company_name,
                    due_date=r.due_date,
                    s3_uri=r.document.s3_uri if r.document else None,
                    confidence=r.confidence,
                    evaluation=evaluation_result,
                    error_message=r.error_message,
                    trace_id=r.trace_id,
                    created_at=r.created_at
                ))
            return results
            
    def get_all_raw(self) -> list[dict]:
        """
        Optimized 'Read Model' for UI Dashboard.
        """
        with self.SessionLocal() as session:
            records = session.query(ExtractionModel).join(DocumentModel).all()
            return [
                {
                    "document_id": r.document_id,
                    "trace_id": r.trace_id,
                    "company_name": r.company_name,
                    "amount_usd": r.amount_usd,
                    "currency": r.currency or "USD",
                    "status": r.status,
                    "due_date": r.due_date,
                    "confidence": r.confidence,
                    "s3_uri": r.document.s3_uri if r.document else None,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                    "is_high_risk": r.amount_usd >= 10000.0 or not r.company_name,
                    "raw_text": r.raw_text
                } for r in records
            ]
