"""
Layer 2: Stale Task Release Tests

These tests prove the system recovers from expected failures.
Hung agents do not brick the system.

# NOTE: v1.1 schema intentionally does NOT include `program_id` on tasks.
# Tests must not assume program-level task binding. Do not add `program_id`.
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session
from app.models.task import Task, TaskStatus, TaskType
from app.models.tenant import Tenant
from app.models.user import User, UserRole
from app.services.task_dispatcher import release_stale_tasks
from app.core.tenant import set_tenant_id


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


class TestStaleTaskRelease:
    """Layer 2: Stale task release tests"""
    
    def test_stale_task_released_after_timeout(
        self, db_session: Session, test_tenant_id: uuid.UUID
    ):
        """
        TC-5.1: Task enters RUNNING, no heartbeat for >5 minutes → released
        
        This test verifies that stale tasks are automatically released.
        """
        # Setup: Create tenant
        tenant = setup_test_tenant(db_session, test_tenant_id)
        set_tenant_id(str(test_tenant_id))
        
        # Create a stale task (RUNNING, started 6 minutes ago, no heartbeat)
        stale_time = datetime.utcnow() - timedelta(minutes=6)
        stale_task = Task(
            id=uuid.uuid4(),
            tenant_id=test_tenant_id,
            task_type=TaskType.APPLY_PROGRAM,
            status=TaskStatus.RUNNING,
            agent_id="hung-agent",
            started_at=stale_time,
            last_heartbeat=None,  # No heartbeat
            payload={"program_name": "Test Program"}
        )
        db_session.add(stale_task)
        db_session.commit()
        task_id = stale_task.id
        original_retry_count = stale_task.retry_count
        
        # Action: Release stale tasks (5 minute timeout)
        released_count = release_stale_tasks(db_session, timeout_seconds=300)
        
        # Assert: Task released
        assert released_count == 1, \
            f"Expected 1 stale task released, got {released_count}"
        
        db_session.refresh(stale_task)
        assert stale_task.status == TaskStatus.PENDING, \
            "Stale task should be reset to PENDING"
        
        assert stale_task.agent_id is None, \
            "Agent ID should be cleared"
        
        assert stale_task.started_at is None, \
            "Started timestamp should be cleared"
        
        assert stale_task.last_heartbeat is None, \
            "Heartbeat should be cleared"
        
        assert stale_task.retry_count == original_retry_count + 1, \
            "Retry count should be incremented"
        
        assert "timeout" in (stale_task.logs or "").lower() or \
               "released" in (stale_task.logs or "").lower(), \
            "Log should indicate task was released due to timeout"
    
    def test_stale_task_with_old_heartbeat_released(
        self, db_session: Session, test_tenant_id: uuid.UUID
    ):
        """
        TC-5.2: Task with old heartbeat (>5 minutes) → released
        
        This test verifies that tasks with old heartbeats are released.
        """
        # Setup
        tenant = setup_test_tenant(db_session, test_tenant_id)
        set_tenant_id(str(test_tenant_id))
        
        # Create task with old heartbeat
        old_heartbeat_time = datetime.utcnow() - timedelta(minutes=6)
        stale_task = Task(
            id=uuid.uuid4(),
            tenant_id=test_tenant_id,
            task_type=TaskType.APPLY_PROGRAM,
            status=TaskStatus.RUNNING,
            agent_id="hung-agent",
            started_at=datetime.utcnow() - timedelta(minutes=10),
            last_heartbeat=old_heartbeat_time,  # Old heartbeat
            payload={"program_name": "Test Program"}
        )
        db_session.add(stale_task)
        db_session.commit()
        
        # Action
        released_count = release_stale_tasks(db_session, timeout_seconds=300)
        
        # Assert
        assert released_count == 1, \
            "Task with old heartbeat should be released"
        
        db_session.refresh(stale_task)
        assert stale_task.status == TaskStatus.PENDING, \
            "Task should be reset to PENDING"
    
    def test_active_task_not_released(
        self, db_session: Session, test_tenant_id: uuid.UUID
    ):
        """
        TC-5.3: Task with recent heartbeat → not released
        
        This test verifies that active tasks are not released.
        """
        # Setup
        tenant = setup_test_tenant(db_session, test_tenant_id)
        set_tenant_id(str(test_tenant_id))
        
        # Create active task with recent heartbeat
        recent_heartbeat = datetime.utcnow() - timedelta(minutes=1)
        active_task = Task(
            id=uuid.uuid4(),
            tenant_id=test_tenant_id,
            task_type=TaskType.APPLY_PROGRAM,
            status=TaskStatus.RUNNING,
            agent_id="active-agent",
            started_at=datetime.utcnow() - timedelta(minutes=5),
            last_heartbeat=recent_heartbeat,  # Recent heartbeat
            payload={"program_name": "Test Program"}
        )
        db_session.add(active_task)
        db_session.commit()
        task_id = active_task.id
        original_agent_id = active_task.agent_id
        
        # Action
        released_count = release_stale_tasks(db_session, timeout_seconds=300)
        
        # Assert: No tasks released
        assert released_count == 0, \
            "Active task should not be released"
        
        db_session.refresh(active_task)
        assert active_task.status == TaskStatus.RUNNING, \
            "Active task should remain RUNNING"
        
        assert active_task.agent_id == original_agent_id, \
            "Agent ID should not be cleared"
    
    def test_pending_task_not_released(
        self, db_session: Session, test_tenant_id: uuid.UUID
    ):
        """
        TC-5.4: PENDING tasks are not released (only RUNNING tasks)
        
        This test verifies that only RUNNING tasks are considered for release.
        """
        # Setup
        tenant = setup_test_tenant(db_session, test_tenant_id)
        set_tenant_id(str(test_tenant_id))
        
        # Create old PENDING task
        old_time = datetime.utcnow() - timedelta(minutes=10)
        pending_task = Task(
            id=uuid.uuid4(),
            tenant_id=test_tenant_id,
            task_type=TaskType.APPLY_PROGRAM,
            status=TaskStatus.PENDING,  # Not RUNNING
            created_at=old_time,
            payload={"program_name": "Test Program"}
        )
        db_session.add(pending_task)
        db_session.commit()
        
        # Action
        released_count = release_stale_tasks(db_session, timeout_seconds=300)
        
        # Assert: No tasks released (only RUNNING tasks are checked)
        assert released_count == 0, \
            "PENDING tasks should not be released"
        
        db_session.refresh(pending_task)
        assert pending_task.status == TaskStatus.PENDING, \
            "PENDING task should remain PENDING"
    
    def test_multiple_stale_tasks_released(
        self, db_session: Session, test_tenant_id: uuid.UUID
    ):
        """
        TC-5.5: Multiple stale tasks are all released
        
        This test verifies that the release function handles multiple stale tasks.
        """
        # Setup
        tenant = setup_test_tenant(db_session, test_tenant_id)
        set_tenant_id(str(test_tenant_id))
        
        # Create multiple stale tasks
        stale_time = datetime.utcnow() - timedelta(minutes=6)
        stale_tasks = []
        for i in range(3):
            task = Task(
                id=uuid.uuid4(),
                tenant_id=test_tenant_id,
                task_type=TaskType.APPLY_PROGRAM,
                status=TaskStatus.RUNNING,
                agent_id=f"hung-agent-{i}",
                started_at=stale_time,
                last_heartbeat=None,
                payload={"program_name": f"Test Program {i}"}
            )
            stale_tasks.append(task)
            db_session.add(task)
        
        db_session.commit()
        
        # Action
        released_count = release_stale_tasks(db_session, timeout_seconds=300)
        
        # Assert: All stale tasks released
        assert released_count == 3, \
            f"Expected 3 stale tasks released, got {released_count}"
        
        for task in stale_tasks:
            db_session.refresh(task)
            assert task.status == TaskStatus.PENDING, \
                f"Task {task.id} should be reset to PENDING"
            assert task.agent_id is None, \
                f"Task {task.id} agent ID should be cleared"
