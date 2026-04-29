from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from bdis.infrastructure.persistence.models import Base
import os

def init_database(db_url: str):
    """
    Infrastructure helper to initialize the database and create schema.
    This keeps the Repository humble and focused only on data access.
    """
    connect_args = {"check_same_thread": False} if "sqlite" in db_url else {}
    engine = create_engine(db_url, connect_args=connect_args)
    # Enterprise rule: migrations (Alembic) are the source of truth for schema.
    # Auto-create is only allowed when explicitly enabled (e.g., quick local demos).
    if os.getenv("BDIS_DB_AUTO_CREATE", "0").lower() in {"1", "true", "yes"}:
        Base.metadata.create_all(engine)
    return engine, sessionmaker(autoflush=False, bind=engine)
