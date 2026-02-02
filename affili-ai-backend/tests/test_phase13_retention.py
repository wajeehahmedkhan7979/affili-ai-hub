
import pytest
import httpx
import uuid
import asyncio
from typing import AsyncGenerator, Generator
from sqlalchemy.orm import Session
from app.main import app
from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.models.tenant import Tenant
from app.models.retention import RetentionRule
from app.models.task import Task, TaskStatus, TaskType
from datetime import datetime, timedelta

# Test IDs
TENANT_ID = "88888888-8888-8888-8888-888888888888"
USER_EMAIL = "retention_test@example.com"

@pytest.fixture(scope="function")
async def api_client() -> AsyncGenerator:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

@pytest.fixture(scope="function")
def db() -> Generator:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def setup_retention_test(db: Session):
    # Ensure tenant
    t_id = uuid.UUID(TENANT_ID)
    tenant = db.query(Tenant).filter(Tenant.id == t_id).first()
    if not tenant:
        tenant = Tenant(id=t_id, name="Retention Test Tenant")
        db.add(tenant)
        db.commit()
    
    # Ensure user
    user = db.query(User).filter(User.email == USER_EMAIL, User.tenant_id == t_id).first()
    if not user:
        user = User(
            id=uuid.uuid4(),
            tenant_id=t_id,
            email=USER_EMAIL,
            role=UserRole.ADMIN,
            is_active=True
        )
        db.add(user)
        db.commit()
        
    return user

@pytest.mark.asyncio
async def test_data_retention_flow(api_client: httpx.AsyncClient, db: Session):
    """Verify data purging and legal hold overrides."""
    setup_retention_test(db)
    headers = {
        "X-Tenant-ID": TENANT_ID,
        "X-User-Email": USER_EMAIL
    }
    
    # 1. Create a Retention Rule (Purge tasks older than 30 days)
    rule_resp = await api_client.post(
        "/api/v1/retention/rules",
        headers=headers,
        json={"entity_type": "tasks", "retention_days": 30}
    )
    assert rule_resp.status_code == 200
    
    # 2. Create Old and New tasks
    old_date = datetime.utcnow() - timedelta(days=40)
    new_date = datetime.utcnow() - timedelta(days=5)
    
    old_id = uuid.uuid4()
    new_id = uuid.uuid4()
    
    t_old = Task(id=old_id, tenant_id=uuid.UUID(TENANT_ID), task_type=TaskType.DISCOVER_PROGRAM, status="COMPLETED", created_at=old_date)
    t_new = Task(id=new_id, tenant_id=uuid.UUID(TENANT_ID), task_type=TaskType.DISCOVER_PROGRAM, status="COMPLETED", created_at=new_date)
    db.add_all([t_old, t_new])
    db.commit()
    
    # 3. Trigger Cleanup
    # First test LEGAL HOLD
    await api_client.post("/api/v1/retention/legal-hold?hold=true", headers=headers)
    
    cleanup_resp_hold = await api_client.post("/api/v1/retention/cleanup", headers=headers)
    assert cleanup_resp_hold.json()["deleted_count"] == 0
    
    # 4. Release Hold and Cleanup
    await api_client.post("/api/v1/retention/legal-hold?hold=false", headers=headers)
    cleanup_resp = await api_client.post("/api/v1/retention/cleanup", headers=headers)
    
    assert cleanup_resp.json()["deleted_count"] >= 1
    
    # Verify old task is gone, new task remains
    db.expire_all() # Ensure we get fresh data
    t_old_check = db.query(Task).filter(Task.id == old_id).first()
    t_new_check = db.query(Task).filter(Task.id == new_id).first()
    assert t_old_check is None
    assert t_new_check is not None

if __name__ == "__main__":
    async def run():
        db = SessionLocal()
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            print("1. Testing Data Retention Flow...")
            await test_data_retention_flow(client, db)
            print("\nPHASE 13 TESTS PASSED!")
        db.close()
    
    asyncio.run(run())
