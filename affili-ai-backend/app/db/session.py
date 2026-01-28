"""
Database session management using SQLAlchemy.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

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


# Lazy-loaded engine and session
_engine = None
_SessionLocal = None


def _initialize():
    """Initialize engine and session on first use."""
    global _engine, _SessionLocal
    if _engine is None:
        _engine = get_engine()
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


# Expose engine and SessionLocal directly
@property
def engine():
    """Get the database engine."""
    _initialize()
    return _engine


def get_engine_instance():
    """Get database engine instance."""
    _initialize()
    return _engine


SessionLocal = None

def _get_session_local():
    """Get the SessionLocal factory."""
    _initialize()
    return _SessionLocal


def get_db() -> Session:
    """Dependency for getting database session."""
    _initialize()
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()
