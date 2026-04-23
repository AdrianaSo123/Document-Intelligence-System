import uuid
from sqlalchemy import Column, String, Float, Date, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from bdis.domain.entities import DocumentInsight
from bdis.ports.document_repository import IDocumentRepository

Base = declarative_base()

class DocumentInsightModel(Base):
    __tablename__ = "document_insights"
    id = Column(String, primary_key=True)
    company_name = Column(String, nullable=True)
    amount_usd = Column(Float, nullable=False, default=0.0)
    status = Column(String, nullable=False, default="unknown")
    due_date = Column(Date, nullable=False)
    s3_uri = Column(String, nullable=True)

class SQLDocumentRepository(IDocumentRepository):
    def __init__(self, db_url="sqlite:///bdis_dev.db"):
        connect_args = {"check_same_thread": False} if "sqlite" in db_url else {}
        self.engine = create_engine(db_url, connect_args=connect_args)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(autoflush=False, bind=self.engine)

    def save(self, insight: DocumentInsight) -> str:
        db_id = str(uuid.uuid4())
        
        model = DocumentInsightModel(
            id=db_id,
            company_name=insight.company_name,
            amount_usd=insight.amount_usd,
            status=insight.status,
            due_date=insight.due_date,
            s3_uri=insight.s3_uri
        )
        
        with self.SessionLocal() as session:
            session.add(model)
            session.commit()
            
        return db_id
        
    def get_all(self) -> list[DocumentInsight]:
        with self.SessionLocal() as session:
            records = session.query(DocumentInsightModel).all()
            return [
                DocumentInsight(
                    company_name=r.company_name,
                    amount_usd=r.amount_usd,
                    status=r.status,
                    due_date=r.due_date,
                    s3_uri=r.s3_uri
                ) for r in records
            ]
            
    def get_all_raw(self) -> list[dict]:
        with self.SessionLocal() as session:
            records = session.query(DocumentInsightModel).all()
            return [
                {
                    "document_id": r.id,
                    "company_name": r.company_name,
                    "amount_usd": r.amount_usd,
                    "status": r.status,
                    "due_date": r.due_date,
                    "s3_uri": r.s3_uri
                } for r in records
            ]
