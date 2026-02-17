"""
Layer 2: Agent Kill-Switch Reaction Tests

These tests prove agents stop cleanly when governance intervenes.

# NOTE: v1.1 schema intentionally does NOT include `program_id` on tasks.
# Tests must not assume program-level task binding. Do not add `program_id`.
"""

import pytest
import uuid
from sqlalchemy.orm import Session
from app.models.task import Task, TaskStatus, TaskType
from app.models.tenant import Tenant
from app.models.user import User, UserRole
from app.services.cost_governance import cost_governance
from app.core.tenant import set_tenant_id


@pytest.fixture
def test_tenant_id():
    """Fixture for test tenant UUID"""
    return uuid.uuid4()


@pytest.fixture
def test_user_id():
    """Fixture for test user UUID"""
    return uuid.uuid4()


def setup_test_tenant_and_user(db_session: Session, tenant_id: uuid.UUID, user_id: uuid.UUID) -> tuple[Tenant, User]:
    """Helper to create test tenant and user."""
    from sqlalchemy import text
    
    tenant = Tenant(id=tenant_id, name="Test Tenant", is_active=True)
    db_session.add(tenant)
    db_session.commit()
    
    # Create user with proper enum casting for PostgreSQL
    db_session.execute(
        text("""
            INSERT INTO users (id, tenant_id, email, role, is_active, created_at)
            VALUES (:id, :tenant_id, :email, CAST(:role AS userrole), :is_active, NOW())
        """),
        {
            "id": user_id,
            "tenant_id": tenant_id,
            "email": f"test-{tenant_id}@example.com",
            "role": "OWNER",
            "is_active": True
        }
    )
    db_session.commit()
    
    user = db_session.query(User).filter(User.id == user_id).first()
    return tenant, user


