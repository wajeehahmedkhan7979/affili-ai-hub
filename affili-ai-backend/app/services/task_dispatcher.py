"""
Task dispatcher service for creating and managing tasks.
"""

from sqlalchemy.orm import Session
from sqlalchemy import update, select, and_, or_
from app.core.time import utcnow
from app.models.task import Task, TaskStatus
from app.models.usage import TenantUsage
from app.schemas.task import TaskCreate
from app.core.tenant import get_tenant_id
from app.db.retry import retry_on_deadlock
from datetime import datetime, date
import uuid
from typing import List, Optional, Dict, Any


from app.core.logging import logger
from fastapi import HTTPException
from app.services.billing_service import check_task_limit
from app.services.policy_service import evaluate_action
from app.models.agent import Agent

def _ensure_agent_identity(db: Session, agent_id: str, public_key: Optional[str] = None) -> bool:
    """
    Ensure agent exists and handles public key pinning.
    Returns True if agent is authorized (new pin or matches existing pin), False otherwise.
    """
    tenant_id = uuid.UUID(get_tenant_id())
    agent = db.query(Agent).filter(Agent.id == agent_id, Agent.tenant_id == tenant_id).first()
    
    if not agent:
        # Create agent record and pin public key if provided
        agent = Agent(
            id=agent_id,
            tenant_id=tenant_id,
            pinned_public_key=public_key,
            last_seen=utcnow()
        )
        db.add(agent)
        return True
    
    # Update last seen
    agent.last_seen = utcnow()
    
    # Check public key pinning
    if public_key:
        if agent.pinned_public_key:
            if agent.pinned_public_key != public_key:
                logger.warning(f"Agent {agent_id} attempted to change pinned public key")
                return False
        else:
            # Pin the key for the first time
            agent.pinned_public_key = public_key
            
    return True

