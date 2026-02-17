"""
Clean conftest.py for Full Product Certification (Phase 25).
Uses SQLite in-memory with StaticPool for speed.
Tables are recreated per-test for isolation.
"""
import pytest
import uuid
from datetime import datetime

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.core.config import get_settings

settings = get_settings()

# Shared engine — single connection for all tests
_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@pytest.fixture(autouse=True)
def reset_tables():
    """Drop and recreate all tables before each test for isolation."""
    Base.metadata.drop_all(bind=_engine)
    Base.metadata.create_all(bind=_engine)
    yield
    # no teardown needed — next test will drop+recreate


@pytest.fixture
def db_session():
    """Create a fresh DB session per test."""
    session = sessionmaker(autocommit=False, autoflush=False, bind=_engine)()
    yield session
    session.close()


@pytest.fixture
def client(db_session):
    """Create TestClient with overridden DB dependency."""
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def default_tenant_id():
    """The default tenant UUID used across tests."""
    return "00000000-0000-0000-0000-000000000000"


@pytest.fixture
def create_test_tenant(db_session, default_tenant_id):
    """Seed a default tenant into the DB."""
    from app.models.tenant import Tenant
    tenant = Tenant(id=uuid.UUID(default_tenant_id), name="Test Tenant")
    db_session.add(tenant)
    db_session.commit()
    return tenant


@pytest.fixture
def create_test_user(db_session, create_test_tenant):
    """Seed a test admin user and return (user, plain_password)."""
    from app.models.user import User, UserRole
    from app.services.auth_service import get_password_hash

    password = "testpassword123"
    user = User(
        id=uuid.uuid4(),
        tenant_id=create_test_tenant.id,
        email="testadmin@example.com",
        hashed_password=get_password_hash(password),
        role=UserRole.OWNER.value,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user, password


@pytest.fixture
def auth_headers(client, create_test_user, default_tenant_id):
    """Login and return auth headers dict."""
    user, password = create_test_user
    resp = client.post("/api/v1/auth/login", json={
        "email": user.email,
        "password": password,
        "tenant_id": default_tenant_id,
    })
    assert resp.status_code == 200, f"Auth setup failed: {resp.text}"
    token = resp.json()["access_token"]
    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": default_tenant_id,
    }


@pytest.fixture
def agent_headers(default_tenant_id):
    """Return headers for agent API calls."""
    return {
        "Authorization": f"Bearer {settings.AGENT_API_KEY}",
        "X-Tenant-ID": default_tenant_id,
    }
