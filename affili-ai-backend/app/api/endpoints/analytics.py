"""
Analytics API.
Phase 14: UX & Operator Experience v2

Exposes aggregated governance and health metrics for the Operator Dashboard.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from datetime import datetime, timedelta, date
from typing import Dict, Any, List
import uuid

from app.core.time import utcnow
from app.db.session import get_db
from app.core.tenant import get_tenant_id_dependency
from app.models.task import Task, TaskStatus
from app.models.usage import TenantUsage
from app.models.llm_usage_log import LLMUsageLog
from app.models.prompt_template import PromptTemplate
from app.services.cost_governance import cost_governance

router = APIRouter()

@router.get("/governance", response_model=Dict[str, Any])
def get_governance_metrics(
    tenant_id: str = Depends(get_tenant_id_dependency),
    db: Session = Depends(get_db)
):
    """
    Get governance status (killswitch, budget, queue).
    Used for the top-level status bar in the dashboard.
    """
    tenant_uuid = uuid.UUID(tenant_id)
    today = date.today()
    
    # 1. Killswitch Status
    killswitch_active = cost_governance.is_tenant_disabled(db, tenant_uuid)
    
    # 2. Budget Usage
    usage = db.query(TenantUsage).filter(
        TenantUsage.tenant_id == tenant_uuid,
        TenantUsage.date == today
    ).first()
    
    daily_spend = float(usage.total_cost) if usage else 0.0
    daily_budget = 50.0  # Default pilot budget, should fetch from config/DB
    
    # 3. Queue Depth (Pending Tasks)
    queue_depth = db.query(func.count(Task.id)).filter(
        Task.tenant_id == tenant_uuid,
        Task.status == TaskStatus.PENDING
    ).scalar()
    
    # 4. Active Workers (Approximation via CLAIMED/RUNNING tasks)
    active_workers = db.query(func.count(Task.id)).filter(
        Task.tenant_id == tenant_uuid,
        Task.status.in_([TaskStatus.CLAIMED, TaskStatus.RUNNING])
    ).scalar()
    
    return {
        "killswitch_active": killswitch_active,
        "daily_spend": daily_spend,
        "daily_budget": daily_budget,
        "queue_depth": queue_depth,
        "active_workers": active_workers
    }


@router.get("/throughput", response_model=Dict[str, Any])
def get_throughput_metrics(
    window_minutes: int = Query(60, ge=5, le=1440),
    tenant_id: str = Depends(get_tenant_id_dependency),
    db: Session = Depends(get_db)
):
    """
    Get task throughput metrics.
    Used for the 'Tasks per Minute' chart.
    """
    tenant_uuid = uuid.UUID(tenant_id)
    cutoff = utcnow() - timedelta(minutes=window_minutes)
    
    # 1. Tasks per minute (Histogram)
    # Note: Requires Postgres date_trunc, using generic SQL for compatibility
    # Group by minute
    try:
        # Postgres optimized query
        if db.bind.dialect.name == "postgresql":
            history_query = text("""
                SELECT 
                    date_trunc('minute', completed_at) as minute,
                    count(*) as count
                FROM tasks
                WHERE tenant_id = :tenant_id
                AND completed_at >= :cutoff
                AND status IN ('COMPLETED', 'SUCCESS', 'FAILED')
                GROUP BY minute
                ORDER BY minute ASC
            """)
            result = db.execute(history_query, {
                "tenant_id": tenant_uuid, 
                "cutoff": cutoff
            }).fetchall()
            
            # Formatter for chart
            history = [{"timestamp": row[0], "count": row[1]} for row in result]
        else:
            # SQLite fallback (no date_trunc)
            history = [] 
    except Exception:
        history = []

    # 2. Overall Success Rate (Window)
    total_in_window = db.query(func.count(Task.id)).filter(
        Task.tenant_id == tenant_uuid,
        Task.completed_at >= cutoff
    ).scalar()
    
    success_in_window = db.query(func.count(Task.id)).filter(
        Task.tenant_id == tenant_uuid,
        Task.completed_at >= cutoff,
        Task.status.in_([TaskStatus.COMPLETED, TaskStatus.SUCCESS])
    ).scalar()
    
    success_rate = (success_in_window / total_in_window) if total_in_window > 0 else 1.0
    
    return {
        "window_minutes": window_minutes,
        "total_processed": total_in_window,
        "success_rate": round(success_rate, 4),
        "history": history
    }


@router.get("/health", response_model=Dict[str, Any])
def get_system_health(
    tenant_id: str = Depends(get_tenant_id_dependency),
    db: Session = Depends(get_db)
):
    """
    Get system health distribution.
    Used for 'Error Distribution' donut chart.
    """
    tenant_uuid = uuid.UUID(tenant_id)
    cutoff = utcnow() - timedelta(hours=24)
    
    # Error distribution by type (using error_message substring or generic status)
    # Simple version: Status distribution
    status_counts = db.query(
        Task.status, func.count(Task.id)
    ).filter(
        Task.tenant_id == tenant_uuid,
        Task.updated_at >= cutoff
    ).group_by(Task.status).all()
    
    distribution = {status.value: count for status, count in status_counts}
    
    # Recent failures
    recent_failures = db.query(Task).filter(
        Task.tenant_id == tenant_uuid,
        Task.status == TaskStatus.FAILED,
        Task.updated_at >= cutoff
    ).order_by(Task.updated_at.desc()).limit(5).all()
    
    formatted_failures = [
        {
            "id": str(task.id),
            "error": task.error_message,
            "timestamp": task.updated_at
        }
        for task in recent_failures
    ]
    
    return {
        "status_distribution": distribution,
        "recent_failures": formatted_failures
    }


@router.get("/ai", response_model=Dict[str, Any])
def get_ai_analytics(
    window_days: int = Query(7, ge=1, le=30),
    tenant_id: str = Depends(get_tenant_id_dependency),
    db: Session = Depends(get_db)
):
    """
    Get AI performance analytics (confidence, latency, cost by version).
    """
    tenant_uuid = uuid.UUID(tenant_id)
    cutoff = utcnow() - timedelta(days=window_days)
    
    # 1. Average Confidence & Latency
    metrics = db.query(
        func.avg(LLMUsageLog.confidence).label("avg_confidence"),
        func.avg(LLMUsageLog.latency_ms).label("avg_latency"),
        func.count(LLMUsageLog.id).label("total_calls")
    ).filter(
        LLMUsageLog.tenant_id == tenant_uuid,
        LLMUsageLog.created_at >= cutoff
    ).one()
    
    # 2. Distribution by Prompt Version
    version_stats = db.query(
        PromptTemplate.name.label("name"),
        PromptTemplate.version.label("version"),
        func.count(LLMUsageLog.id).label("calls"),
        func.avg(LLMUsageLog.confidence).label("avg_confidence"),
        func.avg(LLMUsageLog.latency_ms).label("avg_latency")
    ).join(
        LLMUsageLog, LLMUsageLog.prompt_version_id == PromptTemplate.id
    ).filter(
        LLMUsageLog.tenant_id == tenant_uuid,
        LLMUsageLog.created_at >= cutoff
    ).group_by(PromptTemplate.name, PromptTemplate.version).all()
    
    formatted_versions = [
        {
            "prompt_name": row.name,
            "version": row.version,
            "calls": row.calls,
            "avg_confidence": round(float(row.avg_confidence), 4) if row.avg_confidence else 0,
            "avg_latency_ms": round(float(row.avg_latency), 2) if row.avg_latency else 0
        }
        for row in version_stats
    ]
    
    return {
        "avg_confidence": round(float(metrics.avg_confidence), 4) if metrics.avg_confidence else 0,
        "avg_latency_ms": round(float(metrics.avg_latency), 2) if metrics.avg_latency else 0,
        "total_calls": metrics.total_calls,
        "version_performance": formatted_versions
    }