"""
Comprehensive tests for Phase 7 Enterprise Readiness features.
Covers:
7.1 Multi-Tenant Isolation
7.2 RBAC
7.3 Usage Metrics
7.4 Audit Logging
7.5 Export & Reporting
7.6 Retry & Recovery
"""

import pytest
import uuid
import asyncio
import httpx
from typing import AsyncGenerator, Generator
from sqlalchemy.orm import Session
from app.main import app
from app.db.session import SessionLocal
from app.core.tenant import set_tenant_id, get_tenant_id
from app.models.user import User, UserRole
from app.models.task import Task, TaskStatus
from app.models.tenant import Tenant
from app.models.usage import TenantUsage
from app.models.export_job import ExportJob, ExportStatus
from app.core.security import create_access_token

# Test Tenant IDs
TENANT_A_ID = "11111111-1111-1111-1111-111111111111"
TENANT_B_ID = "22222222-2222-2222-2222-222222222222"

@pytest.fixture(scope="function")
async def api_client() -> AsyncGenerator:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

@pytest.fixture(scope="function")
def db() -> Generator:
    # Use existing DB for now or mock? 
    # For Phase 7 integration logic, we want real DB behavior.
    # Note: This uses the actual configured DB (SQLite file).
    # Ideally should use test DB, but configured for simplicity in this environment.
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def setup_tenant(db: Session, tenant_id: str, name: str):
    """Ensure tenant exists."""
    tenant = db.query(Tenant).filter(Tenant.id == uuid.UUID(tenant_id)).first()
    if not tenant:
        tenant = Tenant(id=uuid.UUID(tenant_id), name=name)
        db.add(tenant)
        db.commit()
    return tenant

def create_user_headers(db: Session, tenant_id: str, role: UserRole, email_prefix: str) -> dict:
    """Create a user and return headers."""
    email = f"{email_prefix}@example.com"
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            tenant_id=uuid.UUID(tenant_id),
            email=email,
            role=role,
            is_active=True
        )
        db.add(user)
        db.commit()
    
    return {
        "X-Tenant-ID": tenant_id,
        "X-User-Email": email
    }

@pytest.mark.asyncio
async def test_tenant_isolation(api_client: httpx.AsyncClient, db: Session):
    """Phase 7.1: Verify tenant A cannot see tenant B's tasks."""
    setup_tenant(db, TENANT_A_ID, "Tenant A")
    setup_tenant(db, TENANT_B_ID, "Tenant B")
    
    headers_a = create_user_headers(db, TENANT_A_ID, UserRole.ADMIN, "admin_a")
    headers_b = create_user_headers(db, TENANT_B_ID, UserRole.ADMIN, "admin_b")
    
    # Create Task in Tenant A
    resp = await api_client.post(
        "/api/v1/tasks",
        headers=headers_a,
        json={"task_type": "DISCOVER_PROGRAM", "payload": {"q": "iso_test"}}
    )
    assert resp.status_code == 201
    task_id = resp.json()["id"]
    
    # Tenant B tries to list tasks
    resp_b = await api_client.get("/api/v1/tasks", headers=headers_b)
    assert resp_b.status_code == 200
    tasks_b = resp_b.json()
    # Should not contain task_id
    assert not any(t["id"] == task_id for t in tasks_b)
    
    # Tenant B tries to get specific task
    resp_b_get = await api_client.get(f"/api/v1/tasks/{task_id}", headers=headers_b)
    # Should return 404 Not Found (hidden)
    assert resp_b_get.status_code == 404

@pytest.mark.asyncio
async def test_rbac_enforcement(api_client: httpx.AsyncClient, db: Session):
    """Phase 7.2: Verify VIEWER cannot create tasks."""
    setup_tenant(db, TENANT_A_ID, "Tenant A")
    headers_viewer = create_user_headers(db, TENANT_A_ID, UserRole.VIEWER, "viewer_a")
    
    resp = await api_client.post(
        "/api/v1/tasks",
        headers=headers_viewer,
        json={"task_type": "DISCOVER_PROGRAM", "payload": {"q": "rbac_test"}}
    )
    assert resp.status_code == 403
    
