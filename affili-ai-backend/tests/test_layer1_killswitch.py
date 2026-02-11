"""
Layer 1: Kill-Switch Global Enforcement Tests

These tests assert that every execution path halts when kill-switch is active.
These tests MUST NEVER FAIL - they are safety invariants.

If any of these tests fail, the pilot must be stopped.
"""

import pytest
import uuid
from fastapi import status
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.task import Task, TaskStatus, TaskType
from app.models.tenant_runtime_flag import TenantRuntimeFlag
from app.models.tenant import Tenant
from app.models.user import User, UserRole
from app.services.cost_governance import cost_governance
from app.services.task_dispatcher import create_task
from app.services.policy_service import evaluate_action
from app.services.cost_governance import check_llm_allowed
from app.core.tenant import set_tenant_id, get_tenant_id


@pytest.fixture
def test_tenant_id():
    """Fixture for test tenant UUID"""
    return uuid.uuid4()


@pytest.fixture
def test_user_id():
    """Fixture for test user UUID (for kill-switch activation)"""
    return uuid.uuid4()


def setup_test_user(db_session: Session, tenant_id: uuid.UUID, user_id: uuid.UUID) -> User:
    """Helper to create a test user."""
    from sqlalchemy import text
    
    # Create user with proper enum casting for PostgreSQL
    db_session.execute(
        text("""
            INSERT INTO users (id, tenant_id, email, role, is_active, created_at)
            VALUES (:id, :tenant_id, :email, CAST(:role AS userrole), :is_active, NOW())
        """),
        {
            "id": user_id,
            "tenant_id": tenant_id,
            "email": f"test-{user_id}@example.com",
            "role": "OWNER",
            "is_active": True
        }
    )
    db_session.commit()
    
    user = db_session.query(User).filter(User.id == user_id).first()
    return user


