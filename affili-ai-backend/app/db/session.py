"""
Database session management using SQLAlchemy.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings

settings = get_settings()


def get_engine(database_url: str = None):
    """Create and return database engine."""
    if database_url is None:
        database_url = settings.DATABASE_URL
    
    # Block SQLite in production if enforced
    is_sqlite = "sqlite" in database_url
    if is_sqlite and getattr(settings, "ENVIRONMENT", "development") == "production":
        raise RuntimeError("SQLite is strictly prohibited in PRODUCTION environment. Use a Postgres instance.")

    # Use in-memory SQLite for testing if URL contains sqlite
    if is_sqlite:
        return create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    else:
        # Ensure we use psycopg (v3) which is modern and handles async/sync well
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
        
        return create_engine(
            database_url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            echo=settings.DEBUG,
            isolation_level="READ COMMITTED"
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
def engine():
    """Get the database engine."""
    _initialize()
    return _engine


def get_engine_instance():
    """Get database engine instance."""
    _initialize()
    return _engine


def SessionLocal():
    """Get a new database session."""
    _initialize()
    return _SessionLocal()


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
