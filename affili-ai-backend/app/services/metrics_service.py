"""
Metrics recording service for task execution.
"""

from sqlalchemy.orm import Session
from app.models.task import Task
from app.models.metrics import TaskMetrics
from app.models.usage import TenantUsage
from app.models.agent import Agent
from datetime import datetime, date
from typing import Optional
import uuid


from app.core.tenant import get_tenant_id
from app.core.logging import logger

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
        start = task.started_at
        end = task.completed_at
        if start.tzinfo is None:
            from datetime import timezone
            start = start.replace(tzinfo=timezone.utc)
        if end.tzinfo is None:
            from datetime import timezone
            end = end.replace(tzinfo=timezone.utc)
        duration = (end - start).total_seconds()
    
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
    tenant_id = get_tenant_id()
    
    def safe_uuid(val):
        if isinstance(val, uuid.UUID): return val
        if not val: return None
        try:
             if isinstance(val, int): return uuid.UUID(int=val)
             return uuid.UUID(str(val))
        except: return val
        
    safe_tid = safe_uuid(tenant_id)
    # Ensure agent exists in the database
    agent_id = task.agent_id # Assuming task.agent_id is available
    pool = task.agent_pool # Assuming task.agent_pool is available
    
    if agent_id and pool and safe_tid:
        agent = db.query(Agent).filter(
            Agent.id == agent_id,
            Agent.tenant_id == safe_tid
        ).first()
        
        if not agent:
            agent = Agent(id=agent_id, pool=pool, tenant_id=safe_tid)
            db.add(agent)
            db.flush() # Flush to ensure agent is available for relationships if needed
    
    try:
        metrics = TaskMetrics(
            tenant_id=safe_tid, # Changed from safe_uuid(tenant_id_str) to safe_tid
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
        logger.error(f"OBSERVABILITY_FAILURE [METRICS_RECORDING] task_id={task.id} error='{e}'")
        return None
