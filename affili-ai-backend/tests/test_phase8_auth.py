
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
from app.services.auth_service import get_password_hash

# Test IDs
TENANT_ID = "33333333-3333-3333-3333-333333333333"
USER_EMAIL = "auth_test@example.com"
USER_PWD = "secure_password"

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

def setup_auth_user(db: Session):
    # Ensure tenant
    t_id = uuid.UUID(TENANT_ID)
    tenant = db.query(Tenant).filter(Tenant.id == t_id).first()
    if not tenant:
        tenant = Tenant(id=t_id, name="Auth Test Tenant")
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
            hashed_password=get_password_hash(USER_PWD),
            is_active=True
        )
        db.add(user)
        db.commit()
    elif not user.hashed_password:
        user.hashed_password = get_password_hash(USER_PWD)
        db.commit()
    return user

@pytest.mark.asyncio
async def test_auth_flow(api_client: httpx.AsyncClient, db: Session):
    """Verify login, token access, and refresh."""
    setup_auth_user(db)
    
    # 1. Login
    login_resp = await api_client.post(
        "/api/v1/auth/login",
        json={
            "email": USER_EMAIL,
            "password": USER_PWD,
            "tenant_id": TENANT_ID
        }
    )
    assert login_resp.status_code == 200
    tokens = login_resp.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]
    
    # 2. Access protected endpoint with token
    # Using /api/v1/tasks as a test
    resp = await api_client.get(
        "/api/v1/tasks",
        headers={
            "X-Tenant-ID": TENANT_ID,
            "Authorization": f"Bearer {access_token}"
        }
    )
    assert resp.status_code == 200
    
    # 3. Access with invalid token
    bad_resp = await api_client.get(
        "/api/v1/tasks",
        headers={
            "X-Tenant-ID": TENANT_ID,
            "Authorization": "Bearer invalid_token"
        }
    )
    assert bad_resp.status_code == 401
    
    # 4. Refresh token
    refresh_resp = await api_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    assert refresh_resp.status_code == 200
    new_tokens = refresh_resp.json()
    assert "access_token" in new_tokens
    assert new_tokens["access_token"] != access_token

@pytest.mark.asyncio
async def test_cross_tenant_token_rejection(api_client: httpx.AsyncClient, db: Session):
    """Verify that a token for Tenant A cannot be used with Tenant B header."""
    setup_auth_user(db)
    
    # Login for Tenant A
    login_resp = await api_client.post(
        "/api/v1/auth/login",
        json={"email": USER_EMAIL, "password": USER_PWD, "tenant_id": TENANT_ID}
    )
    token = login_resp.json()["access_token"]
    
    # Try using this token with a DIFFERENT tenant ID in header
    other_tenant = str(uuid.uuid4())
    # Note: verify_tenant might fail 404 if other_tenant doesn't exist, 
    # but the check in get_current_user should catch the mismatch.
    
    # Create the other tenant first to ensure we reach the security check
    db.add(Tenant(id=uuid.UUID(other_tenant), name="Other Tenant"))
    db.commit()
    
    resp = await api_client.get(
        "/api/v1/tasks",
        headers={
            "X-Tenant-ID": other_tenant,
            "Authorization": f"Bearer {token}"
        }
    )
    # Should be 403 Forbidden due to tid mismatch in token vs header
    assert resp.status_code == 403
    assert "Token tenant mismatch" in resp.json()["detail"]

if __name__ == "__main__":
    async def run():
        db = SessionLocal()
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            print("1. Testing Auth Flow...")
            await test_auth_flow(client, db)
            print("2. Testing Cross-Tenant Boundary...")
            await test_cross_tenant_token_rejection(client, db)
            print("\nPHASE 8 TESTS PASSED!")
        db.close()
    
    asyncio.run(run())
