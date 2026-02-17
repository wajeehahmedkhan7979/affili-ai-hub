import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import uuid
from datetime import datetime, timedelta

from app.main import app
from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.tenant import Tenant
from app.models.security import LoginHistory, RiskProfile
from app.services.auth_service import get_password_hash
from app.core.time import utcnow

@pytest.fixture
def test_user(db_session: Session):
    # Setup tenant and user
    tenant_id = uuid.uuid4()
    tenant = Tenant(id=tenant_id, name="Security Test Tenant")
    db_session.add(tenant)
    db_session.flush()

    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        tenant_id=tenant_id,
        email="security_test@example.com",
        hashed_password=get_password_hash("password123"),
        role=UserRole.OPERATOR.value,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    return user

def test_login_behavioral_success_and_logging(db_session: Session, test_user: User, client: TestClient):
    """Test that a normal login works and creates history."""
    payload = {
        "email": test_user.email,
        "password": "password123",
        "tenant_id": str(test_user.tenant_id)
    }
    
    # First login - New IP/Device penalty (20+20=40)
    headers = {"User-Agent": "TestBrowser/1.0"}
    response = client.post("/api/v1/auth/login", json=payload, headers=headers)
    
    assert response.status_code == 200
    
    # Verify history entry
    history = db_session.query(LoginHistory).filter(LoginHistory.user_id == test_user.id).first()
    assert history is not None
    assert history.status == "SUCCESS"
    assert history.risk_score >= 40.0 # New IP (testclient uses 127.0.0.1) + New Device
    assert history.user_agent == "TestBrowser/1.0"

    # Verify risk profile created
    profile = db_session.query(RiskProfile).filter(RiskProfile.user_id == test_user.id).first()
    assert profile is not None
    assert len(profile.known_ips) == 1
    assert len(profile.known_devices) == 1

def test_login_risk_escalation_on_failure(db_session: Session, test_user: User, client: TestClient):
    """Test that multiple failed logins increase risk score."""
    payload = {
        "email": test_user.email,
        "password": "wrong_password",
        "tenant_id": str(test_user.tenant_id)
    }
    
    headers = {"User-Agent": "AttackerBot/1.0"}
    
    # 5 Failed attempts
    for _ in range(5):
        client.post("/api/v1/auth/login", json=payload, headers=headers)
    
    # Verify risk score for user
    from app.services import security_service as sec_svc
    assessment = sec_svc.evaluate_login_risk(db_session, test_user, "127.0.0.1", "AttackerBot/1.0")
    
    # New IP(20) + New Device(20) + 5 Failures(50) = 90 (Blocked)
    assert assessment["risk_score"] >= 80.0
    assert assessment["allowed"] is False
    assert "Recent Failures" in assessment["reason"]

def test_login_blocked_on_high_risk(db_session: Session, test_user: User, client: TestClient):
    """Test that high risk login is blocked before password check."""
    # 1. Manually spike risk in history
    for _ in range(10):
        history = LoginHistory(
            tenant_id=test_user.tenant_id,
            user_id=test_user.id,
            email=test_user.email,
            ip_address="1.2.3.4",
            user_agent="EvilBot",
            status="FAILED",
            risk_score=90.0,
            created_at=utcnow()
        )
        db_session.add(history)
    db_session.commit()
    
    # 2. Try valid login from same "evil" environment
    payload = {
        "email": test_user.email,
        "password": "password123", # CORRECT PASSWORD
        "tenant_id": str(test_user.tenant_id)
    }
    headers = {"User-Agent": "EvilBot"}
    
    # Override client IP proxy if possible, or just let testclient do its thing
    # In reality, the IP is captured from request.client.host
    
    response = client.post("/api/v1/auth/login", json=payload, headers=headers)
    
    # Should be BLOCKED with 403 Forbidden
    assert response.status_code == 403
    assert "Access restricted due to high risk score" in response.json()["detail"]

def test_progressive_backoff_applied(db_session: Session, client: TestClient):
    """Test that medium risk scores trigger delays."""
    from app.services import security_service as sec_svc
    from app.services.auth_service import get_password_hash
    
    # Setup unique user for this test to avoid risk pollution from other tests
    tenant_id = uuid.uuid4()
    tenant = Tenant(id=tenant_id, name="Backoff Test Tenant")
    db_session.add(tenant)
    db_session.flush()

    user = User(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        email="backoff_test@example.com",
        hashed_password=get_password_hash("password123"),
        role=UserRole.OPERATOR.value,
        is_active=True
    )
    db_session.add(user)
    db_session.flush()
    
    # Setup profile with some baseline risk and TRUSTED environment
    # to avoid the +40 novelty penalty
    from app.services.security_service import get_device_fingerprint
    TEST_UA = "BackoffTestBot/1.0"
    ua_hash = get_device_fingerprint(TEST_UA)
    
    profile = RiskProfile(
        user_id=user.id,
        baseline_risk_score=60.0, # Medium Risk
        known_ips=["testclient"],
        known_devices=[ua_hash] 
    )
    db_session.add(profile)
    db_session.commit()
    
    payload = {
        "email": user.email,
        "password": "password123",
        "tenant_id": str(user.tenant_id)
    }
    
    import time
    start_time = time.time()
    response = client.post("/api/v1/auth/login", json=payload, headers={"User-Agent": TEST_UA})
    end_time = time.time()
    
    duration = end_time - start_time
    # Score 60 -> (60-50)/10 = 1.0 second delay
    # We allow some jitter, so maybe >= 0.9
    assert duration >= 0.9
    assert response.status_code == 200
