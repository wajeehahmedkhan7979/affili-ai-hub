"""
Task dispatcher service for creating and managing tasks.
"""

from sqlalchemy.orm import Session
from sqlalchemy import update, select, and_, or_
from app.models.task import Task, TaskStatus
from app.models.usage import TenantUsage
from app.schemas.task import TaskCreate
from app.core.tenant import get_tenant_id
from datetime import datetime, date
import uuid
from typing import List, Optional, Dict, Any


from fastapi import HTTPException
from app.services.billing_service import check_task_limit

def create_task(
    db: Session,
    task_type: str,
    payload: Optional[Dict[str, Any]] = None,
    agent_pool: Optional[str] = "default",
) -> Task:
    """Create a new task for an agent to process."""
    tenant_id_str = get_tenant_id()
    tenant_uuid = uuid.UUID(tenant_id_str)
    
    # Phase 9: Billing Enforcement
    if not check_task_limit(db, tenant_uuid):
        raise HTTPException(
            status_code=402, 
            detail="Billing limit reached or tenant suspended. Please upgrade your plan."
        )
        
    # Phase 12: Policy Engine
    try:
        from app.services.policy_service import evaluate_action
        allowed, reason = evaluate_action(db, tenant_uuid, "create_task", {"task_type": task_type})
        if not allowed:
            raise HTTPException(
                status_code=403,
                detail=f"Action blocked by policy: {reason}"
            )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Warning: Policy evaluation failed: {e}")

    task = Task(
        tenant_id=tenant_uuid,
        task_type=task_type,
        payload=payload,
        agent_pool=agent_pool,
        status=TaskStatus.PENDING,
    )
    db.add(task)
    
    # Increment usage counter (tasks_created)
    today = date.today()
    # tenant_id_str already got above
    tenant_uuid = uuid.UUID(tenant_id_str)
    
    usage = db.query(TenantUsage).filter(
        TenantUsage.tenant_id == tenant_uuid,
        TenantUsage.date == today
    ).first()
    
    if not usage:
        usage = TenantUsage(
            tenant_id=tenant_uuid,
            date=today,
            tasks_created=1
        )
        db.add(usage)
    else:
        usage.tasks_created += 1
        
    db.commit()
    db.refresh(task)
    return task


def get_task(db: Session, task_id: uuid.UUID) -> Optional[Task]:
    """Get a task by ID."""
    return db.query(Task).filter(Task.id == task_id).first()


def get_pending_tasks(db: Session, limit: int = 100) -> List[Task]:
    """Get pending tasks waiting for agents (tenant-scoped)."""
    return db.query(Task).filter(
        Task.status == TaskStatus.PENDING,
        Task.tenant_id == uuid.UUID(get_tenant_id())
    ).limit(limit).all()


def claim_task(
    db: Session, 
    task_id: uuid.UUID, 
    agent_id: str,
    agent_pool: Optional[str] = "default"
) -> Optional[Task]:
    """
    Claim a task for an agent - ATOMIC operation at database level.
    
    Now supports pool-based assignment:
    - If task has agent_pool set, only agents from that pool can claim
    - If task has no pool (None), any agent can claim (backward compat)
    
    Uses single UPDATE statement with WHERE clause to ensure only ONE agent
    can transition a task from PENDING → CLAIMED, regardless of concurrency.
    
    Race-condition free:
    - No pre-read
    - No check-then-act window
    - Single SQL statement at DB level
    
    Args:
        db: Database session
        task_id: Task UUID to claim
        agent_id: Agent claiming the task
        agent_pool: Agent's pool name
        
    Returns:
        Claimed Task if successful, None if task was already claimed or doesn't exist
    """
    # Atomic UPDATE: only succeeds if task is PENDING AND pool matches AND tenant matches
    stmt = update(Task).where(
        (Task.id == task_id) & 
        (Task.status == TaskStatus.PENDING) &
        (Task.tenant_id == uuid.UUID(get_tenant_id())) &
        ((Task.agent_pool == agent_pool) | (Task.agent_pool == None))
    ).values(
        status=TaskStatus.CLAIMED,
        agent_id=agent_id,
        claimed_at=datetime.utcnow()
    )
    
    result = db.execute(stmt)
    db.commit()
    
    # If no rows were updated, task was already claimed or doesn't exist
    if result.rowcount == 0:
        return None
    
    # Fetch and return the updated task
    task = get_task(db, task_id)
    return task


