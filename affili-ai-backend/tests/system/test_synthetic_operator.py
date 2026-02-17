import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from sqlalchemy.orm import Session
from app.services.synthetic_operator import synthetic_op
from app.models.metrics import SyntheticAudit
from fastapi.testclient import TestClient

@pytest.mark.asyncio
async def test_synthetic_operator_cycle(db_session: Session):
    """
    Test that running a certification cycle creates an audit entry.
    """
    # Mock Redis to avoid connection errors
    mock_broadcaster = AsyncMock()
    # Mock the publisher to avoid real Redis calls
    mock_broadcaster.publish = AsyncMock()
    
    with patch("app.core.redis_bus.broadcaster", mock_broadcaster):
        # 1. Run certification with injected session
        await synthetic_op.run_certification(db=db_session)
    
    # 2. Verify audit persisted
    audit = db_session.query(SyntheticAudit).order_by(SyntheticAudit.timestamp.desc()).first()
    assert audit is not None
    assert audit.status == "UP"
    assert "auth" in audit.results
    assert "task_flow" in audit.results
    assert "broadcasting" in audit.results
    assert audit.duration_ms > 0

def test_synthetic_observability_endpoint(client: TestClient, db_session: Session, auth_headers: dict):
    """
    Test that the observability endpoint returns the latest synthetic run.
    """
    # Create a mock audit entry
    import uuid
    from app.core.time import utcnow
    
    # Cleanup previous entries
    db_session.query(SyntheticAudit).delete()
    db_session.commit()
    
    mock_audit = SyntheticAudit(
        id=uuid.uuid4(),
        status="UP",
        results={"test": "pass"},
        duration_ms=100,
        timestamp=utcnow()
    )
    db_session.add(mock_audit)
    db_session.commit()
    
    # Call API
    resp = client.get("/api/v1/observability/synthetic/latest", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "UP"
    assert data["results"]["test"] == "pass"
