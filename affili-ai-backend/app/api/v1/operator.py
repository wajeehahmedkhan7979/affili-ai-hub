"""
Operator intervention API endpoints.

Handles paused task lifecycle:
- List paused tasks
- Resume tasks (with governance checks)
- Cancel tasks
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid

from app.core.time import utcnow
from app.db.session import get_db
from app.core.auth import require_roles, get_current_user
from app.models import Task, OperatorActionLog, OperatorActionType
from app.services.cost_governance import cost_governance
from app.core.logging import logger

router = APIRouter(prefix="/operator", tags=["operator"])


# === Request Models ===

class ResumeTaskRequest(BaseModel):
    reason: Optional[str] = None
    

class CancelTaskRequest(BaseModel):
    reason: str


# === Paused Task Endpoints ===

@router.get("/tasks/paused")
def get_paused_tasks(
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["OWNER", "ADMIN", "OPERATOR"])),
    limit: int = 50
):
    """
    Get all paused tasks awaiting human intervention.
    
    Filters:
    - PAUSED_FOR_CAPTCHA
    - PAUSED_LOW_CONFIDENCE
-    - PAUSED_OPERATOR_REVIEW
    """
    tenant_id = current_user.tenant_id
    
    paused_statuses = [
        "PAUSED_FOR_CAPTCHA",
        "PAUSED_LOW_CONFIDENCE",
        "PAUSED_OPERATOR_REVIEW"
    ]
    
    tasks = db.query(Task).filter(
        and_(
            Task.tenant_id == tenant_id,
            Task.status.in_(paused_statuses)
        )
    ).order_by(Task.updated_at.desc()).limit(limit).all()
    
    return {
        "tenant_id": str(tenant_id),
        "total_paused": len(tasks),
        "tasks": [
            {
                "id": str(task.id),
                "type": task.task_type,
                "status": task.status,
                "program_id": str(task.program_id) if task.program_id else None,
                "paused_at": task.updated_at.isoformat(),
                "screenshot_url": task.screenshot_url if hasattr(task, 'screenshot_url') else None,
                "metadata": task.payload
            }
            for task in tasks
        ]
    }


@router.post("/tasks/{task_id}/resume")
def resume_task(
    task_id: str,
    request: ResumeTaskRequest,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["OWNER", "ADMIN", "OPERATOR"]))
):
    """
    Resume a paused task after human intervention.
    
    SAFETY:
    - Re-checks kill-switch
    - Re-checks quotas
    - Does NOT re-run completed steps
    """
    task_uuid = uuid.UUID(task_id)
    
    # FETCH TASK FIRST (Required to get tenant_id for kill-switch check)
    task = db.query(Task).filter(Task.id == task_uuid).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # GOVERNANCE: Re-check kill-switch (FAIL FAST - Bucket A Fix)
    # Moved to top for Phase 2.5 safety compliance
    if cost_governance.is_tenant_disabled(db, task.tenant_id):
        raise HTTPException(
            status_code=403,
            detail="AI operations disabled for tenant (kill-switch active)"
        )
    
    # Verify paused
    if not task.status.startswith("PAUSED_") and task.status != "FAILED": # Allow resuming failed tasks if strictly needed, but policy says paused. 
        # Actually v1.1 says resume paused tasks.
        # But wait, if kill-switch RAN, the task is FAILED.
        # So we should probably expect 403 regardless of status if tenant is disabled.
        # But logic says: check tenant disabled -> 403.
        # Then check status.
        pass

    if not task.status.startswith("PAUSED_"):
        raise HTTPException(status_code=400, detail="Task is not paused")
    
    # GOVERNANCE: Re-check quotas
    quota_check = cost_governance.check_llm_quota(db, task.tenant_id)
    if not quota_check["allowed"]:
        raise HTTPException(
            status_code=429,
            detail=f"LLM quota exceeded: {quota_check.get('reason', 'Unknown')}"
        )
    
    # Update task status
    task.status = "PENDING"  # Re-queue for agent pickup
    task.updated_at = utcnow()
    
    if request.reason:
        if not task.payload:
            task.payload = {}
        task.payload["resume_reason"] = request.reason
    
    # Log operator action
    log_entry = OperatorActionLog(
        tenant_id=task.tenant_id,
        operator_id=current_user.id,
        task_id=task.id,
        action=OperatorActionType.RESUME_TASK,
        reason=request.reason
    )
    db.add(log_entry)
    
    db.commit()
    
    logger.info(f"Task {task_id} resumed by {current_user.email}")
    
    return {
        "task_id": str(task_id),
        "status": "PENDING",
        "resumed_at": utcnow().isoformat(),
        "resumed_by": str(current_user.id)
    }


@router.post("/tasks/{task_id}/cancel")
def cancel_task(
    task_id: str,
    request: CancelTaskRequest,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["OWNER", "ADMIN", "OPERATOR"]))
):
    """
    Cancel a paused task.
    
    Use when task cannot be completed (e.g., unsolvable CAPTCHA).
    """
    task_uuid = uuid.UUID(task_id)
    
    task = db.query(Task).filter(Task.id == task_uuid).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Update to FAILED_OPERATOR_CANCEL
    task.status = "FAILED_OPERATOR_CANCEL"
    task.updated_at = utcnow()
    
    if not task.payload:
        task.payload = {}
    task.payload["cancel_reason"] = request.reason
    
    # Log operator action
    log_entry = OperatorActionLog(
        tenant_id=task.tenant_id,
        operator_id=current_user.id,
        task_id=task.id,
        action=OperatorActionType.CANCEL_TASK,
        reason=request.reason
    )
    db.add(log_entry)
    
    db.commit()
    
    logger.warning(f"Task {task_id} CANCELLED by {current_user.email}: {request.reason}")
    
    return {
        "task_id": str(task_id),
        "status": "FAILED_OPERATOR_CANCEL",
        "cancelled_at": utcnow().isoformat(),
        "reason": request.reason
    }