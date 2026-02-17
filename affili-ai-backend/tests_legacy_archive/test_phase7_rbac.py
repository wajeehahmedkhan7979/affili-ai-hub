"""
Tests for Phase 7.2 RBAC.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.models.tenant import Tenant
from app.models.user import User, UserRole
import uuid

client = TestClient(app)

# Test Data
TENANT_ID = str(uuid.uuid4())
TENANT_NAME = "RBAC Test Tenant"

# User IDs
OWNER_EMAIL = "owner@test.com"
ADMIN_EMAIL = "admin@test.com"
OPERATOR_EMAIL = "operator@test.com"
VIEWER_EMAIL = "viewer@test.com"


@pytest.fixture
def setup_rbac_tenant(db: Session):
    """Create a tenant and users with different roles."""
    # Create Tenant
    tenant = Tenant(id=uuid.UUID(TENANT_ID), name=TENANT_NAME)
    db.add(tenant)
    
    # Create Users
    users = [
        User(tenant_id=uuid.UUID(TENANT_ID), email=OWNER_EMAIL, role=UserRole.OWNER),
        User(tenant_id=uuid.UUID(TENANT_ID), email=ADMIN_EMAIL, role=UserRole.ADMIN),
        User(tenant_id=uuid.UUID(TENANT_ID), email=OPERATOR_EMAIL, role=UserRole.OPERATOR),
        User(tenant_id=uuid.UUID(TENANT_ID), email=VIEWER_EMAIL, role=UserRole.VIEWER),
    ]
    db.add_all(users)
    
    db.commit()
    yield
    
    # Cleanup
    db.query(User).filter(User.tenant_id == uuid.UUID(TENANT_ID)).delete(synchronize_session=False)
    db.query(Tenant).filter(Tenant.id == uuid.UUID(TENANT_ID)).delete(synchronize_session=False)
    db.commit()


def get_headers(email: str, tenant_id: str = TENANT_ID):
    return {
        "X-Tenant-ID": tenant_id,
        "X-User-Email": email
    }


def test_rbac_task_creation(setup_rbac_tenant):
    """Test task creation permissions."""
    
    payload = {"task_type": "DISCOVER_PROGRAM", "payload": {"query": "test"}}
    
    # OWNER -> Allowed
    resp = client.post("/api/v1/tasks", headers=get_headers(OWNER_EMAIL), json=payload)
    assert resp.status_code == 201
    
    # ADMIN -> Allowed
    resp = client.post("/api/v1/tasks", headers=get_headers(ADMIN_EMAIL), json=payload)
    assert resp.status_code == 201
    
    # OPERATOR -> Allowed
    resp = client.post("/api/v1/tasks", headers=get_headers(OPERATOR_EMAIL), json=payload)
    assert resp.status_code == 201
    
    # VIEWER -> Forbidden
    resp = client.post("/api/v1/tasks", headers=get_headers(VIEWER_EMAIL), json=payload)
    assert resp.status_code == 403


def test_rbac_program_management(setup_rbac_tenant):
    """Test program management permissions."""
    
    payload = {
        "name": "Test Program",
        "signup_url": "http://example.com/signup",
        "affiliate_url": "http://example.com/aff"
    }
    
    # OWNER -> Allowed
    resp = client.post("/api/v1/programs", headers=get_headers(OWNER_EMAIL), json=payload)
    assert resp.status_code == 201
    prog_id = resp.json()["id"]
    
    # ADMIN -> Allowed (Update)
    resp = client.put(f"/api/v1/programs/{prog_id}", headers=get_headers(ADMIN_EMAIL), json={"name": "Updated"})
    assert resp.status_code == 200
    
    # OPERATOR -> Forbidden
    resp = client.post("/api/v1/programs", headers=get_headers(OPERATOR_EMAIL), json=payload)
    assert resp.status_code == 403
    
    # VIEWER -> Forbidden
    resp = client.post("/api/v1/programs", headers=get_headers(VIEWER_EMAIL), json=payload)
    assert resp.status_code == 403


def test_rbac_reports(setup_rbac_tenant):
    """Test report access permissions."""
    
    # OWNER -> Allowed
    resp = client.get("/api/v1/reports/execution", headers=get_headers(OWNER_EMAIL))
    assert resp.status_code == 200
    
    # ADMIN -> Allowed
    resp = client.get("/api/v1/reports/execution", headers=get_headers(ADMIN_EMAIL))
    assert resp.status_code == 200
    
    # OPERATOR -> Forbidden
    resp = client.get("/api/v1/reports/execution", headers=get_headers(OPERATOR_EMAIL))
    assert resp.status_code == 403
    
    # VIEWER -> Forbidden
    resp = client.get("/api/v1/reports/execution", headers=get_headers(VIEWER_EMAIL))
    assert resp.status_code == 403


def test_rbac_agents(setup_rbac_tenant):
    """Test agent management permissions."""
    
    # OWNER -> Allowed
    resp = client.get("/api/v1/agents", headers=get_headers(OWNER_EMAIL))
    assert resp.status_code == 200
    
    # ADMIN -> Forbidden
    resp = client.get("/api/v1/agents", headers=get_headers(ADMIN_EMAIL))
    assert resp.status_code == 403


def test_missing_identity_header(setup_rbac_tenant):
    """Test missing X-User-Email header."""
    
    # Missing header -> 403 (enforced by dependency)
    resp = client.get("/api/v1/reports/execution", headers={"X-Tenant-ID": TENANT_ID})
    assert resp.status_code == 403


def test_cross_tenant_user_access(setup_rbac_tenant):
    """Test accessing with valid user but wrong tenant ID."""
    
    # User exists in TENANT_ID, but we send request with DIFFERENT_TENANT_ID
    # Since user is scoped to tenant, this user shouldn't exist in the other tenant context
    
    other_tenant_id = str(uuid.uuid4())
    resp = client.get(
        "/api/v1/reports/execution", 
        headers={"X-Tenant-ID": other_tenant_id, "X-User-Email": OWNER_EMAIL}
    )
    # verify_tenant checks if tenant exists first. If random tenant doesn't exist -> 404
    # If tenant existed but user didn't belong to it -> 403
    
    # Let's expect 404 because verify_tenant runs first and tenant doesn't exist
    assert resp.status_code == 404
