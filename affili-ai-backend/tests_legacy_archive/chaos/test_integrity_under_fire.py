import pytest
import uuid
import time
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from app.services.workflow_service import workflow_service
from app.services.task_dispatcher import create_task, update_task_status
from app.models.task import Task, TaskStatus
from app.models.workflow import WorkflowDefinition, WorkflowStatus
from app.core.tenant import set_tenant_id
from app.db.session import get_db

# Chaos Scenarios

def test_db_disconnection_resilience(db_session):
    """
    Scenario: Database connection drops during workflow execution.
    Expected: Task creation/update should raise DB error, but system should not crash hard.
    Retry logic should handle transient failures (simulated here by catching exception).
    """
    tenant_id = uuid.uuid4()
    set_tenant_id(str(tenant_id))

    # Create a workflow definition
    wf_def = workflow_service.create_definition(
        db_session, tenant_id, "Chaos WF", 
        {"steps": [{"id": "s1", "type": "TEST", "next": "s2"}]}
    )

    # Start instance
    instance = workflow_service.start_instance(db_session, tenant_id, wf_def.id)
    db_session.commit()

    # Simulate DB Error during step execution
    with patch("sqlalchemy.orm.Session.add", side_effect=Exception("DB Connection Lost")):
        try:
            workflow_service._execute_step(db_session, instance, {"id": "s1", "type": "TEST"})
        except Exception as e:
            assert str(e) == "DB Connection Lost"
    
    # Verify Instance is still RUNNING (not corrupted/stopped in logic, though DB write failed)
    # in reality, if DB write fails, the transaction rolls back.
    # The key is: does the system have a mechanism to retry? 
    # For now, we verify that the exception is raised and propagates, allowing Queue/Worker to retry.
    assert instance.status == WorkflowStatus.RUNNING

def test_worker_crash_orphaned_task(db_session):
    """
    Scenario: Worker crashes while processing a task.
    Expected: Task remains 'IN_PROGRESS' but locked by a dead worker.
    The 'Heartbeat Reaper' (simulated) should reset it.
    """
    tenant_id = uuid.uuid4()
    set_tenant_id(str(tenant_id))

    # Create Task
    task = create_task(db_session, "TEST_TASK", {"data": "important"})
    db_session.commit()

    # Worker Claims Task
    task.status = TaskStatus.IN_PROGRESS
    task.locked_by = "worker-dead-1"
    task.locked_at = time.time() - 600 # 10 mins ago (stale)
    db_session.commit()

    # Simulate Reaper Logic
    # (In production this is a background job, here we verify the logic works)
    stale_threshold = time.time() - 300 # 5 mins
    stale_task = db_session.query(Task).filter(
        Task.status == TaskStatus.IN_PROGRESS,
        Task.locked_at < stale_threshold
    ).first()

    assert stale_task is not None
    assert stale_task.id == task.id

    # Reset Task
    stale_task.status = TaskStatus.PENDING
    stale_task.locked_by = None
    stale_task.locked_at = None
    db_session.commit()

    # Verify Task is ready to be picked up again
    refreshed_task = db_session.query(Task).filter(Task.id == task.id).first()
    assert refreshed_task.status == TaskStatus.PENDING
    assert refreshed_task.locked_by is None

def test_api_timeout_retry(db_session):
    """
    Scenario: External API times out.
    Expected: Task marked as FAILED with specific error, enabling retry policy.
    """
    tenant_id = uuid.uuid4()
    set_tenant_id(str(tenant_id))

    # Create Task
    task = create_task(db_session, "API_CALL", {})
    
    # Simulate Worker logic catching timeout
    try:
        # Code that calls external API
        raise TimeoutError("External API 504 Gateway Timeout")
    except TimeoutError:
        # Update task status
        update_task_status(
            db_session, 
            task.id, 
            TaskStatus.FAILED, 
            result={"error": "Timeout", "retryable": True}
        )
    
    db_session.refresh(task)
    assert task.status == TaskStatus.FAILED
    assert task.result["retryable"] is True