class TestAgentKillSwitchReaction:
    """Layer 2: Agent kill-switch reaction tests"""
    
    def test_active_task_canceled_on_killswitch(
        self, db_session: Session, test_tenant_id: uuid.UUID, test_user_id: uuid.UUID
    ):
        """
        TC-7.1: Kill-switch activated → active task auto-canceled
        
        This test verifies that enabling kill-switch cancels all active tasks.
        """
        # Setup
        tenant, user = setup_test_tenant_and_user(db_session, test_tenant_id, test_user_id)
        set_tenant_id(str(test_tenant_id))
        
        # Create active tasks in various states
        running_task = Task(
            id=uuid.uuid4(),
            tenant_id=test_tenant_id,
            task_type=TaskType.APPLY_PROGRAM,
            status=TaskStatus.RUNNING,
            agent_id="test-agent",
            payload={"program_name": "Running Task"}
        )
        
        claimed_task = Task(
            id=uuid.uuid4(),
            tenant_id=test_tenant_id,
            task_type=TaskType.APPLY_PROGRAM,
            status=TaskStatus.CLAIMED,
            agent_id="test-agent",
            payload={"program_name": "Claimed Task"}
        )
        
        paused_task = Task(
            id=uuid.uuid4(),
            tenant_id=test_tenant_id,
            task_type=TaskType.APPLY_PROGRAM,
            status=TaskStatus.PAUSED_FOR_CAPTCHA,
            agent_id="test-agent",
            payload={"program_name": "Paused Task"}
        )
        
        db_session.add_all([running_task, claimed_task, paused_task])
        db_session.commit()
        
        # Action: Enable kill-switch (should trigger cleanup)
        cost_governance.enable_tenant_killswitch(
            db=db_session,
            tenant_id=test_tenant_id,
            reason="Test kill-switch cleanup",
            disabled_by=test_user_id
        )
        db_session.commit()
        
        # Assert: All active tasks canceled
        for task in [running_task, claimed_task, paused_task]:
            db_session.refresh(task)
            assert task.status == TaskStatus.FAILED, \
                f"Task {task.id} should be FAILED after kill-switch"
            
            assert "Tenant Kill-switch Active" in (task.error_message or ""), \
                f"Task {task.id} should have kill-switch error message"
            
            assert "kill-switch" in (task.logs or "").lower() or \
                   "canceled" in (task.logs or "").lower(), \
                f"Task {task.id} logs should indicate kill-switch cancellation"
    
    def test_pending_task_canceled_on_killswitch(
        self, db_session: Session, test_tenant_id: uuid.UUID, test_user_id: uuid.UUID
    ):
        """
        TC-7.2: PENDING tasks are also canceled on kill-switch
        
        This test verifies that PENDING tasks are included in cleanup.
        """
        # Setup
        tenant, user = setup_test_tenant_and_user(db_session, test_tenant_id, test_user_id)
        set_tenant_id(str(test_tenant_id))
        
        # Create pending task
        pending_task = Task(
            id=uuid.uuid4(),
            tenant_id=test_tenant_id,
            task_type=TaskType.APPLY_PROGRAM,
            status=TaskStatus.PENDING,
            payload={"program_name": "Pending Task"}
        )
        db_session.add(pending_task)
        db_session.commit()
        
        # Action: Enable kill-switch
        cost_governance.enable_tenant_killswitch(
            db=db_session,
            tenant_id=test_tenant_id,
            reason="Test kill-switch",
            disabled_by=test_user_id
        )
        db_session.commit()
        
        # Assert: PENDING task canceled
        db_session.refresh(pending_task)
        assert pending_task.status == TaskStatus.FAILED, \
            "PENDING task should be canceled on kill-switch"
    
    def test_completed_task_not_affected_by_killswitch(
        self, db_session: Session, test_tenant_id: uuid.UUID, test_user_id: uuid.UUID
    ):
        """
        TC-7.3: COMPLETED tasks are not affected by kill-switch
        
        This test verifies that completed tasks remain unchanged.
        """
        # Setup
        tenant, user = setup_test_tenant_and_user(db_session, test_tenant_id, test_user_id)
        set_tenant_id(str(test_tenant_id))
        
        # Create completed task
        completed_task = Task(
            id=uuid.uuid4(),
            tenant_id=test_tenant_id,
            task_type=TaskType.APPLY_PROGRAM,
            status=TaskStatus.COMPLETED,
            payload={"program_name": "Completed Task"}
        )
        db_session.add(completed_task)
        db_session.commit()
        original_status = completed_task.status
        
        # Action: Enable kill-switch
        cost_governance.enable_tenant_killswitch(
            db=db_session,
            tenant_id=test_tenant_id,
            reason="Test kill-switch",
            disabled_by=test_user_id
        )
        db_session.commit()
        
        # Assert: Completed task unchanged
        db_session.refresh(completed_task)
        assert completed_task.status == TaskStatus.COMPLETED, \
            "COMPLETED task should not be affected by kill-switch"
        
        assert completed_task.status == original_status, \
            "Task status should remain unchanged"
    
    def test_killswitch_cleanup_logs_reason(
        self, db_session: Session, test_tenant_id: uuid.UUID, test_user_id: uuid.UUID
    ):
        """
        TC-7.4: Kill-switch cleanup logs reason in task logs
        
        This test verifies that cleanup operations are logged.
        """
        # Setup
        tenant, user = setup_test_tenant_and_user(db_session, test_tenant_id, test_user_id)
        set_tenant_id(str(test_tenant_id))
        
        # Create active task
        active_task = Task(
            id=uuid.uuid4(),
            tenant_id=test_tenant_id,
            task_type=TaskType.APPLY_PROGRAM,
            status=TaskStatus.RUNNING,
            agent_id="test-agent",
            payload={"program_name": "Active Task"}
        )
        db_session.add(active_task)
        db_session.commit()
        
        killswitch_reason = "Emergency shutdown for testing"
        
        # Action: Enable kill-switch with specific reason
        cost_governance.enable_tenant_killswitch(
            db=db_session,
            tenant_id=test_tenant_id,
            reason=killswitch_reason,
            disabled_by=test_user_id
        )
        db_session.commit()
        
        # Assert: Reason logged in task
        db_session.refresh(active_task)
        assert killswitch_reason in (active_task.error_message or ""), \
            "Kill-switch reason should be in error message"
        
        assert "kill-switch" in (active_task.logs or "").lower() or \
               "canceled" in (active_task.logs or "").lower(), \
            "Task logs should indicate kill-switch cancellation"
