import pytest
import uuid
from sqlalchemy.orm import Session
from app.models.task import Task, TaskStatus, TaskType
from app.services.task_dispatcher import find_and_claim_task, create_task
from app.core.tenant import get_tenant_id

from app.models.tenant import Tenant

def test_find_and_claim_task_simple(db_session: Session):
    """Test basic claiming logic."""
    # Create a tenant
    tenant = Tenant(name="Test Tenant", is_active=True)
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)
    
    # Set context
    from app.core.tenant import set_tenant_id
    set_tenant_id(str(tenant.id))
    
    # Create a task
    task = create_task(db_session, TaskType.DISCOVER_PROGRAM, {"test": "data"}, agent_pool="test_pool")
    db_session.commit()
    
    # Claim it
    claimed_task = find_and_claim_task(db_session, "agent_1", agent_pool="test_pool")
    
    assert claimed_task is not None
    assert claimed_task.id == task.id
    assert claimed_task.status == TaskStatus.CLAIMED
    assert claimed_task.agent_id == "agent_1"
    assert claimed_task.agent_pool == "test_pool"

def test_find_and_claim_task_pool_isolation(db_session: Session):
    """Test that agents don't claim from other pools."""
    # Create a tenant
    tenant = Tenant(name="Test Tenant", is_active=True)
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)
    
    # Set context
    from app.core.tenant import set_tenant_id
    set_tenant_id(str(tenant.id))
    
    # Create two tasks in different pools
    task_pool_a = create_task(db_session, TaskType.DISCOVER_PROGRAM, {"pool": "A"}, agent_pool="pool_a")
    task_pool_b = create_task(db_session, TaskType.DISCOVER_PROGRAM, {"pool": "B"}, agent_pool="pool_b")
    db_session.commit()
    
    # Agent from pool A should only find task A
    claimed_a = find_and_claim_task(db_session, "agent_a", agent_pool="pool_a")
    assert claimed_a is not None
    assert claimed_a.id == task_pool_a.id
    
    # Agent from pool B should only find task B
    claimed_b = find_and_claim_task(db_session, "agent_b", agent_pool="pool_b")
    assert claimed_b is not None
    assert claimed_b.id == task_pool_b.id

def test_find_and_claim_task_none_available(db_session: Session):
    """Test return None when no tasks available."""
    # Create a tenant
    tenant = Tenant(name="Test Tenant", is_active=True)
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)
    
    # Set context
    from app.core.tenant import set_tenant_id
    set_tenant_id(str(tenant.id))
    
    claimed = find_and_claim_task(db_session, "agent_1", agent_pool="empty_pool")
    assert claimed is None

def test_claim_next_api(client, db_session):
    """Test the /claim-next API endpoint."""
    # Create a tenant
    tenant = Tenant(name="Test Tenant", is_active=True)
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)
    
    # No token provided - should be 401
    response = client.post(
        "/api/v1/tasks/claim-next", 
        json={"agent_id": "test_agent"},
        headers={"X-Tenant-ID": str(tenant.id)}
    )
    assert response.status_code == 401
