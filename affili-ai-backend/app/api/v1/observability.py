"""
Observability and Metrics API.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.api.dependencies import get_current_user, require_roles
from app.models.user import User, UserRole
from app.models.task import Task, TaskStatus
from app.models.metrics import TaskMetrics
from app.models.usage import TenantUsage
from datetime import datetime, timedelta
import uuid

router = APIRouter(prefix="/observability", tags=["observability"])

@router.get("/metrics/overview", dependencies=[Depends(require_roles(UserRole.OWNER, UserRole.ADMIN))])
def get_metrics_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get high-level system performance metrics for the tenant."""
    # 1. Success Rate (Last 24h)
    yesterday = datetime.utcnow() - timedelta(days=1)
    
    total_tasks = db.query(Task).filter(
        Task.tenant_id == current_user.tenant_id,
        Task.created_at >= yesterday
    ).count()
    
    completed_tasks = db.query(Task).filter(
        Task.tenant_id == current_user.tenant_id,
        Task.status == "COMPLETED",
        Task.created_at >= yesterday
    ).count()
    
    success_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    # 2. Average Duration
    avg_duration = db.query(func.avg(TaskMetrics.duration_seconds)).filter(
        TaskMetrics.tenant_id == current_user.tenant_id,
        TaskMetrics.success == True
    ).scalar() or 0
    
    # 3. Task distribution by type
    type_stats = db.query(Task.task_type, func.count(Task.id)).filter(
        Task.tenant_id == current_user.tenant_id
    ).group_by(Task.task_type).all()
    
    # 4. Agent performance (minutes used)
    total_usage = db.query(func.sum(TenantUsage.agent_minutes)).filter(
        TenantUsage.tenant_id == current_user.tenant_id
    ).scalar() or 0

    return {
        "success_rate_24h": round(success_rate, 2),
        "avg_duration_seconds": round(avg_duration, 2),
        "total_usage_minutes": total_usage,
        "tasks_by_type": {str(t): c for t, c in type_stats}
    }

from sqlalchemy import func, text
...
@router.get("/health/diagnostics")
def get_detailed_health(db: Session = Depends(get_db)):
    """Advanced health diagnostics (Database, Connectivity)."""
    try:
        # DB Ping
        db.execute(text("SELECT 1"))
        db_status = "UP"
    except Exception as e:
        db_status = f"DOWN: {str(e)}"
        
    return {
        "status": "UP" if db_status == "UP" else "DEGRADED",
        "components": {
            "database": db_status,
            "system_time": datetime.utcnow().isoformat()
        }
    }
