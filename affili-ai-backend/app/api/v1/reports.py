"""
Reports API endpoints for execution transparency.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.models.metrics import TaskMetrics
from app.models.task import Task
from app.models.program import Program
from app.api.dependencies import verify_tenant, require_roles
from app.core.tenant import get_tenant_id
from app.models.user import UserRole
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

router = APIRouter(prefix="/reports", tags=["reports"], dependencies=[Depends(verify_tenant)])


@router.get("/execution", dependencies=[Depends(require_roles(UserRole.OWNER, UserRole.ADMIN))])
def get_execution_report(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get execution summary report (tenant-scoped).
    
    Returns:
    - total_tasks
    - success_count
    - success_rate
    - failure_count
    - captcha_count
    - avg_duration
    - failure_breakdown (by type)
    """
    # Build query
    query = db.query(TaskMetrics).filter(TaskMetrics.tenant_id == get_tenant_id())
    
    # Apply date filters if provided
    if start_date:
        start_dt = datetime.fromisoformat(start_date)
        query = query.filter(TaskMetrics.created_at >= start_dt)
    if end_date:  
        end_dt = datetime.fromisoformat(end_date)
        query = query.filter(TaskMetrics.created_at <= end_dt)
    
    # Get all metrics
    metrics = query.all()
    
    if not metrics:
        return {
            "total_tasks": 0,
            "success_count": 0,
            "success_rate": 0.0,
            "failure_count": 0,
            "captcha_count": 0,
            "avg_duration": 0.0,
            "failure_breakdown": {}
        }
    
    # Calculate aggregates
    total = len(metrics)
    success_count = sum(1 for m in metrics if m.success)
    failure_count = sum(1 for m in metrics if not m.success)
    captcha_count = sum(1 for m in metrics if m.captcha_detected)
    
    # Average duration (only for completed tasks with duration)
    durations = [m.duration_seconds for m in metrics if m.duration_seconds is not None]
    avg_duration = sum(durations) / len(durations) if durations else 0.0
    
    # Failure breakdown
    failure_breakdown = {}
    for m in metrics:
        if m.failure_type:
            failure_breakdown[m.failure_type] = failure_breakdown.get(m.failure_type, 0) + 1
    
    return {
        "total_tasks": total,
        "success_count": success_count,
        "success_rate": round((success_count / total * 100) if total > 0 else 0.0, 2),
        "failure_count": failure_count,
        "captcha_count": captcha_count,
        "avg_duration": round(avg_duration, 2),
        "failure_breakdown": failure_breakdown
    }


@router.get("/programs", dependencies=[Depends(require_roles(UserRole.OWNER, UserRole.ADMIN))])
def get_program_report(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get program-level statistics (tenant-scoped).
    
    Returns metrics grouped by program_name:
    - total_tasks
    - success_rate
    - avg_duration
    - captcha_rate
    """
    # Get metrics grouped by program
    metrics_by_program = {}
    
    metrics = db.query(TaskMetrics).filter(TaskMetrics.tenant_id == get_tenant_id()).all()
    
    for m in metrics:
        prog = m.program_name or "Unknown"
        
        if prog not in metrics_by_program:
            metrics_by_program[prog] = {
                "program_name": prog,
                "total_tasks": 0,
                "successes": 0,
                "captchas": 0,
                "durations": []
            }
        
        metrics_by_program[prog]["total_tasks"] += 1
        if m.success:
            metrics_by_program[prog]["successes"] += 1
        if m.captcha_detected:
            metrics_by_program[prog]["captchas"] += 1
        if m.duration_seconds:
            metrics_by_program[prog]["durations"].append(m.duration_seconds)
    
    # Calculate rates
    result = []
    for prog, data in metrics_by_program.items():
        total = data["total_tasks"]
        avg_dur = sum(data["durations"]) / len(data["durations"]) if data["durations"] else 0.0
        
        result.append({
            "program_name": prog,
            "total_tasks": total,
            "success_rate": round((data["successes"] / total * 100) if total > 0 else 0.0, 2),
            "captcha_rate": round((data["captchas"] / total * 100) if total > 0 else 0.0, 2),
            "avg_duration": round(avg_dur, 2)
        })
    
    return {"programs": result}


@router.get("/discovery", dependencies=[Depends(require_roles(UserRole.OWNER, UserRole.ADMIN))])
def get_discovery_report(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get discovery agent statistics (tenant-scoped).
    
    Returns:
    - total_programs_discovered
    - avg_confidence
    - high_confidence_count (>0.7)
    - source_breakdown
    """
    programs = db.query(Program).filter(
        Program.discovery_source.isnot(None),
        Program.tenant_id == get_tenant_id()
    ).all()
    
    if not programs:
        return {
            "total_programs_discovered": 0,
            "avg_confidence": 0.0,
            "high_confidence_count": 0,
            "source_breakdown": {}
        }
    
    total = len(programs)
    confidences = [p.discovery_confidence for p in programs if p.discovery_confidence is not None]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
    high_confidence = sum(1 for c in confidences if c > 0.7)
    
    # Source breakdown
    source_breakdown = {}
    for p in programs:
        source = p.discovery_source or "Unknown"
        source_breakdown[source] = source_breakdown.get(source, 0) + 1
    
    return {
        "total_programs_discovered": total,
        "avg_confidence": round(avg_confidence, 2),
        "high_confidence_count": high_confidence,
        "source_breakdown": source_breakdown
    }
