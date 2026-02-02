"""
Tests for Phase 7 multi-tenant isolation.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.db.session import get_db
from app.models.tenant import Tenant
import uuid

client = TestClient(app)

# Test Data
TENANT_A_ID = str(uuid.uuid4())
TENANT_B_ID = str(uuid.uuid4())
TENANT_A_NAME = "Tenant A"
TENANT_B_NAME = "Tenant B"


@pytest.fixture
def setup_tenants(db: Session):
    """Create two test tenants."""
    # Create Tenant A
    tenant_a = Tenant(id=uuid.UUID(TENANT_A_ID), name=TENANT_A_NAME)
    db.add(tenant_a)
    
    # Create Tenant B
    tenant_b = Tenant(id=uuid.UUID(TENANT_B_ID), name=TENANT_B_NAME)
    db.add(tenant_b)
    
    db.commit()
    yield
    
    # Cleanup
    db.query(Tenant).filter(Tenant.id.in_([uuid.UUID(TENANT_A_ID), uuid.UUID(TENANT_B_ID)])).delete(synchronize_session=False)
    db.commit()


def test_tenant_isolation_programs(setup_tenants, db: Session):
    """Test that programs are isolated between tenants."""
    
    # 1. Create Program as Tenant A
    headers_a = {"X-Tenant-ID": TENANT_A_ID}
    resp = client.post(
        "/api/v1/programs",
        headers=headers_a,
        json={
            "name": "Program A",
            "signup_url": "http://example.com/a",
            "affiliate_url": "http://example.com/a?ref=me"
        }
    )
    assert resp.status_code == 201
    prog_a_id = resp.json()["id"]
    
    # 2. Create Program as Tenant B
    headers_b = {"X-Tenant-ID": TENANT_B_ID}
    resp = client.post(
        "/api/v1/programs",
        headers=headers_b,
        json={
            "name": "Program B",
            "signup_url": "http://example.com/b",
            "affiliate_url": "http://example.com/b?ref=me"
        }
    )
    assert resp.status_code == 201
    prog_b_id = resp.json()["id"]
    
    # 3. List programs as Tenant A - should only see Program A
    resp = client.get("/api/v1/programs", headers=headers_a)
    assert resp.status_code == 200
    programs_a = resp.json()
    ids_a = [p["id"] for p in programs_a]
    assert prog_a_id in ids_a
    assert prog_b_id not in ids_a
    
    # 4. List programs as Tenant B - should only see Program B
    resp = client.get("/api/v1/programs", headers=headers_b)
    assert resp.status_code == 200
    programs_b = resp.json()
    ids_b = [p["id"] for p in programs_b]
    assert prog_b_id in ids_b
    assert prog_a_id not in ids_b


def test_tenant_isolation_tasks(setup_tenants, db: Session):
    """Test that tasks are isolated between tenants."""
    
    # 1. Create Task as Tenant A
    headers_a = {"X-Tenant-ID": TENANT_A_ID}
    resp = client.post(
        "/api/v1/tasks",
        headers=headers_a,
        json={
            "task_type": "DISCOVER_PROGRAM",
            "payload": {"query": "fitness"}
        }
    )
    assert resp.status_code == 201
    task_a_id = resp.json()["id"]
    
    # 2. Create Task as Tenant B
    headers_b = {"X-Tenant-ID": TENANT_B_ID}
    resp = client.post(
        "/api/v1/tasks",
        headers=headers_b,
        json={
            "task_type": "DISCOVER_PROGRAM",
            "payload": {"query": "crypto"}
        }
    )
    assert resp.status_code == 201
    task_b_id = resp.json()["id"]
    
    # 3. List tasks as Tenant A
    resp = client.get("/api/v1/tasks", headers=headers_a)
    assert resp.status_code == 200
    tasks_a = resp.json()
    ids_a = [t["id"] for t in tasks_a]
    assert task_a_id in ids_a
    assert task_b_id not in ids_a
    
    # 4. Attempt to access Task B as Tenant A (should fail)
    resp = client.get(f"/api/v1/tasks/{task_b_id}", headers=headers_a)
    assert resp.status_code == 404  # Not Found (security through obscurity)


def test_default_tenant_fallback(db: Session):
    """Test fallback to default tenant when header is missing."""
    
    # Create request without header
    resp = client.get("/api/v1/programs")
    assert resp.status_code == 200
    # Should not crash and return list (empty or default tenant data)
