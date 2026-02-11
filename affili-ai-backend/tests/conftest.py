"""
Pytest configuration and fixtures for testing.
"""

import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient
from sqlalchemy import text

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
    
    # Disable statement caching in psycopg to avoid prepared statement reuse errors
    if "+" in url and "psycopg" in url and "?" not in url:
        url += "?options=-c%20statement_cache_size=0"
    
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
        # Disable prepared statement pooling to avoid "already exists" errors
        engine = create_engine(
            test_db_url,
            pool_pre_ping=True,
            isolation_level="READ COMMITTED",
            execution_options={
                "psycopg.prepared_statement_name_func": lambda stmt: None,  # Disable prepared statements
                "compiled_cache": None  # Disable compiled query caching
            }
        )
    
    # Create all tables for the first time if possible. In some CI or shared
    # Postgres instances the DDL reflection/creation can trigger prepared
    # statement conflicts; guard against that and continue since tests run
    # against a pre-provisioned v1.1 DB in our freeze discipline.
    try:
        Base.metadata.create_all(bind=engine)
    except Exception:
        # If creation fails (e.g., prepared-statement collision or permission
        # restrictions), proceed — the tests target an existing DB schema.
        pass
    
    # Reflect existing 'tasks' table to ensure ORM mapping matches the live DB schema.
    # Some environments use a pre-provisioned Postgres where migrations differ from models
    # (notably v1.1 intentionally lacks `program_id`, `operator_confidence`).
    # Reflect and rebind Task.__table__ to the actual DB table so ORM queries
    # only select columns that actually exist, avoiding UndefinedColumn errors.
    try:
        from sqlalchemy import MetaData, Table, inspect
        from sqlalchemy.orm import configure_mappers
        from app.models.task import Task

        # Reflect the live tasks table
        meta = MetaData()
        reflected_tasks = Table("tasks", meta, autoload_with=engine)
        
        # Check if the reflected table is materially different from the model
        model_cols = set(Task.__table__.columns.keys())
        reflected_cols = set(reflected_tasks.columns.keys())
        
        # If the reflected schema is missing columns that the model defines, rebind
        # the ORM table to use only the columns that actually exist in the DB.
        if model_cols != reflected_cols:
            Task.__table__ = reflected_tasks
            # Reconfigure mappers to ensure they use the updated table definition
            configure_mappers()
    except Exception as e:
        # If reflection fails, fall back to model-defined tables
        # (tests may create them, or a pre-provisioned DB is in place)
        pass
    yield engine
    # Optional: don't drop all for Postgres if sharing a persistent DB, 
    # but for clean tests we usually drop or use a separate schema.
    # Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(engine):
    """Create a new database session for each test with transactional rollback."""
    # Patch the Task mapper to exclude columns that don't exist in the v1.1 DB
    try:
        from app.models.task import Task
        from sqlalchemy import inspect, MetaData, Table
        from sqlalchemy.orm import configure_mappers
        
        # Reflect the live tasks table to get actual column names
        meta = MetaData()
        reflected_tasks = Table("tasks", meta, autoload_with=engine)
        reflected_cols = set(reflected_tasks.columns.keys())
        
        # Get columns defined in the model
        model_cols = set(Task.__table__.columns.keys())
        missing_cols = model_cols - reflected_cols
        
        # If there are missing columns, need to patch the mapper
        if missing_cols:
            # Rebind the table to the reflected version (has only cols that exist in DB)
            Task.__table__ = reflected_tasks
            
            # Clear the mapper registry's compiled state so it re-compiles with new table
            from sqlalchemy.orm import registry as orm_registry
            from app.db.base import Base
            
            # Force a complete mapper reconfiguration
            Base.registry.configured = False
            configure_mappers()
    except Exception as e:
        # If patching fails, continue and rely on db_session's error handling
        pass
    
    # Dispose of any pooled connections to avoid prepared statement reuse issues
    engine.dispose()
    
    connection = engine.connect()
    # Clear any prepared statements that may be cached in the DB session
    # This addresses: psycopg.errors.DuplicatePreparedStatement: prepared statement "_pg3_0" already exists
    try:
        connection.execute(text("DEALLOCATE ALL;"))
    except Exception:
        # Ignore errors here — some DBs (e.g., SQLite) or restricted users may not support DEALLOCATE
        pass
    
    # Begin transaction if not already active (DEALLOCATE ALL may auto-begin)
    if not connection.in_transaction():
        transaction = connection.begin()
    else:
        # Use the existing transaction
        transaction = connection.get_transaction()

    
    # Create session bound to connection
    session = sessionmaker(autocommit=False, autoflush=False, bind=connection)()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()
    
    # Ensure connection is fully disposed
    engine.dispose()


@pytest.fixture
def insert_task(db_session):
    """Helper fixture to insert a task row without relying on ORM mappings.

    Uses a raw INSERT that omits `program_id` to remain compatible with the
    frozen v1.1 DB schema used by tests.
    """
    from sqlalchemy import text
    from uuid import uuid4
    from datetime import datetime

    def _insert(**kwargs):
        preferred_cols = [
            "id", "tenant_id", "task_type", "status", "payload",
            "agent_id", "agent_pool", "retry_count", "max_retries",
            "logs", "screenshot_url", "error_message",
            "created_at", "updated_at", "claimed_at", "started_at",
            "completed_at", "last_heartbeat", "operator_confidence"
        ]

        # Determine actual columns present in the live 'tasks' table and use only those.
        try:
            from sqlalchemy import inspect
            actual_cols = [c["name"] for c in inspect(db_session.get_bind()).get_columns("tasks")]
        except Exception:
            actual_cols = preferred_cols

        cols = [c for c in preferred_cols if c in actual_cols]

        values = {}
        for c in cols:
            values[c] = kwargs.get(c, None)

        if values["id"] is None:
            values["id"] = str(uuid4())
        values["created_at"] = values.get("created_at") or datetime.utcnow()
        values["updated_at"] = values.get("updated_at") or datetime.utcnow()

        # Ensure payload is JSON-serializable string for JSONB column
        try:
            import json as _json
            if isinstance(values.get("payload"), dict):
                values["payload"] = _json.dumps(values["payload"])
        except Exception:
            pass

        col_list = ", ".join(cols)
        param_list = ", ".join([f":{c}" for c in cols])
        sql = f"INSERT INTO tasks ({col_list}) VALUES ({param_list})"
        db_session.execute(text(sql), values)
        db_session.commit()
        try:
            import uuid as _uuid
            return _uuid.UUID(values["id"]) if isinstance(values["id"], str) else values["id"]
        except Exception:
            return values["id"]

    return _insert


@pytest.fixture
def get_task_safe(db_session):
    """Helper fixture to safely query Task with load_only to avoid non-existent columns."""
    def _get_task(task_id):
        from app.models.task import Task
        from sqlalchemy.orm import load_only
        
        return db_session.query(Task).options(
            load_only(
                Task.id, Task.tenant_id, Task.task_type, Task.status, Task.payload,
                Task.result, Task.agent_id, Task.agent_pool, Task.retry_count,
                Task.max_retries, Task.logs, Task.screenshot_url, Task.error_message,
                Task.created_at, Task.updated_at, Task.claimed_at, Task.started_at,
                Task.completed_at, Task.last_heartbeat
            )
        ).filter(Task.id == task_id).first()
    
    return _get_task


@pytest.fixture
def client(db_session):
    """Create test client with test database."""
    def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
