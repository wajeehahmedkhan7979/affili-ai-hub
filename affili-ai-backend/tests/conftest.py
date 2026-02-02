"""
Pytest configuration and fixtures for testing.
"""

import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.core.config import settings


@pytest.fixture(scope="session")
def test_db_url():
    """Use PostgreSQL for tests if configured, else fallback to settings."""
    # Priority: 1. TEST_DATABASE_URL env var 2. settings.DATABASE_URL
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        url = settings.DATABASE_URL
    
    # Ensure correctly formatted postgres URL for sqlalchemy + psycopg
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    
    return url


@pytest.fixture(scope="session")
def engine(test_db_url):
    """Create test database engine."""
    if "sqlite" in test_db_url:
        engine = create_engine(
            test_db_url,
            connect_args={"check_same_thread": False},
        )
    else:
        # PostgreSQL configurations
        engine = create_engine(
            test_db_url,
            pool_pre_ping=True,
            isolation_level="READ COMMITTED"
        )
    
    # Create all tables for the first time
    Base.metadata.create_all(bind=engine)
    yield engine
    # Optional: don't drop all for Postgres if sharing a persistent DB, 
    # but for clean tests we usually drop or use a separate schema.
    # Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(engine):
    """Create a new database session for each test with transactional rollback."""
    connection = engine.connect()
    transaction = connection.begin()
    
    # Create session bound to connection
    session = sessionmaker(autocommit=False, autoflush=False, bind=connection)()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    """Create test client with test database."""
    def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
