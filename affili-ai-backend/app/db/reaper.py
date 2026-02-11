"""
Heartbeat reaper for recovering orphaned task claims.

When workers crash after claiming tasks but before completing them,
the reaper identifies stale claims and resets them to PENDING for retry.

This ensures:
- No tasks are permanently lost due to worker crashes
- Failed claims are retried with fresh workers
- System self-heals from infrastructure failures
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List
import uuid

from app.models.task import Task, TaskStatus
from app.models.audit_log import AuditLog, AuditEventType


def reap_stale_task_claims(
    db: Session,
    heartbeat_timeout_minutes: int = 5,
    dry_run: bool = False
) -> List[uuid.UUID]:
    """
    Find and reset tasks with stale claims (no heartbeat within timeout).
    
    A task is considered stale if:
    1. Status is CLAIMED or RUNNING
    2. Either:
       - last_heartbeat is older than timeout
       - last_heartbeat is NULL and claimed_at is older than timeout
    
    Args:
        db: Database session
        heartbeat_timeout_minutes: Minutes without heartbeat before considering stale
        dry_run: If True, only identify stale tasks without resetting them
    
    Returns:
        List of task IDs that were (or would be) reaped
    
    Usage:
        # In production cron job:
        from app.db.session import SessionLocal
        from app.db.reaper import reap_stale_task_claims
        
        db = SessionLocal()
        try:
            reaped = reap_stale_task_claims(db, heartbeat_timeout_minutes=10)
            print(f"Reaped {len(reaped)} stale tasks")
        finally:
            db.close()
    """
    cutoff_time = datetime.utcnow() - timedelta(minutes=heartbeat_timeout_minutes)
    
    # Find stale tasks
    stale_tasks = db.query(Task).filter(
        and_(
            Task.status.in_([TaskStatus.CLAIMED, TaskStatus.RUNNING]),
            or_(
                # Has heartbeat, but it's stale
                Task.last_heartbeat < cutoff_time,
                # No heartbeat at all, and claim is old
                and_(
                    Task.last_heartbeat == None,
                    Task.claimed_at < cutoff_time
                )
            )
        )
    ).all()
    
    reaped_ids = [task.id for task in stale_tasks]
    
    if dry_run:
        return reaped_ids
    
    # Reset stale tasks to PENDING
    for task in stale_tasks:
        original_agent = task.agent_id
        original_status = task.status
        
        task.status = TaskStatus.PENDING
        task.agent_id = None
        task.claimed_at = None
        task.last_heartbeat = None
        
        # Log the reaping action for audit trail
        audit = AuditLog(
            tenant_id=task.tenant_id,
            event_type=AuditEventType.TASK_REAPED,
            actor_type="system",
            actor_id="heartbeat-reaper",
            resource_type="task",
            resource_id=str(task.id),
            details={
                "original_agent_id": original_agent,
                "original_status": original_status.value,
                "reason": "heartbeat_timeout",
                "timeout_minutes": heartbeat_timeout_minutes,
                "last_heartbeat": task.last_heartbeat.isoformat() if task.last_heartbeat else None,
                "claimed_at": task.claimed_at.isoformat() if task.claimed_at else None
            }
        )
        db.add(audit)
    
    db.commit()
    
    return reaped_ids


def get_stale_claim_metrics(
    db: Session,
    heartbeat_timeout_minutes: int = 5
) -> dict:
    """
    Get metrics about stale claims without modifying them.
    
    Returns:
        Dict with:
        - stale_count: Number of stale tasks
        - stale_task_ids: List of stale task IDs
        - oldest_stale_claim: Oldest claim timestamp
        - agents_with_stale_claims: List of agent IDs with stale claims
    """
    cutoff_time = datetime.utcnow() - timedelta(minutes=heartbeat_timeout_minutes)
    
    stale_tasks = db.query(Task).filter(
        and_(
            Task.status.in_([TaskStatus.CLAIMED, TaskStatus.RUNNING]),
            or_(
                Task.last_heartbeat < cutoff_time,
                and_(
                    Task.last_heartbeat == None,
                    Task.claimed_at < cutoff_time
                )
            )
        )
    ).all()
    
    if not stale_tasks:
        return {
            "stale_count": 0,
            "stale_task_ids": [],
            "oldest_stale_claim": None,
            "agents_with_stale_claims": []
        }
    
    oldest_claim = min(
        (t.claimed_at for t in stale_tasks if t.claimed_at),
        default=None
    )
    
    agents = list(set(t.agent_id for t in stale_tasks if t.agent_id))
    
    return {
        "stale_count": len(stale_tasks),
        "stale_task_ids": [str(t.id) for t in stale_tasks],
        "oldest_stale_claim": oldest_claim.isoformat() if oldest_claim else None,
        "agents_with_stale_claims": agents
    }
