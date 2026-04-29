from __future__ import annotations

import sqlalchemy as sa
from bdis.domain.entities import DocumentExtraction, JobStatus
from bdis.domain.value_objects import Money
from bdis.ports.document_repository import IDocumentRepository
from bdis.domain.evaluation import EvaluationResult
from bdis.infrastructure.persistence.models import (
    DocumentModel,
    ExtractionModel,
    EvaluationModel,
    InsightsModel,
)

class SQLDocumentRepository(IDocumentRepository):
    def __init__(self, session_factory):
        self.SessionLocal = session_factory

    def save(self, workspace_id: str, extraction: DocumentExtraction) -> str:
        import uuid
        from datetime import date
        
        # 1. Prepare JSON data
        extracted_data_json = extraction.extracted_data.copy()
        for k, v in extracted_data_json.items():
            if isinstance(v, (date,)):
                extracted_data_json[k] = v.isoformat()

        # 2. Map to Models
        # Enterprise requirement: deterministic behavior under retries.
        # With unique(workspace_id, document_id), we must not blindly insert a new DocumentModel each time.
        
        ext_model = ExtractionModel(
            id=str(uuid.uuid4()),
            document_id=extraction.document_id,
            workspace_id=workspace_id,
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
                workspace_id=workspace_id,
                accuracy=extraction.evaluation.accuracy,
                field_scores_json=extraction.evaluation.field_scores,
                confidence_score=extraction.evaluation.confidence_score,
                created_at=extraction.created_at
            )
        
        # 3. Persist in a single transaction
        with self.SessionLocal() as session:
            try:
                existing_doc = (
                    session.query(DocumentModel)
                    .filter_by(workspace_id=workspace_id, document_id=extraction.document_id)
                    .first()
                )
                if existing_doc:
                    # Keep the latest URI around if present.
                    if extraction.s3_uri:
                        existing_doc.s3_uri = extraction.s3_uri
                else:
                    session.add(
                        DocumentModel(
                            id=str(uuid.uuid4()),
                            document_id=extraction.document_id,
                            workspace_id=workspace_id,
                            s3_uri=extraction.s3_uri,
                            created_at=extraction.created_at,
                        )
                    )

                session.add(ext_model)
                if eval_model:
                    session.add(eval_model)
                session.commit()
                
                # 4. Final Spec Compliance: Update persistent Insights table
                self._recalculate_insights(session_factory=self.SessionLocal, workspace_id=workspace_id)
            except Exception:
                session.rollback()
                raise
                
        return extraction.document_id

    def _recalculate_insights(self, session_factory, workspace_id: str):
        """
        Materialized View logic: Recalculates and persists per-workspace metrics.
        """
        from bdis.core.financials import convert_to_usd
        from datetime import date
        
        with session_factory() as session:
            all_ext = session.query(ExtractionModel).filter_by(workspace_id=workspace_id).all()
            
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
            
            insights = session.query(InsightsModel).filter_by(workspace_id=workspace_id, id="current").first()
            if not insights:
                insights = InsightsModel(workspace_id=workspace_id, id="current")
                session.add(insights)
                
            insights.total_revenue_usd = total_rev
            insights.overdue_count = overdue
            insights.high_risk_count = high_risk
            insights.document_count = len(all_ext)
            insights.last_updated = date.today()
            
            session.commit()
        
    def get_all(self, workspace_id: str) -> list[DocumentExtraction]:
        """
        Retrieves normalized records and reconstructs the DocumentExtraction Domain Entity.
        """
        with self.SessionLocal() as session:
            # Query joined data
            records = (
                session.query(ExtractionModel)
                .join(DocumentModel)
                .filter(ExtractionModel.workspace_id == workspace_id)
                .all()
            )
            
            results = []
            for r in records:
                # Find matching evaluation if any
                evaluation_record = (
                    session.query(EvaluationModel)
                    .filter_by(workspace_id=workspace_id, document_id=r.document_id)
                    .first()
                )
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

    def get_by_document_id(self, workspace_id: str, document_id: str) -> DocumentExtraction | None:
        with self.SessionLocal() as session:
            r = (
                session.query(ExtractionModel)
                .filter_by(workspace_id=workspace_id, document_id=document_id)
                .order_by(ExtractionModel.created_at.desc())
                .first()
            )
            if not r:
                return None

            evaluation_record = (
                session.query(EvaluationModel)
                .filter_by(workspace_id=workspace_id, document_id=document_id)
                .first()
            )
            evaluation_result = None
            if evaluation_record:
                evaluation_result = EvaluationResult(
                    document_id=document_id,
                    accuracy=evaluation_record.accuracy,
                    field_scores=evaluation_record.field_scores_json,
                    confidence_score=evaluation_record.confidence_score,
                )

            doc = (
                session.query(DocumentModel)
                .filter_by(workspace_id=workspace_id, document_id=document_id)
                .first()
            )

            return DocumentExtraction(
                document_id=r.document_id,
                status=r.status,
                raw_text=r.raw_text or "",
                extracted_data=r.extracted_data_json or {},
                money=Money(r.amount_usd, r.currency or "USD"),
                company_name=r.company_name,
                due_date=r.due_date,
                s3_uri=doc.s3_uri if doc else None,
                confidence=r.confidence,
                evaluation=evaluation_result,
                error_message=r.error_message,
                trace_id=r.trace_id,
                created_at=r.created_at,
            )
            
    def get_all_raw(self, workspace_id: str) -> list[dict]:
        """
        Optimized 'Read Model' for UI Dashboard.
        """
        with self.SessionLocal() as session:
            records = (
                session.query(ExtractionModel)
                .join(DocumentModel)
                .filter(ExtractionModel.workspace_id == workspace_id)
                .all()
            )
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
