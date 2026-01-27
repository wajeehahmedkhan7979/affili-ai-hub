"""
Tasks API endpoints - core agent queue.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header
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
)
from typing import List, Optional
import uuid

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    task_in: TaskCreate,
    db: Session = Depends(get_db),
):
    """Create a custom task."""
    task = svc_create_task(db, task_in.task_type, task_in.payload)
    return task


@router.get("", response_model=List[TaskResponse])
def list_tasks(
    status: Optional[str] = None,
    agent_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """List tasks with optional filtering."""
    query = db.query(Task)
    if status:
        query = query.filter(Task.status == status)
    if agent_id:
        query = query.filter(Task.agent_id == agent_id)
    return query.offset(skip).limit(limit).all()


@router.get("/{task_id}", response_model=TaskResponse)
def get_task_endpoint(
    task_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """Get a task by ID."""
    task = get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/{task_id}/claim", response_model=TaskResponse)
def claim_task(
    task_id: uuid.UUID,
    claim_req: TaskClaimRequest,
    db: Session = Depends(get_db),
):
    """Claim a task for an agent."""
    task = svc_claim_task(db, task_id, claim_req.agent_id)
    if not task:
        raise HTTPException(status_code=400, detail="Cannot claim task (not pending)")
    return task


@router.post("/{task_id}/update", response_model=TaskResponse)
def update_task(
    task_id: uuid.UUID,
    update_in: TaskUpdate,
    db: Session = Depends(get_db),
):
    """Update task progress/status."""
    task = update_task_status(
        db,
        task_id,
        update_in.status or TaskStatus.RUNNING,
        update_in.result,
        update_in.logs,
        update_in.screenshot_url,
        update_in.error_message,
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


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