@pytest.mark.asyncio
async def test_usage_tracking(api_client: httpx.AsyncClient, db: Session):
    """Phase 7.3: Verify usage counters increment."""
    setup_tenant(db, TENANT_A_ID, "Tenant A")
    headers_admin = create_user_headers(db, TENANT_A_ID, UserRole.ADMIN, "admin_a2")
    
    # Get current usage
    resp_usage = await api_client.get("/api/v1/usage", headers=headers_admin)
    initial_count = resp_usage.json()["totals"]["tasks_created"]
    
    # Create task
    await api_client.post(
        "/api/v1/tasks",
        headers=headers_admin,
        json={"task_type": "DISCOVER_PROGRAM", "payload": {"q": "usage_test"}}
    )
    
    # Verify increment
    resp_usage_after = await api_client.get("/api/v1/usage", headers=headers_admin)
    new_count = resp_usage_after.json()["totals"]["tasks_created"]
    
    assert new_count == initial_count + 1

@pytest.mark.asyncio
async def test_audit_logging(api_client: httpx.AsyncClient, db: Session):
    """Phase 7.4: Verify API action creates audit log."""
    setup_tenant(db, TENANT_A_ID, "Tenant A")
    headers_owner = create_user_headers(db, TENANT_A_ID, UserRole.OWNER, "owner_a")
    
    # Create task
    resp = await api_client.post(
        "/api/v1/tasks",
        headers=headers_owner,
        json={"task_type": "APPLY_PROGRAM", "payload": {"p": "audit_test"}}
    )
    task_id = resp.json()["id"]
    
    # Check audit logs
    resp_audit = await api_client.get("/api/v1/audit", headers=headers_owner)
    assert resp_audit.status_code == 200
    logs = resp_audit.json()
    
    # Look for TASK_CREATED event for this task
    found = False
    for log in logs:
        if log["event_type"] == "TASK_CREATED" and log["resource_id"] == task_id:
            found = True
            break
    assert found, "Audit log for TASK_CREATED not found"

@pytest.mark.asyncio
async def test_export_flow(api_client: httpx.AsyncClient, db: Session):
    """Phase 7.5: Verify export job creation and status."""
    setup_tenant(db, TENANT_A_ID, "Tenant A")
    headers_admin = create_user_headers(db, TENANT_A_ID, UserRole.ADMIN, "admin_a3")
    
    # Request export
    resp = await api_client.post(
        "/api/v1/exports",
        headers=headers_admin,
        json={"export_type": "tasks_csv"}
    )
    assert resp.status_code == 200
    export_id = resp.json()["id"]
    
    # Check status
    resp_status = await api_client.get(f"/api/v1/exports/{export_id}", headers=headers_admin)
    assert resp_status.status_code == 200
    assert resp_status.json()["status"] in ["PENDING", "PROCESSING", "COMPLETED"]

@pytest.mark.asyncio
async def test_retry_mechanism(api_client: httpx.AsyncClient, db: Session):
    """Phase 7.6: Verify task retry."""
    setup_tenant(db, TENANT_A_ID, "Tenant A")
    headers_admin = create_user_headers(db, TENANT_A_ID, UserRole.ADMIN, "admin_a4")
    
    # Create task
    resp = await api_client.post(
        "/api/v1/tasks",
        headers=headers_admin,
        json={"task_type": "DISCOVER_PROGRAM", "payload": {"q": "retry_test"}}
    )
    task_id = resp.json()["id"]
    
    # Manually fail it in DB
    task = db.query(Task).filter(Task.id == uuid.UUID(task_id)).first()
    task.status = TaskStatus.FAILED
    db.commit()
    
    # Retry via API
    resp_retry = await api_client.post(f"/api/v1/tasks/{task_id}/retry", headers=headers_admin)
    assert resp_retry.status_code == 200
    
    # Check status is PENDING
    assert resp_retry.json()["status"] == "PENDING"
    assert resp_retry.json()["retry_count"] == 1

if __name__ == "__main__":
    async def run_all():
        print("Starting Phase 7 Enterprise Verification...")
        # Setup session
        db = SessionLocal()
        try:
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                print("1. Tenant Isolation...")
                await test_tenant_isolation(client, db)
                print("2. RBAC Enforcement...")
                await test_rbac_enforcement(client, db)
                print("3. Usage Tracking...")
                await test_usage_tracking(client, db)
                print("4. Audit Logging...")
                await test_audit_logging(client, db)
                print("5. Export Flow...")
                await test_export_flow(client, db)
                print("6. Retry Mechanism...")
                await test_retry_mechanism(client, db)
                print("\nALL PHASE 7 TESTS PASSED!")
        except Exception as e:
            print(f"\nTEST FAILED: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            db.close()
            
    asyncio.run(run_all())
