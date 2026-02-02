
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
from app.models.billing import BillingPlan, TenantBilling, BillingStatus
from app.models.usage import TenantUsage
from datetime import date, datetime

# Test IDs
TENANT_ID = "44444444-4444-4444-4444-444444444444"
USER_EMAIL = "billing_test@example.com"

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

def setup_billing_test(db: Session):
    # Ensure tenant
    t_id = uuid.UUID(TENANT_ID)
    tenant = db.query(Tenant).filter(Tenant.id == t_id).first()
    if not tenant:
        tenant = Tenant(id=t_id, name="Billing Test Tenant")
        db.add(tenant)
        db.commit()
    
    # Ensure user (using header auth for simplicity in this test)
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
    
    # Ensure billing (Start with Pro to have high limits, then we'll swap to Free)
    pro_plan = db.query(BillingPlan).filter(BillingPlan.name == "Pro").first()
    billing = db.query(TenantBilling).filter(TenantBilling.tenant_id == t_id).first()
    if not billing:
        billing = TenantBilling(
            tenant_id=t_id,
            plan_id=pro_plan.id,
            status=BillingStatus.ACTIVE,
            cycle_start=datetime.utcnow()
        )
        db.add(billing)
        db.commit()
    else:
        billing.plan_id = pro_plan.id
        billing.status = BillingStatus.ACTIVE
        db.commit()
        
    return user

@pytest.mark.asyncio
async def test_billing_enforcement(api_client: httpx.AsyncClient, db: Session):
    """Verify that task creation is blocked when limits are reached."""
    setup_billing_test(db)
    headers = {
        "X-Tenant-ID": TENANT_ID,
        "X-User-Email": USER_EMAIL
    }
    
    # 1. Check status
    status_resp = await api_client.get("/api/v1/billing/status", headers=headers)
    assert status_resp.status_code == 200
    data = status_resp.json()
    assert data["plan_name"] == "Pro"
    
    # 2. Simulate reaching limit
    # Swap to Free plan (limit 10)
    free_plan = db.query(BillingPlan).filter(BillingPlan.name == "Free").first()
    billing = db.query(TenantBilling).filter(TenantBilling.tenant_id == uuid.UUID(TENANT_ID)).first()
    billing.plan_id = free_plan.id
    db.commit()
    
    # Record 10 tasks in current cycle
    usage = db.query(TenantUsage).filter(
        TenantUsage.tenant_id == uuid.UUID(TENANT_ID),
        TenantUsage.date == date.today()
    ).first()
    if not usage:
        usage = TenantUsage(tenant_id=uuid.UUID(TENANT_ID), date=date.today(), tasks_created=10)
        db.add(usage)
    else:
        usage.tasks_created = 10
    db.commit()
    
    # 3. Try to create 11th task
    task_resp = await api_client.post(
        "/api/v1/tasks",
        headers=headers,
        json={"task_type": "billing_limit_test", "payload": {}}
    )
    # Should be 402 Payment Required
    assert task_resp.status_code == 402
    assert "limit reached" in task_resp.json()["detail"]
    
    # 4. Try with suspended status
    billing.status = BillingStatus.SUSPENDED
    db.commit()
    
    task_resp_2 = await api_client.post(
        "/api/v1/tasks",
        headers=headers,
        json={"task_type": "billing_suspended_test", "payload": {}}
    )
    assert task_resp_2.status_code == 402
    assert "suspended" in task_resp_2.json()["detail"]

if __name__ == "__main__":
    async def run():
        db = SessionLocal()
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            print("1. Testing Billing Enforcement...")
            await test_billing_enforcement(client, db)
            print("\nPHASE 9 TESTS PASSED!")
        db.close()
    
    asyncio.run(run())
