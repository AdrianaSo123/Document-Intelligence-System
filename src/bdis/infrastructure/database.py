from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from bdis.adapters.repositories import Base

def init_database(db_url: str):
    """
    Infrastructure helper to initialize the database and create schema.
    This keeps the Repository humble and focused only on data access.
    """
    connect_args = {"check_same_thread": False} if "sqlite" in db_url else {}
    engine = create_engine(db_url, connect_args=connect_args)
    Base.metadata.create_all(engine)
    return engine, sessionmaker(autoflush=False, bind=engine)
