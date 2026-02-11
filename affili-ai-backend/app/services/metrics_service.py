"""
Metrics recording service for task execution.
"""

from sqlalchemy.orm import Session
from app.models.task import Task
from app.models.metrics import TaskMetrics
from app.models.usage import TenantUsage
from datetime import datetime, date
from typing import Optional
import uuid


from app.core.tenant import get_tenant_id

def record_task_metrics(db: Session, task: Task) -> Optional[TaskMetrics]:
    """
    Record metrics for a completed or failed task.
    
    Args:
        db: Database session
        task: Completed task
        
    Returns:
        TaskMetrics object if successful, None otherwise
    """
    # Only record for terminal states
    if task.status not in ["COMPLETED", "FAILED", "PAUSED_FOR_CAPTCHA"]:
        return None
    
    # Calculate duration
    duration = None
    if task.started_at and task.completed_at:
        duration = (task.completed_at - task.started_at).total_seconds()
    
    # Extract failure information
    failure_type = None
    if task.result and isinstance(task.result, dict):
        failure_type = task.result.get("failure_type")
    
    # Determine success
    success = (task.status == "COMPLETED")
    captcha_detected = (task.status == "PAUSED_FOR_CAPTCHA")
    
    # Extract program name from payload
    program_name = None
    if task.payload and isinstance(task.payload, dict):
        program_name = task.payload.get("program_name")
    
    # Create metrics record
    tenant_id_str = get_tenant_id()
    try:
        metrics = TaskMetrics(
            tenant_id=uuid.UUID(tenant_id_str),
            task_id=task.id,
            program_name=program_name,
            task_type=task.task_type.value if hasattr(task.task_type, 'value') else str(task.task_type),
            agent_id=task.agent_id,
            agent_pool=task.agent_pool,
            duration_seconds=duration,
            success=success,
            failure_type=failure_type,
            captcha_detected=captcha_detected
        )
        
        db.add(metrics)
        # removed db.commit() to ensure atomicity with the caller (update_task_status)
        # db.flush() is safer as it pushes to DB without committing the whole transaction
        db.flush()
        
        # Also update tenant usage
        try:
            from app.services.usage_service import update_usage
            update_usage(db, task.tenant_id, task_minutes=duration or 0)
        except Exception as e:
            logger.warning(f"Failed to update usage from metrics: {e}")
        
        # Update agent stats
        try:
            from app.services.agent_service import update_agent_stats
            update_agent_stats(db, task)
        except Exception as e:
            logger.warning(f"Failed to update agent stats: {e}")
            
        return metrics
        
    except Exception as e:
        # Crucial: Rollback ONLY if we added something to the session that failed
        db.rollback()
        from app.core.logging import logger
        logger.error(f"OBSERVABILITY_FAILURE [METRICS_RECORDING] task_id={task.id} error='{e}'")
        return None