def find_and_claim_task(
    db: Session,
    agent_id: str,
    agent_pool: Optional[str] = "default"
) -> Optional[Task]:
    """
    Find the next available task and claim it atomically using Postgres FOR UPDATE SKIP LOCKED.
    
    This is the modern, scalable way to implement a task queue in Postgres.
    It prevents multiple agents from trying to claim the same task.
    """
    tenant_id = uuid.UUID(get_tenant_id())
    
    # 1. Select the next pending task for this tenant and pool
    # Use FOR UPDATE SKIP LOCKED for high concurrency safety
    stmt = (
        select(Task)
        .where(
            and_(
                Task.status == TaskStatus.PENDING,
                Task.tenant_id == tenant_id,
                or_(Task.agent_pool == agent_pool, Task.agent_pool == None)
            )
        )
        .order_by(Task.created_at.asc())
        .limit(1)
        .with_for_update(skip_locked=True)
    )
    
    task = db.execute(stmt).scalars().first()
    
    if not task:
        return None
        
    # 2. Update status and agent info
    task.status = TaskStatus.CLAIMED
    task.agent_id = agent_id
    task.claimed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(task)
    return task



def update_task_status(
    db: Session,
    task_id: uuid.UUID,
    status: str,
    result: Optional[Dict[str, Any]] = None,
    logs: Optional[str] = None,
    screenshot_url: Optional[str] = None,
    error_message: Optional[str] = None,
) -> Optional[Task]:
    """Update task status and optionally result/logs."""
    task = get_task(db, task_id)
    if not task:
        return None
    
    task.status = status
    if result is not None:
        task.result = result
    if logs is not None:
        task.logs = logs
    if screenshot_url is not None:
        task.screenshot_url = screenshot_url
    if error_message is not None:
        task.error_message = error_message
    
    # Set completion timestamp for terminal states
    if status in ["COMPLETED", "FAILED", "PAUSED_FOR_CAPTCHA"]:
        task.completed_at = datetime.utcnow()
        
        # Record metrics for terminal states
        try:
            from app.services.metrics_service import record_task_metrics
            record_task_metrics(db, task)
        except Exception as e:
            # Don't fail task update if metrics recording fails
            print(f"Warning: Failed to record metrics for task {task_id}: {e}")

        # Phase 10: Webhook Trigger
        try:
            from app.services.webhook_service import trigger_webhook_event
            event_type = f"task.{status.lower()}"
            trigger_webhook_event(
                db, 
                task.tenant_id, 
                event_type, 
                {"task_id": str(task.id), "status": status, "task_type": str(task.task_type)}
            )
        except Exception as e:
            print(f"Warning: Failed to trigger webhook for task {task_id}: {e}")
    
    # Set started_at if transitioning to RUNNING
    if status == "RUNNING" and not task.started_at:
        task.started_at = datetime.utcnow()
        # Trigger started webhook
        try:
            from app.services.webhook_service import trigger_webhook_event
            trigger_webhook_event(
                db, 
                task.tenant_id, 
                "task.started", 
                {"task_id": str(task.id), "status": "RUNNING", "task_type": str(task.task_type)}
            )
        except Exception as e:
            print(f"Warning: Failed to trigger 'started' webhook for task {task_id}: {e}")
    
    db.commit()
    db.refresh(task)
    return task


def retry_task(db: Session, task_id: uuid.UUID) -> Optional[Task]:
    """Retry a failed task."""
    task = get_task(db, task_id)
    if not task:
        return None
    
    if task.retry_count < task.max_retries:
        task.status = TaskStatus.PENDING
        task.retry_count += 1
        task.agent_id = None
        task.claimed_at = None
        task.error_message = None
        db.commit()
        db.refresh(task)
        return task
    
    return None


def delete_task(db: Session, task_id: uuid.UUID) -> bool:
    """Delete a task."""
    task = get_task(db, task_id)
    if not task:
        return False
    
    db.delete(task)
    db.commit()
    return True


def update_heartbeat(db: Session, task_id: uuid.UUID) -> bool:
    """Update task heartbeat timestamp."""
    task = get_task(db, task_id)
    if not task:
        return False
    
    task.last_heartbeat = datetime.utcnow()
    db.commit()
    return True


def release_stale_tasks(db: Session, timeout_seconds: int = 300) -> int:
    """
    Release tasks that haven't sent a heartbeat recently.
    
    Args:
        db: Database session
        timeout_seconds: Seconds of inactivity before releasing (default 5 mins)
        
    Returns:
        Number of released tasks
    """
    cutoff = datetime.utcnow().timestamp() - timeout_seconds
    cutoff_dt = datetime.fromtimestamp(cutoff)
    
    # Find stale RUNNING tasks
    stale_tasks = db.query(Task).filter(
        (Task.status == TaskStatus.RUNNING) &
        (
            (Task.last_heartbeat < cutoff_dt) | 
            ((Task.last_heartbeat == None) & (Task.started_at < cutoff_dt))
        )
    ).all()
    
    count = 0
    for task in stale_tasks:
        # Reset to PENDING
        task.status = TaskStatus.PENDING
        task.agent_id = None
        task.started_at = None
        task.last_heartbeat = None
        task.retry_count += 1
        
        # Log the incident
        log_msg = f"\n[System] Task released due to timeout (last heartbeat: {task.last_heartbeat})\n"
        task.logs = (task.logs or "") + log_msg
        
        count += 1
    
    if count > 0:
        db.commit()
        
    return count