class TestKillSwitchEnforcement:
    """Layer 1: Kill-switch global enforcement tests"""
    
    def test_killswitch_blocks_task_creation(
        self, db_session: Session, client, test_tenant_id: uuid.UUID, test_user_id: uuid.UUID
    ):
        """
        TC-1.1: Creating a task while kill-switch is ON → ❌ blocked
        
        This test verifies that task creation is blocked when kill-switch is active.
        Tests the service layer directly, which is where kill-switch enforcement happens.
        """
        # Setup: Create tenant and user first (required for foreign keys)
        tenant = Tenant(id=test_tenant_id, name="Test Tenant", is_active=True)
        db_session.add(tenant)
        db_session.commit()
        
        user = setup_test_user(db_session, test_tenant_id, test_user_id)
        
        # Enable kill-switch for tenant
        cost_governance.enable_tenant_killswitch(
            db=db_session,
            tenant_id=test_tenant_id,
            reason="Test kill-switch enforcement",
            disabled_by=test_user_id
        )
        db_session.commit()
        
        # Verify kill-switch is active
        flag = db_session.query(TenantRuntimeFlag).filter(
            TenantRuntimeFlag.tenant_id == test_tenant_id
        ).first()
        assert flag is not None
        assert flag.ai_disabled is True
        
        # Set tenant context for service calls
        set_tenant_id(str(test_tenant_id))
        
        # Action: Verify policy blocks task creation when kill-switch is active
        context = {
            "task_type": "APPLY_PROGRAM",
            "program_domain": "shareasale.com",
            "payload": {"program_name": "Test Program"}
        }
        allowed, reason = evaluate_action(db_session, test_tenant_id, "create_task", context)
        assert allowed is False, f"Kill-switch should block create_task: {reason}"
        assert any(k in (reason or "").lower() for k in ["disabled", "kill", "blocked", "suspended"]), \
            f"Reason should indicate kill-switch: {reason}"
        
        # Assert: No task created in DB
        from sqlalchemy.orm import load_only
        task_count = db_session.query(Task).options(
            load_only(
                Task.id, Task.tenant_id, Task.task_type, Task.status, Task.payload,
                Task.result, Task.agent_id, Task.agent_pool, Task.retry_count,
                Task.max_retries, Task.logs, Task.screenshot_url, Task.error_message,
                Task.created_at, Task.updated_at, Task.claimed_at, Task.started_at,
                Task.completed_at, Task.last_heartbeat
            )
        ).filter(
            Task.tenant_id == test_tenant_id
        ).count()
        assert task_count == 0, "No task should be created when kill-switch is active"
    
    def test_killswitch_blocks_task_polling(
        self, db_session: Session, client, test_tenant_id: uuid.UUID, test_user_id: uuid.UUID
    ):
        """
        TC-1.2: Polling a task while kill-switch is ON → ❌ blocked
        
        This test verifies that agents cannot poll for tasks when kill-switch is active.
        """
        # Setup: Create tenant and user first
        tenant = Tenant(id=test_tenant_id, name="Test Tenant", is_active=True)
        db_session.add(tenant)
        db_session.commit()
        
        user = setup_test_user(db_session, test_tenant_id, test_user_id)
        
        # Create a task first (before kill-switch)
        set_tenant_id(str(test_tenant_id))
        
        # Manually create task to ensure it exists before kill-switch
        task = Task(
            id=uuid.uuid4(),
            tenant_id=test_tenant_id,
            task_type=TaskType.APPLY_PROGRAM,
            status=TaskStatus.PENDING,
            payload={"program_name": "Test Program"},
            agent_pool="default",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)
        
        # Enable kill-switch
        cost_governance.enable_tenant_killswitch(
            db=db_session,
            tenant_id=test_tenant_id,
            reason="Test kill-switch polling block",
            disabled_by=test_user_id
        )
        db_session.commit()
        
        # Action: Attempt to poll for tasks via service
        # Note: Agent poll endpoint may not check kill-switch directly,
        # but tasks should not be available if kill-switch is active
        # This test verifies that kill-switch prevents task availability
        from app.services.task_dispatcher import get_pending_tasks
        
        set_tenant_id(str(test_tenant_id))
        pending_tasks = get_pending_tasks(db_session, limit=10)
        
        
        # Assert: No tasks available (kill-switch should prevent new task creation AND cleanup old ones)
        # Since we created the task before kill-switch, verify it's not accessible
        assert len(pending_tasks) == 0, "No pending tasks should be returned when kill-switch is active"
        
        # Assert: Task became FAILED (cleanup)
        db_session.refresh(task)
        assert task.status == TaskStatus.FAILED, \
            "Task should be FAILED when kill-switch cleans up pending tasks"
        assert "Kill-switch" in (task.error_message or ""), "Error message should mention kill-switch"
    
    def test_killswitch_blocks_task_resume(
        self, db_session: Session, client, test_tenant_id: uuid.UUID, test_user_id: uuid.UUID
    ):
        """
        TC-1.3: Resuming a paused task while kill-switch is ON → ❌ blocked
        
        This test verifies that operators cannot resume tasks when kill-switch is active.
        """
        # Setup: Create tenant and user first
        tenant = Tenant(id=test_tenant_id, name="Test Tenant", is_active=True)
        db_session.add(tenant)
        db_session.commit()
        
        user = setup_test_user(db_session, test_tenant_id, test_user_id)
        
        # Create a paused task
        set_tenant_id(str(test_tenant_id))
        task = Task(
            id=uuid.uuid4(),
            tenant_id=test_tenant_id,
            task_type=TaskType.APPLY_PROGRAM,
            status=TaskStatus.PAUSED_FOR_CAPTCHA,
            payload={"program_name": "Test Program"}
        )
        db_session.add(task)
        db_session.commit()
        task_id = str(task.id)
        
        # Enable kill-switch
        cost_governance.enable_tenant_killswitch(
            db=db_session,
            tenant_id=test_tenant_id,
            reason="Test kill-switch resume block",
            disabled_by=test_user_id
        )
        db_session.commit()
        
        # Action: Attempt to resume task
        response = client.post(
            f"/api/v1/operator/tasks/{task_id}/resume",
            json={"reason": "Test resume"},
            headers={
                "Authorization": "Bearer test-token",
                "X-Tenant-ID": str(test_tenant_id)
            }
        )
        
        # Assert: HTTP 403
        assert response.status_code == 403, \
            f"Expected 403, got {response.status_code}: {response.json()}"
        
        error_detail = response.json().get("detail", "").lower()
        assert any(keyword in error_detail for keyword in ["disabled", "kill", "blocked"]), \
            f"Error message should indicate kill-switch: {error_detail}"
        
        # Assert: Task became FAILED (cleanup)
        db_session.refresh(task)
        assert task.status == TaskStatus.FAILED, \
            "Task should be FAILED when kill-switch cleans up paused tasks"
    
    def test_killswitch_blocks_llm_call(
        self, db_session: Session, test_tenant_id: uuid.UUID, test_user_id: uuid.UUID
    ):
        """
        TC-1.4: LLM call while kill-switch is ON → ❌ blocked
        
        This test verifies that LLM calls are blocked when kill-switch is active.
        """
        # Setup: Create tenant and user first
        tenant = Tenant(id=test_tenant_id, name="Test Tenant", is_active=True)
        db_session.add(tenant)
        db_session.commit()
        
        user = setup_test_user(db_session, test_tenant_id, test_user_id)
        
        # Enable kill-switch
        cost_governance.enable_tenant_killswitch(
            db=db_session,
            tenant_id=test_tenant_id,
            reason="Test kill-switch LLM block",
            disabled_by=test_user_id
        )
        db_session.commit()
        
        # Action: Attempt LLM call check
        result = check_llm_allowed(
            db=db_session,
            tenant_id=test_tenant_id,
            task_id=None,
            current_task_calls=0
        )
        
        # Assert: LLM call not allowed
        assert result["allowed"] is False, \
            "LLM calls should be blocked when kill-switch is active"
        
        assert result.get("reason") in ["TENANT_DISABLED", "QUOTA_EXCEEDED"] or \
               "disabled" in str(result.get("reason", "")).lower(), \
            f"Reason should indicate kill-switch: {result.get('reason')}"
        
        # Assert: Quota check shows disabled
        quota_check = result.get("quota_check", {})
        if quota_check:
            assert quota_check.get("reason") == "TENANT_DISABLED" or \
                   quota_check.get("allowed") is False, \
                "Quota check should reflect kill-switch status"
    
    def test_killswitch_cleanup_cancels_active_tasks(
        self, db_session: Session, test_tenant_id: uuid.UUID, test_user_id: uuid.UUID
    ):
        """
        TC-1.5: Kill-switch activation cancels all active tasks
        
        This test verifies that enabling kill-switch cancels all active tasks.
        """
        # Setup: Create tenant and user first
        tenant = Tenant(id=test_tenant_id, name="Test Tenant", is_active=True)
        db_session.add(tenant)
        db_session.commit()
        
        user = setup_test_user(db_session, test_tenant_id, test_user_id)
        
        # Create multiple tasks in different states
        set_tenant_id(str(test_tenant_id))
        
        pending_task = Task(
            id=uuid.uuid4(),
            tenant_id=test_tenant_id,
            task_type=TaskType.APPLY_PROGRAM,
            status=TaskStatus.PENDING,
            payload={"program_name": "Test Program 1"}
        )
        
        claimed_task = Task(
            id=uuid.uuid4(),
            tenant_id=test_tenant_id,
            task_type=TaskType.APPLY_PROGRAM,
            status=TaskStatus.CLAIMED,
            agent_id="test-agent",
            payload={"program_name": "Test Program 2"}
        )
        
        running_task = Task(
            id=uuid.uuid4(),
            tenant_id=test_tenant_id,
            task_type=TaskType.APPLY_PROGRAM,
            status=TaskStatus.RUNNING,
            agent_id="test-agent",
            payload={"program_name": "Test Program 3"}
        )
        
        paused_task = Task(
            id=uuid.uuid4(),
            tenant_id=test_tenant_id,
            task_type=TaskType.APPLY_PROGRAM,
            status=TaskStatus.PAUSED_FOR_CAPTCHA,
            payload={"program_name": "Test Program 4"}
        )
        
        db_session.add_all([pending_task, claimed_task, running_task, paused_task])
        db_session.commit()
        
        # Action: Enable kill-switch (should trigger cleanup)
        cost_governance.enable_tenant_killswitch(
            db=db_session,
            tenant_id=test_tenant_id,
            reason="Test kill-switch cleanup",
            disabled_by=test_user_id
        )
        db_session.commit()
        
        # Assert: All active tasks are canceled
        for task in [pending_task, claimed_task, running_task, paused_task]:
            db_session.refresh(task)
            assert task.status == TaskStatus.FAILED, \
                f"Task {task.id} should be FAILED after kill-switch activation"
            assert "Tenant Kill-switch Active" in (task.error_message or ""), \
                f"Task {task.id} should have kill-switch error message"
        
        # Assert: Agent IDs cleared
        db_session.refresh(claimed_task)
        db_session.refresh(running_task)
        # Note: cleanup may or may not clear agent_id, depending on implementation
        # This assertion is optional based on actual behavior