def create_task(
    db: Session,
    task_type: str,
    payload: Optional[Dict[str, Any]] = None,
    agent_pool: Optional[str] = "default",
    program_id: Optional[uuid.UUID] = None,
) -> Task:
    """Create a new task for an agent to process."""
    tenant_id_str = get_tenant_id()
    tenant_uuid = uuid.UUID(tenant_id_str)
    
    
    # Phase 9: Billing Enforcement (skip in DEBUG mode)
    from app.core.config import get_settings
    settings = get_settings()
    
    # Phase 2.5: Kill-Switch Enforcement (Bucket A Fix)
    from app.services.cost_governance import cost_governance
    if cost_governance.is_tenant_disabled(db, tenant_uuid):
        raise HTTPException(
            status_code=403,
            detail="AI operations disabled for tenant (kill-switch active)"
        )

    if not settings.DEBUG:
        if not check_task_limit(db, tenant_uuid):
            raise HTTPException(
                status_code=402, 
                detail="Billing limit reached or tenant suspended. Please upgrade your plan."
            )

        
    # Phase 12: Policy Engine
    try:
        context = {"task_type": task_type, **(payload or {})}
        allowed, reason = evaluate_action(db, tenant_uuid, "create_task", context)
        if not allowed:
            raise HTTPException(
                status_code=403,
                detail=f"Action blocked by policy: {reason}"
            )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback() # START ROLLBACK
        print(f"Warning: Policy evaluation failed: {e}")

    # Phase 6.1: Program-level Throttling
    if program_id:
        from app.services.cost_governance import cost_governance
        throttle_check = cost_governance.check_program_task_limit(db, tenant_uuid, program_id)
        if not throttle_check["allowed"]:
            raise HTTPException(
                status_code=429,
                detail=f"Program limit reached: {throttle_check['active_count']}/{throttle_check['limit']} active tasks."
            )

    task = Task(
        tenant_id=tenant_uuid,
        # program_id=program_id, # Removed in v1.1
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
    
    # Phase 14: WebSocket Broadcast (TASK_CREATED)
    try:
        from app.core.websockets import manager
        import asyncio
        
        payload = {
            "event": "TASK_CREATED",
            "data": {
                "id": str(task.id),
                "status": task.status,
                "task_type": task.task_type,
                "created_at": task.created_at.isoformat()
            }
        }
        
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(manager.broadcast(payload, str(task.tenant_id)))
        except RuntimeError:
            pass
    except Exception as e:
        print(f"Warning: Failed to broadcast create event: {e}")
        
    return task


def get_task(db: Session, task_id: uuid.UUID) -> Optional[Task]:
    """
    Get a task by ID. Uses ORM but with load_only to avoid loading non-existent columns
    (program_id, operator_confidence, feedback_json) in the v1.1 frozen schema.
    """
    from sqlalchemy.orm import load_only
    
    # Load only columns that definitely exist in the v1.1 DB schema
    task = db.query(Task).options(
        load_only(
            Task.id, Task.tenant_id, Task.task_type, Task.status, Task.payload,
            Task.result, Task.agent_id, Task.agent_pool, Task.retry_count,
            Task.max_retries, Task.logs, Task.screenshot_url, Task.error_message,
            Task.created_at, Task.updated_at, Task.claimed_at, Task.started_at,
            Task.completed_at, Task.last_heartbeat
        )
    ).filter(Task.id == task_id).first()
    
    return task


def get_pending_tasks(db: Session, limit: int = 100) -> List[Task]:
    """Get pending tasks waiting for agents (tenant-scoped).
    Uses load_only to avoid loading non-existent columns in v1.1 schema.
    """
    from sqlalchemy.orm import load_only
    
    return db.query(Task).options(
        load_only(
            Task.id, Task.tenant_id, Task.task_type, Task.status, Task.payload,
            Task.result, Task.agent_id, Task.agent_pool, Task.retry_count,
            Task.max_retries, Task.logs, Task.screenshot_url, Task.error_message,
            Task.created_at, Task.updated_at, Task.claimed_at, Task.started_at,
            Task.completed_at, Task.last_heartbeat
        )
    ).filter(
        Task.status == TaskStatus.PENDING,
        Task.tenant_id == uuid.UUID(get_tenant_id())
    ).limit(limit).all()


def claim_task(
    db: Session, 
    task_id: uuid.UUID, 
    agent_id: str,
    agent_pool: Optional[str] = "default",
    public_key: Optional[str] = None
) -> Optional[Task]:
    """
    Claim a task for an agent - ATOMIC operation at database level.
    
    Now supports pool-based assignment and agent identity pinning.
    """
    # 0. Ensure agent identity is valid (pinning check)
    if not _ensure_agent_identity(db, agent_id, public_key):
        return None
        
    # Atomic UPDATE: only succeeds if task is PENDING AND pool matches AND tenant matches
    stmt = update(Task).where(
        (Task.id == task_id) & 
        (Task.status == TaskStatus.PENDING) &
        (Task.tenant_id == uuid.UUID(get_tenant_id())) &
        ((Task.agent_pool == agent_pool) | (Task.agent_pool == None))
    ).values(
        status=TaskStatus.CLAIMED,
        agent_id=agent_id,
        claimed_at=utcnow()
    )
    
    result = db.execute(stmt)
    db.commit()
    
    # If no rows were updated, task was already claimed or doesn't exist
    if result.rowcount == 0:
        return None
    
    # Fetch and return the updated task
    task = get_task(db, task_id)
    return task


@retry_on_deadlock(max_attempts=3, backoff_ms=50)
def find_and_claim_task(
    db: Session,
    agent_id: str,
    agent_pool: Optional[str] = "default",
    public_key: Optional[str] = None
) -> Optional[Task]:
    """
    Find the next available task and claim it atomically.
    Supports agent identity pinning.
    """
    # 0. Ensure agent identity is valid (pinning check)
    if not _ensure_agent_identity(db, agent_id, public_key):
        return None
        
    tenant_id = uuid.UUID(get_tenant_id())
    is_postgres = db.bind.dialect.name == "postgresql"
    
    if is_postgres:
        # Postgres: Atomic UPDATE with subquery and RETURNING
        # This is the safest pattern - single statement, zero race window
        subquery = (
            select(Task.id)
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
            .scalar_subquery()
        )
        
        stmt = (
            update(Task)
            .where(Task.id == subquery)
            .values(
                status=TaskStatus.CLAIMED,
                agent_id=agent_id,
                claimed_at=utcnow()
            )
            .returning(Task)
        )
        
        result = db.execute(stmt)
        db.commit()
        task = result.scalars().first()
        
        if task:
            db.refresh(task)  # Ensure all relationships loaded
        return task
    
    else:
        # SQLite fallback: Select-then-update with row lock
        # Not as robust, but acceptable for dev/test
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
            .with_for_update()
        )
        
        task = db.execute(stmt).scalars().first()
        
        if not task:
            return None
        
        task.status = TaskStatus.CLAIMED
        task.agent_id = agent_id
        task.claimed_at = utcnow()
        
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
    # operator_confidence: Optional[int] = None,
    # feedback_json: Optional[Dict[str, Any]] = None,
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
    # if operator_confidence is not None:
    #    task.operator_confidence = operator_confidence
    # if feedback_json is not None:
    #    task.feedback_json = feedback_json
    
    # Set completion timestamp for terminal states
    if status in ["COMPLETED", "FAILED", "PAUSED_FOR_CAPTCHA"]:
        task.completed_at = utcnow()
        
        # Record metrics for terminal states
        try:
            from app.services.metrics_service import record_task_metrics
            record_task_metrics(db, task)
        except Exception as e:
            # Don't fail task update if metrics recording fails, but must rollback to clear poisoned session
            db.rollback()
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

        # Phase 21: Workflow Orchestration Hook
        try:
            from app.services.workflow_service import workflow_service
            print(f"DEBUG: Checking workflow progression for task {task_id}")
            workflow_service.handle_task_completion(db, task_id)
            print(f"DEBUG: Workflow progression completed for task {task_id}")
        except Exception as e:
            import traceback
            print(f"ERROR: Failed to progress workflow for task {task_id}: {e}")
            print(f"Traceback: {traceback.format_exc()}")
    
    # Set started_at if transitioning to RUNNING
    if status == "RUNNING" and not task.started_at:
        task.started_at = utcnow()
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
    
    # Phase 14: WebSocket Broadcast
    # Bridge Sync (SQLAlchemy) -> Async (WebSockets)
    try:
        from app.core.websockets import manager
        import asyncio
        
        payload = {
            "event": "TASK_UPDATED",
            "data": {
                "id": str(task.id),
                "status": task.status,
                "task_type": task.task_type,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "updated_at": task.updated_at.isoformat() if task.updated_at else None
            }
        }
        
        # Check if there is a running loop
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(manager.broadcast(payload, str(task.tenant_id)))
        except RuntimeError:
            # No running loop (e.g. running from script/worker without async loop)
            # In purely sync context, we skip broadcast or need a separate event bus (Redis)
            pass
            
    except Exception as e:
        print(f"Warning: Failed to broadcast WebSocket event: {e}")

    return task


def retry_task(db: Session, task_id: uuid.UUID) -> Optional[Task]:
    """Retry a failed task."""
    task = get_task(db, task_id)
    if not task:
        return None
    
    # Hard Retry Ceiling for v1.1
    retry_limit = min(task.max_retries, 3)
    if task.retry_count < retry_limit:
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
    
    task.last_heartbeat = utcnow()
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
    from sqlalchemy.orm import load_only
    
    cutoff = utcnow().timestamp() - timeout_seconds
    cutoff_dt = datetime.fromtimestamp(cutoff)
    
    # Find stale RUNNING tasks using load_only to avoid non-existent columns
    stale_tasks = db.query(Task).options(
        load_only(
            Task.id, Task.tenant_id, Task.task_type, Task.status, Task.payload,
            Task.result, Task.agent_id, Task.agent_pool, Task.retry_count,
            Task.max_retries, Task.logs, Task.screenshot_url, Task.error_message,
            Task.created_at, Task.updated_at, Task.claimed_at, Task.started_at,
            Task.completed_at, Task.last_heartbeat
        )
    ).filter(
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