"""
Task dispatcher service for creating and managing tasks.
"""

from sqlalchemy.orm import Session
from app.models.task import Task, TaskType, TaskStatus
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid


def create_task(
    db: Session,
    task_type: str,
    payload: Optional[Dict[str, Any]] = None,
) -> Task:
    """Create a new task for an agent to process."""
    task = Task(
        task_type=task_type,
        payload=payload,
        status=TaskStatus.PENDING,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def get_task(db: Session, task_id: uuid.UUID) -> Optional[Task]:
    """Get a task by ID."""
    return db.query(Task).filter(Task.id == task_id).first()


def get_pending_tasks(db: Session, limit: int = 10) -> List[Task]:
    """Get all pending tasks."""
    return db.query(Task).filter(
        Task.status == TaskStatus.PENDING
    ).limit(limit).all()


def claim_task(db: Session, task_id: uuid.UUID, agent_id: str) -> Optional[Task]:
    """Claim a task for an agent."""
    task = get_task(db, task_id)
    if not task or task.status != TaskStatus.PENDING:
        return None
    
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
        task.logs = (task.logs or "") + logs
    if screenshot_url is not None:
        task.screenshot_url = screenshot_url
    if error_message is not None:
        task.error_message = error_message
    
    # Update timestamps based on status
    if status == TaskStatus.RUNNING and not task.started_at:
        task.started_at = datetime.utcnow()
    elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
        task.completed_at = datetime.utcnow()
    
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
