"""
Layer 2: Retry Ceiling Enforcement Tests

These tests prove the system prevents infinite retries.
"""

"""
Layer 2: Retry Ceiling Tests

These tests assert that tasks cannot be retried more than the configured ceiling.

# NOTE: v1.1 schema intentionally does NOT include `program_id` on tasks.
# Tests must not assume program-level task binding. Do not add `program_id`.
"""
import pytest
import uuid
from sqlalchemy.orm import Session
from app.services.task_dispatcher import retry_task
from app.core.tenant import set_tenant_id
from app.models.task import Task, TaskStatus, TaskType
from app.models.tenant import Tenant


@pytest.fixture
def test_tenant_id():
    """Fixture for test tenant UUID"""
    return uuid.uuid4()


def setup_test_tenant(db_session: Session, tenant_id: uuid.UUID) -> Tenant:
    """Helper to create test tenant."""
    tenant = Tenant(id=tenant_id, name="Test Tenant", is_active=True)
    db_session.add(tenant)
    db_session.commit()
    return tenant


class TestRetryCeilingEnforcement:
    """Layer 2: Retry ceiling enforcement tests"""
    
    def test_retry_ceiling_enforced(
        self, db_session: Session, test_tenant_id: uuid.UUID, insert_task
    ):
        """
        TC-6.1: Force task failure 3 times → fourth attempt blocked
        
        This test verifies that tasks cannot be retried more than the ceiling.
        """
        # Setup
        tenant = setup_test_tenant(db_session, test_tenant_id)
        set_tenant_id(str(test_tenant_id))
        
        # Create task at retry ceiling (insert via raw SQL to avoid model/DB mismatch)
        task_id = insert_task(
            id=uuid.uuid4(),
            tenant_id=test_tenant_id,
            task_type="APPLY_PROGRAM",
            status="FAILED",
            retry_count=3,
            max_retries=3,
            payload={"program_name": "Test Program"},
            agent_pool="default"
        )
        
        # Action: Attempt retry
        result = retry_task(db_session, task_id)
        
        # Assert: Retry blocked
        assert result is None, \
            "Task at retry ceiling should not be retried"
        
        from sqlalchemy.orm import load_only
        task = db_session.query(Task).options(
            load_only(
                Task.id, Task.tenant_id, Task.task_type, Task.status, Task.payload,
                Task.result, Task.agent_id, Task.agent_pool, Task.retry_count,
                Task.max_retries, Task.logs, Task.screenshot_url, Task.error_message,
                Task.created_at, Task.updated_at, Task.claimed_at, Task.started_at,
                Task.completed_at, Task.last_heartbeat
            )
        ).filter(Task.id == task_id).first()
        assert task is not None
        assert task.status == TaskStatus.FAILED, "Task should remain FAILED"
        assert task.retry_count == 3, "Retry count should not be incremented"
    
    def test_retry_allowed_before_ceiling(
        self, db_session: Session, test_tenant_id: uuid.UUID, insert_task
    ):
        """
        TC-6.2: Task with retry_count < max_retries → retry allowed
        
        This test verifies that retries are allowed before reaching the ceiling.
        """
        # Setup
        tenant = setup_test_tenant(db_session, test_tenant_id)
        set_tenant_id(str(test_tenant_id))
        
        # Create task below retry ceiling
        task_id = insert_task(
            id=uuid.uuid4(),
            tenant_id=test_tenant_id,
            task_type="APPLY_PROGRAM",
            status="FAILED",
            retry_count=1,
            max_retries=3,
            payload={"program_name": "Test Program"},
            agent_pool="default"
        )
        
        # Action: Retry task
        result = retry_task(db_session, task_id)
        
        # Assert: Retry allowed
        assert result is not None, \
            "Task below retry ceiling should be retried"
        
        from sqlalchemy.orm import load_only
        task = db_session.query(Task).options(
            load_only(
                Task.id, Task.tenant_id, Task.task_type, Task.status, Task.payload,
                Task.result, Task.agent_id, Task.agent_pool, Task.retry_count,
                Task.max_retries, Task.logs, Task.screenshot_url, Task.error_message,
                Task.created_at, Task.updated_at, Task.claimed_at, Task.started_at,
                Task.completed_at, Task.last_heartbeat
            )
        ).filter(Task.id == task_id).first()
        assert task is not None
        assert task.status == TaskStatus.PENDING, "Task should be reset to PENDING for retry"
        assert task.retry_count == 2, f"Retry count should be incremented to 2, got {task.retry_count}"
        assert task.agent_id is None, "Agent ID should be cleared for retry"
    
    def test_retry_ceiling_hard_limit(
        self, db_session: Session, test_tenant_id: uuid.UUID, insert_task
    ):
        """
        TC-6.3: Hard ceiling of 3 retries enforced even if max_retries > 3
        
        This test verifies that the hard ceiling (min(max_retries, 3)) is enforced.
        """
        # Setup
        tenant = setup_test_tenant(db_session, test_tenant_id)
        set_tenant_id(str(test_tenant_id))
        
        # Create task with max_retries=5 but retry_count=3
        # Hard ceiling should be min(5, 3) = 3
        task_id = insert_task(
            id=uuid.uuid4(),
            tenant_id=test_tenant_id,
            task_type="APPLY_PROGRAM",
            status="FAILED",
            retry_count=3,
            max_retries=5,  # Higher than hard ceiling
            payload={"program_name": "Test Program"},
            agent_pool="default"
        )
        
        # Action: Attempt retry
        result = retry_task(db_session, task_id)
        
        # Assert: Retry blocked (hard ceiling is 3)
        assert result is None, \
            "Task should not be retried even if max_retries > 3 (hard ceiling is 3)"
        
        from sqlalchemy.orm import load_only
        task = db_session.query(Task).options(
            load_only(
                Task.id, Task.tenant_id, Task.task_type, Task.status, Task.payload,
                Task.result, Task.agent_id, Task.agent_pool, Task.retry_count,
                Task.max_retries, Task.logs, Task.screenshot_url, Task.error_message,
                Task.created_at, Task.updated_at, Task.claimed_at, Task.started_at,
                Task.completed_at, Task.last_heartbeat
            )
        ).filter(Task.id == task_id).first()
        assert task is not None
        assert task.status == TaskStatus.FAILED, "Task should remain FAILED"
    
    def test_retry_resets_task_state(
        self, db_session: Session, test_tenant_id: uuid.UUID, insert_task
    ):
        """
        TC-6.4: Retry resets task state correctly
        
        This test verifies that retrying a task resets all necessary fields.
        """
        # Setup
        tenant = setup_test_tenant(db_session, test_tenant_id)
        set_tenant_id(str(test_tenant_id))
        
        # Create failed task with agent assigned
        task_id = insert_task(
            id=uuid.uuid4(),
            tenant_id=test_tenant_id,
            task_type="APPLY_PROGRAM",
            status="FAILED",
            retry_count=1,
            max_retries=3,
            agent_id="previous-agent",
            error_message="Previous error",
            payload={"program_name": "Test Program"},
            agent_pool="default"
        )
        
        # Action: Retry task
        result = retry_task(db_session, task_id)
        
        # Assert: Task state reset
        assert result is not None, \
            "Task should be retried"
        
        from sqlalchemy.orm import load_only
        task = db_session.query(Task).options(
            load_only(
                Task.id, Task.tenant_id, Task.task_type, Task.status, Task.payload,
                Task.result, Task.agent_id, Task.agent_pool, Task.retry_count,
                Task.max_retries, Task.logs, Task.screenshot_url, Task.error_message,
                Task.created_at, Task.updated_at, Task.claimed_at, Task.started_at,
                Task.completed_at, Task.last_heartbeat
            )
        ).filter(Task.id == task_id).first()
        assert task is not None
        assert task.status == TaskStatus.PENDING, "Task should be reset to PENDING"
        assert task.agent_id is None, "Agent ID should be cleared"
        assert task.error_message is None, "Error message should be cleared"
        assert task.retry_count == 2, "Retry count should be incremented"
