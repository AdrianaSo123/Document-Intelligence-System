import uuid
from sqlalchemy import Column, String, Float, Date, create_engine, JSON
from sqlalchemy.orm import declarative_base, sessionmaker
from bdis.domain.entities import DocumentExtraction
from bdis.ports.document_repository import IDocumentRepository

Base = declarative_base()

class DocumentExtractionModel(Base):
    __tablename__ = "document_extractions"
    id = Column(String, primary_key=True)
    document_id = Column(String, unique=True)
    trace_id = Column(String)
    company_name = Column(String, nullable=True)
    amount_usd = Column(Float, nullable=False, default=0.0)
    status = Column(String, nullable=False)
    due_date = Column(Date, nullable=True)
    confidence = Column(Float, default=0.0)
    error_message = Column(String, nullable=True)
    extracted_data = Column(JSON, nullable=True)
    s3_uri = Column(String, nullable=True)
    created_at = Column(Date)

class SQLDocumentRepository(IDocumentRepository):
    def __init__(self, db_url="sqlite:///bdis_dev.db"):
        connect_args = {"check_same_thread": False} if "sqlite" in db_url else {}
        self.engine = create_engine(db_url, connect_args=connect_args)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(autoflush=False, bind=self.engine)

    def save(self, extraction: DocumentExtraction) -> str:
        model = DocumentExtractionModel(
            id=str(uuid.uuid4()),
            document_id=extraction.document_id,
            trace_id=extraction.trace_id,
            company_name=extraction.company_name,
            amount_usd=extraction.amount_usd,
            status=extraction.status,
            due_date=extraction.due_date,
            confidence=extraction.confidence,
            error_message=extraction.error_message,
            extracted_data=extraction.extracted_data,
            s3_uri=extraction.s3_uri,
            created_at=extraction.created_at
        )
        
        with self.SessionLocal() as session:
            session.add(model)
            session.commit()
            
        return extraction.document_id
        
    def get_all(self) -> list[DocumentExtraction]:
        with self.SessionLocal() as session:
            records = session.query(DocumentExtractionModel).all()
            return [
                DocumentExtraction(
                    document_id=r.document_id,
                    status=r.status,
                    raw_text="", # Not stored in model currently
                    extracted_data=r.extracted_data or {},
                    amount_usd=r.amount_usd,
                    company_name=r.company_name,
                    due_date=r.due_date,
                    s3_uri=r.s3_uri,
                    confidence=r.confidence,
                    error_message=r.error_message,
                    trace_id=r.trace_id,
                    created_at=r.created_at
                ) for r in records
            ]
            
    def get_all_raw(self) -> list[dict]:
        with self.SessionLocal() as session:
            records = session.query(DocumentExtractionModel).all()
            return [
                {
                    "document_id": r.document_id,
                    "trace_id": r.trace_id,
                    "company_name": r.company_name,
                    "amount_usd": r.amount_usd,
                    "status": r.status,
                    "due_date": r.due_date,
                    "confidence": r.confidence,
                    "s3_uri": r.s3_uri
                } for r in records
            ]
