
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
from app.models.policy import Policy
from app.models.task import TaskType, TaskStatus
from datetime import date, datetime

# Test IDs
TENANT_ID = "77777777-7777-7777-7777-777777777777"
USER_EMAIL = "policy_test@example.com"

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

def setup_policy_test(db: Session):
    # Ensure tenant
    t_id = uuid.UUID(TENANT_ID)
    tenant = db.query(Tenant).filter(Tenant.id == t_id).first()
    if not tenant:
        tenant = Tenant(id=t_id, name="Policy Test Tenant")
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
async def test_policy_enforcement(api_client: httpx.AsyncClient, db: Session):
    """Verify that policies correctly block actions."""
    setup_policy_test(db)
    headers = {
        "X-Tenant-ID": TENANT_ID,
        "X-User-Email": USER_EMAIL
    }
    
    # 1. Create a Restricted Type policy
    policy_resp = await api_client.post(
        "/api/v1/policies",
        headers=headers,
        json={
            "name": "No Discovery",
            "rules": {"restricted_task_types": ["DISCOVER_PROGRAM"]},
            "is_active": True
        }
    )
    assert policy_resp.status_code == 200
    
    # 2. Try to create a DISCOVER_PROGRAM task
    task_resp = await api_client.post(
        "/api/v1/tasks",
        headers=headers,
        json={"task_type": "DISCOVER_PROGRAM", "payload": {}}
    )
    # Should be 403 Forbidden because of policy
    assert task_resp.status_code == 403
    assert "blocked by policy" in task_resp.json()["detail"]
    assert "DISCOVER_PROGRAM" in task_resp.json()["detail"]
    
    # 3. Check allowed type still works
    task_resp_ok = await api_client.post(
        "/api/v1/tasks",
        headers=headers,
        json={"task_type": "APPLY_PROGRAM", "payload": {}}
    )
    assert task_resp_ok.status_code == 201 or task_resp_ok.status_code == 200

if __name__ == "__main__":
    async def run():
        db = SessionLocal()
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            print("1. Testing Policy Enforcement...")
            await test_policy_enforcement(client, db)
            print("\nPHASE 12 TESTS PASSED!")
        db.close()
    
    asyncio.run(run())
