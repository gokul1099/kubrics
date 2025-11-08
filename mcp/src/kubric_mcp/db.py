from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from typing import Generator
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://user:password@localhost:5432/mydb")

engine = create_engine(DATABASE_URL, echo=True)


def init_db():
    from kubric_mcp.models import Base

    """Initialize database and create pgvector extension"""
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    ##Drop all data
    print("Dropping data")
    Base.metadata.drop_all(engine)
    print("Create data")
    Base.metadata.create_all(engine)
    print("Database tables created successfully")


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session() -> Generator[Session, None, None]:
    """Dependency for getting database session"""
    with SessionLocal() as session:
        yield session
