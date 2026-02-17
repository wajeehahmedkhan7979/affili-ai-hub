
import pytest
import httpx
import uuid
import asyncio
import json
from typing import AsyncGenerator, Generator
from sqlalchemy.orm import Session
from app.main import app
from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.models.tenant import Tenant
from app.core.logging import correlation_id_ctx

# Test IDs
TENANT_ID = "66666666-6666-6666-6666-666666666666"
USER_EMAIL = "obs_test@example.com"

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

def setup_obs_test(db: Session):
    # Ensure tenant
    t_id = uuid.UUID(TENANT_ID)
    tenant = db.query(Tenant).filter(Tenant.id == t_id).first()
    if not tenant:
        tenant = Tenant(id=t_id, name="Obs Test Tenant")
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
async def test_observability_flow(api_client: httpx.AsyncClient, db: Session):
    """Verify correlation IDs and health diagnostics."""
    setup_obs_test(db)
    headers = {
        "X-Tenant-ID": TENANT_ID,
        "X-User-Email": USER_EMAIL,
        "X-Correlation-ID": "test-correlation-123"
    }
    
    # 1. Check Correlation ID reflection
    resp = await api_client.get("/api/v1/health", headers=headers)
    assert resp.status_code == 200
    assert resp.headers.get("X-Correlation-ID") == "test-correlation-123"
    
    # 2. Check Diagnostics
    diag_resp = await api_client.get("/api/v1/observability/health/diagnostics", headers=headers)
    print(f"DIAG RESP: {diag_resp.json()}")
    assert diag_resp.status_code == 200
    data = diag_resp.json()
    assert data["status"] == "UP"
    assert "database" in data["components"]
    
    # 3. Check Overview Metrics
    metrics_resp = await api_client.get("/api/v1/observability/metrics/overview", headers=headers)
    print(f"METRICS RESP: {metrics_resp.json()}")
    assert metrics_resp.status_code == 200
    mdata = metrics_resp.json()
    assert "success_rate_24h" in mdata
    assert "avg_duration_seconds" in mdata

if __name__ == "__main__":
    async def run():
        db = SessionLocal()
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            print("1. Testing Observability Flow...")
            await test_observability_flow(client, db)
            print("\nPHASE 11 TESTS PASSED!")
        db.close()
    
    asyncio.run(run())
