"""
Tasks API endpoints - core agent queue.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.task import Task, TaskStatus
from app.schemas.task import TaskCreate, TaskUpdate, TaskClaimRequest, TaskPollRequest, TaskResponse
from app.core.security import verify_agent_key
from app.services.task_dispatcher import (
    create_task as svc_create_task,
    get_task,
    get_pending_tasks,
    claim_task as svc_claim_task,
    update_task_status,
    retry_task as svc_retry_task,
)
from app.services.audit_service import log_audit_event, AuditEventType
from app.core.rate_limiter import check_rate_limit
from app.api.dependencies import verify_tenant, require_roles, get_current_user, get_optional_user
from app.core.tenant import get_tenant_id
from app.models.user import UserRole, User
from typing import List, Optional
import uuid

router = APIRouter(prefix="/tasks", tags=["tasks"], dependencies=[Depends(verify_tenant)])


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED, 
             dependencies=[Depends(require_roles(UserRole.OWNER, UserRole.ADMIN, UserRole.OPERATOR))])
def create_task(
    task_in: TaskCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a custom task.
    Limited to 10 requests per minute per IP.
    """
    # Rate limiting - use client IP as identifier
    client_ip = request.client.host if request.client else "unknown"
    check_rate_limit("task_creation", identifier=client_ip)

    try:
        task = svc_create_task(
            db, 
            task_in.task_type, 
            task_in.payload,
            agent_pool=task_in.agent_pool,
            program_id=task_in.program_id
        )
        
        # Audit Log
        log_audit_event(
            db=db,
            event_type=AuditEventType.TASK_CREATED,
            actor_type="USER",
            actor_id=str(current_user.id),
            actor_email=current_user.email,
            resource_type="TASK",
            resource_id=str(task.id),
            details={"task_type": task_in.task_type}
        )
        db.commit()
        
        return task
    except Exception as e:
        import traceback
        with open("backend_error.log", "a") as f:
            f.write(f"\n[ERROR] Task Creation Failed: {str(e)}\n")
            f.write(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@router.get("", response_model=List[TaskResponse])
def list_tasks(
    status: Optional[str] = None,
    agent_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List tasks with optional filtering (tenant-scoped)."""
    query = db.query(Task).filter(Task.tenant_id == uuid.UUID(get_tenant_id()))
    if status:
        query = query.filter(Task.status == status)
    if agent_id:
        query = query.filter(Task.agent_id == agent_id)
    return query.offset(skip).limit(limit).all()


@router.get("/{task_id}", response_model=TaskResponse)
def get_task_endpoint(
    task_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get status of a specific task."""
    task = get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    # Tenant check
    if str(task.tenant_id) != get_tenant_id():
        raise HTTPException(status_code=404, detail="Task not found")
        
    return task


@router.post("/{task_id}/claim", response_model=TaskResponse)
def claim_task_endpoint(
    task_id: uuid.UUID,
    claim_req: TaskClaimRequest,
    db: Session = Depends(get_db),
):
    """
    Claim a task atomically.
    Supports pool-based assignment.
    """
    agent_pool = getattr(claim_req, "agent_pool", "default")
    task = svc_claim_task(db, task_id, claim_req.agent_id, agent_pool=agent_pool)
    if not task:
        raise HTTPException(status_code=409, detail="Task already claimed or not found")
    return task


@router.post("/{task_id}/update", response_model=TaskResponse)
async def update_task(
    task_id: uuid.UUID,
    update_in: TaskUpdate,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
    current_human: Optional[User] = Depends(get_optional_user)
):
    """Update task progress/status. 
    Accessible by Users (ADMIN/OPERATOR) OR Agents with valid API key.
    """
    from app.core.security import verify_agent_key
    from app.api.dependencies import verify_tenant
    
    authenticated = False
    actor_type = "UNKNOWN"
    actor_id = "unknown"
    actor_email = "unknown"

    # 1. Try Human User Auth (has higher precedence for audit)
    if current_human:
        # Check roles
        if current_human.role in (UserRole.OWNER, UserRole.ADMIN, UserRole.OPERATOR):
            authenticated = True
            actor_type = "USER"
            actor_id = str(current_human.id)
            actor_email = current_human.email
    
    # 2. Try Agent Auth (Bearer token) if not authenticated as human
    if not authenticated and authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        if verify_agent_key(token):
            authenticated = True
            actor_type = "AGENT"
            # Agents often don't have a formal "User" record but act on behalf of a tenant
            # Ensure multi-tenant context is set (usually done by verify_tenant dep)
            task_obj = get_task(db, task_id)
            actor_id = task_obj.agent_id if task_obj and task_obj.agent_id else "remote-agent"
            actor_email = "agent@affili-ai.internal"

    if not authenticated:
        raise HTTPException(status_code=401, detail="Not authorized to update tasks")

    task = update_task_status(
        db,
        task_id,
        update_in.status or TaskStatus.RUNNING,
        update_in.result,
        update_in.logs,
        update_in.screenshot_url,
        update_in.error_message,
        update_in.operator_confidence,
        update_in.feedback_json,
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    # Audit Log for status change
    log_audit_event(
        db=db,
        event_type=AuditEventType.TASK_EXECUTED,
        actor_type=actor_type,
        actor_id=actor_id,
        actor_email=actor_email,
        resource_type="TASK",
        resource_id=str(task.id),
        details={"status": task.status, "result": str(update_in.result)[:100] if update_in.result else None}
    )
    db.commit()
    
    return task


@router.post("/{task_id}/retry", response_model=TaskResponse,
             dependencies=[Depends(require_roles(UserRole.OWNER, UserRole.ADMIN, UserRole.OPERATOR))])
def retry_task_endpoint(
    task_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retry a failed task.
    Resets status to PENDING and increments retry count.
    """
    task = get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    # Tenant check
    if str(task.tenant_id) != get_tenant_id():
        raise HTTPException(status_code=404, detail="Task not found")
        
    # Check if retryable
    if task.status != TaskStatus.FAILED and task.status != "PAUSED_FOR_CAPTCHA":
        raise HTTPException(status_code=400, detail=f"Cannot retry task in status {task.status}")
        
    retried_task = svc_retry_task(db, task_id)
    if not retried_task:
        raise HTTPException(status_code=400, detail="Retry limit reached or failed to retry")
        
    # Audit
    log_audit_event(
        db=db,
        event_type=AuditEventType.ADMIN_ACTION,
        actor_type="USER",
        actor_id=str(current_user.id),
        actor_email=current_user.email,
        resource_type="TASK",
        resource_id=str(task.id),
        details={"action": "retry", "previous_status": task.status}
    )
    db.commit()
    
    return retried_task


@router.post("/poll", response_model=List[TaskResponse])
def poll_tasks(
    poll_req: TaskPollRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """Agent endpoint to poll for tasks.
    
    Agents send a Bearer token in Authorization header.
    Returns list of PENDING tasks (unclaimed).
    """
    # Verify API key
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization.split(" ")[1]
    if not verify_agent_key(token):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Get pending tasks
    tasks = get_pending_tasks(db, limit=10)
    return tasks


@router.post("/claim-next", response_model=Optional[TaskResponse])
def claim_next_task(
    poll_req: TaskClaimRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """
    Find and claim the next available task for an agent.
    Uses FOR UPDATE SKIP LOCKED for maximum concurrency safety.
    """
    # Verify API key
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization.split(" ")[1]
    if not verify_agent_key(token):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    from app.services.task_dispatcher import find_and_claim_task
    agent_pool = getattr(poll_req, "agent_pool", "default")
    task = find_and_claim_task(db, poll_req.agent_id, agent_pool=agent_pool)
    return task



@router.post("/{task_id}/heartbeat", status_code=status.HTTP_200_OK)
def heartbeat_task(
    task_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """Update task heartbeat."""
    from app.services.task_dispatcher import update_heartbeat
    success = update_heartbeat(db, task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"status": "ok"}


@router.post("/cleanup", status_code=status.HTTP_200_OK, 
             dependencies=[Depends(require_roles(UserRole.OWNER, UserRole.ADMIN))])
def cleanup_tasks(
    timeout_seconds: int = 300,
    db: Session = Depends(get_db),
):
    """Release stale tasks."""
    from app.services.task_dispatcher import release_stale_tasks
    count = release_stale_tasks(db, timeout_seconds)
    return {"released_count": count}
