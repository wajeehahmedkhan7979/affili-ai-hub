"""
Database session management using SQLAlchemy.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import os

from app.core.config import get_settings

settings = get_settings()


def get_engine():
    """Create and return database engine."""
    database_url = settings.DATABASE_URL
    
    # Use in-memory SQLite for testing if URL contains sqlite
    if "sqlite" in database_url:
        return create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    else:
        # PostgreSQL/Supabase
        return create_engine(
            database_url,
            pool_pre_ping=True,
            echo=settings.DEBUG,
        )


engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
