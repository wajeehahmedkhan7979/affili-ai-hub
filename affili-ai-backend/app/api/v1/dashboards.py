"""
Dashboards API for system analytics and metrics.

Provides aggregated metrics for the UI dashboard.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.models.task import Task, TaskStatus, TaskType
from app.models.agent import Agent
from app.models.metrics import TaskMetrics
from app.models.tenant import Tenant
from app.api.dependencies import get_current_user, require_roles
from app.models.user import User, UserRole
from app.core.tenant import get_tenant_id
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import uuid

router = APIRouter(prefix="/dashboards", tags=["dashboards"])


@router.get("/agent-health")
def get_agent_health(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Return agent health scores and task counts.
    
    Useful for monitoring agent pool performance.
    """
    tenant_id = uuid.UUID(get_tenant_id())
    
    agents = db.query(Agent).filter(Agent.tenant_id == tenant_id).all()
    
    agent_stats = []
    for agent in agents:
        # Calculate success rate
        success_rate = 0.0
        if agent.total_tasks > 0:
            success_rate = (agent.successful_tasks / agent.total_tasks) * 100
        
        agent_stats.append({
            "agent_id": agent.id,
            "pool": agent.pool,
            "health_score": agent.health_score,
            "total_tasks": agent.total_tasks,
            "successful_tasks": agent.successful_tasks,
            "failed_tasks": agent.failed_tasks,
            "success_rate": round(success_rate, 2),
            "captcha_count": agent.captcha_count,
            "timeout_count": agent.timeout_count,
            "last_seen": agent.last_seen.isoformat() if agent.last_seen else None,
            "status": "active" if agent.last_seen and (datetime.utcnow() - agent.last_seen).seconds < 300 else "inactive"
        })
    
    return {
        "agents": agent_stats,
        "summary": {
            "total_agents": len(agent_stats),
            "active_agents": sum(1 for a in agent_stats if a["status"] == "active"),
            "avg_health": round(sum(a["health_score"] for a in agent_stats) / len(agent_stats), 2) if agent_stats else 0
        }
    }


@router.get("/task-throughput")
def get_task_throughput(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    days: int = Query(7, ge=1, le=90)
):
    """
    Return task completion rates over time.
    
    Args:
        days: Number of days to look back (1-90)
    """
    tenant_id = uuid.UUID(get_tenant_id())
    since = datetime.utcnow() - timedelta(days=days)
    
    # Query task metrics
    metrics = db.query(
        func.date(TaskMetrics.completed_at).label("date"),
        TaskMetrics.status,
        func.count(TaskMetrics.id).label("count")
    ).filter(
        TaskMetrics.tenant_id == tenant_id,
        TaskMetrics.completed_at >= since
    ).group_by(
        func.date(TaskMetrics.completed_at),
        TaskMetrics.status
    ).order_by(func.date(TaskMetrics.completed_at)).all()
    
    # Format for charting
    throughput_data = {}
    for date, status, count in metrics:
        date_str = date.isoformat()
        if date_str not in throughput_data:
            throughput_data[date_str] = {"completed": 0, "failed": 0}
        
        if status == TaskStatus.COMPLETED:
            throughput_data[date_str]["completed"] = count
        elif status == TaskStatus.FAILED:
            throughput_data[date_str]["failed"] = count
    
    return {
        "data": throughput_data,
        "period": {"start": since.isoformat(), "end": datetime.utcnow().isoformat()}
    }


@router.get("/program-success-rates")
def get_program_success_rates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Return success rates by program type.
    
    Helps identify which affiliate programs have the best automation success.
    """
    tenant_id = uuid.UUID(get_tenant_id())
    
    # Query task metrics grouped by task type (which maps to program)
    metrics = db.query(
        TaskMetrics.task_type,
        TaskMetrics.status,
        func.count(TaskMetrics.id).label("count")
    ).filter(
        TaskMetrics.tenant_id == tenant_id
    ).group_by(
        TaskMetrics.task_type,
        TaskMetrics.status
    ).all()
    
    # Aggregate by program
    program_stats = {}
    for task_type, status, count in metrics:
        if task_type not in program_stats:
            program_stats[task_type] = {"completed": 0, "failed": 0}
        
        if status == TaskStatus.COMPLETED:
            program_stats[task_type]["completed"] = count
        elif status == TaskStatus.FAILED:
            program_stats[task_type]["failed"] = count
    
    # Calculate success rates
    results = []
    for program, stats in program_stats.items():
        total = stats["completed"] + stats["failed"]
        success_rate = (stats["completed"] / total * 100) if total > 0 else 0
        
        results.append({
            "program": program,
            "completed": stats["completed"],
            "failed": stats["failed"],
            "total": total,
            "success_rate": round(success_rate, 2)
        })
    
    # Sort by total descending
    results.sort(key=lambda x: x["total"], reverse=True)
    
    return {"programs": results}


@router.get("/system-overview")
def get_dashboard_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Return high-level system statistics for the UI dashboard.
    Matches frontend expectation: programsFound, pendingApprovals, applicationsSubmitted, connectedAgents
    """
    tenant_id = uuid.UUID(get_tenant_id())
    
    # 1. Programs Found
    from app.models.program import Program
    programs_found = db.query(Program).filter(Program.tenant_id == tenant_id).count()
    
    # 2. Applications Stats
    from app.models.application import Application, ApplicationStatus
    total_apps = db.query(Application).filter(Application.tenant_id == tenant_id).count()
    pending_apps = db.query(Application).filter(
        Application.tenant_id == tenant_id,
        Application.status == ApplicationStatus.PENDING
    ).count()
    
    # 3. Connected Agents (Active in last 5 mins)
    active_agents = db.query(Agent).filter(
        Agent.tenant_id == tenant_id,
        Agent.last_seen >= datetime.utcnow() - timedelta(minutes=5)
    ).count()
    
    return {
        "programsFound": programs_found,
        "pendingApprovals": pending_apps,
        "applicationsSubmitted": total_apps,
        "connectedAgents": active_agents
    }


# === SLA Metrics (Phase U) ===

@router.get("/sla")
def get_sla_metrics(
    days: int = 7,
    db: Session = Depends(get_db)
):
    """
    Get SLA metrics for production monitoring.
    
    Metrics:
    - Mean time to completion (MTTC)
    - Mean time paused (MTP)
    - CAPTCHA frequency
    - Human intervention rate
    """
    since = datetime.utcnow() - timedelta(days=days)
    
    # Get all tasks in period
    tasks = db.query(Task).filter(Task.created_at >= since).all()
    
    if not tasks:
        return {
            "period_days": days,
            "total_tasks": 0,
            "mttr_seconds": 0,
            "captcha_rate": 0.0,
            "human_intervention_rate": 0.0
        }
    
    # Calculate Mean Time To Resolution
    completed_tasks = [t for t in tasks if t.status == "COMPLETED"]
    if completed_tasks:
        resolution_times = [
            (t.updated_at - t.created_at).total_seconds()
            for t in completed_tasks
            if t.updated_at and t.created_at
        ]
        mttr = sum(resolution_times) / len(resolution_times) if resolution_times else 0
    else:
        mttr = 0
    
    # Calculate CAPTCHA rate
    captcha_tasks = [t for t in tasks if t.status == "PAUSED_FOR_CAPTCHA"]
    captcha_rate = len(captcha_tasks) / len(tasks) if tasks else 0.0
    
    # Calculate human intervention rate
    paused_tasks = [
        t for t in tasks
        if t.status.startswith("PAUSED_") or t.status == "FAILED_OPERATOR_CANCEL"
    ]
    intervention_rate = len(paused_tasks) / len(tasks) if tasks else 0.0
    
    return {
        "period_days": days,
        "total_tasks": len(tasks),
        "completed_tasks": len(completed_tasks),
        "mttr_seconds": round(mttr, 2),
        "mttr_minutes": round(mttr / 60, 2),
        "captcha_rate": round(captcha_rate, 3),
        "human_intervention_rate": round(intervention_rate, 3),
        "captcha_count": len(captcha_tasks),
        "intervention_count": len(paused_tasks)
    }


# === Program Risk Scoring (Phase U) ===

@router.get("/programs/{program_id}/risk-score")
def get_program_risk_score(
    program_id: str,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """
    Calculate risk score for a program (0-100).
    
    Higher score = higher risk.
    
    Inputs:
    - CAPTCHA rate (weight: 30%)
    - Failure rate (weight: 40%)
    - Feedback corrections (weight: 20%)
    - Success rate (weight: 10%, inverse)
    """
    program_uuid = uuid.UUID(program_id)
    since = datetime.utcnow() - timedelta(days=days)
    
    # Get all tasks for program
    tasks = db.query(Task).filter(
        and_(
            Task.program_id == program_uuid,
            Task.created_at >= since
        )
    ).all()
    
    if not tasks:
        return {
            "program_id": str(program_id),
            "risk_score": 0,
            "risk_level": "UNKNOWN",
            "reason": "No tasks in period",
            "recommendation": "Enable automation to collect data"
        }
    
    total = len(tasks)
    
    # Calculate component scores
    captcha_count = len([t for t in tasks if t.status == "PAUSED_FOR_CAPTCHA"])
    captcha_rate = captcha_count / total if total > 0 else 0
    
    failed_count = len([t for t in tasks if t.status.startswith("FAILED_")])
    failure_rate = failed_count / total if total > 0 else 0
    
    completed_count = len([t for t in tasks if t.status == "COMPLETED"])
    success_rate = completed_count / total if total > 0 else 0
    
   # Human feedback corrections (placeholder - would query HumanFeedback table)
    correction_rate = 0.0  # TODO: Implement when feedback data available
    
    # Calculate weighted risk score (0-100)
    risk_score = (
        (captcha_rate * 30) +
        (failure_rate * 40) +
        (correction_rate * 20) +
        ((1 - success_rate) * 10)
    )
    
    # Determine risk level
    if risk_score < 20:
        risk_level = "LOW"
        recommendation = "Automation performing well"
    elif risk_score < 50:
        risk_level = "MEDIUM"
        recommendation = "Monitor closely, consider threshold adjustments"
    elif risk_score < 75:
        risk_level = "HIGH"
        recommendation = "Increase human oversight, raise confidence thresholds"
    else:
        risk_level = "CRITICAL"
        recommendation = "Consider disabling automation for this program"
    
    return {
        "program_id": str(program_id),
        "period_days": days,
        "risk_score": round(risk_score, 2),
        "risk_level": risk_level,
        "recommendation": recommendation,
        "metrics": {
            "total_tasks": total,
            "captcha_rate": round(captcha_rate, 3),
            "failure_rate": round(failure_rate, 3),
            "success_rate": round(success_rate, 3),
            "correction_rate": round(correction_rate, 3)
        }
    }
@router.get("/confidence-drift")
def get_confidence_drift(
    days: int = Query(30, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Track mean AI confidence scores over time.
    """
    tenant_id = uuid.UUID(get_tenant_id())
    since = datetime.utcnow() - timedelta(days=days)
    
    # Query tasks with results that have confidence scores
    # This assumes confidence is stored in task.result['confidence']
    tasks = db.query(Task).filter(
        Task.tenant_id == tenant_id,
        Task.created_at >= since,
        Task.status == TaskStatus.COMPLETED
    ).all()
    
    # Group by date
    daily_stats = {}
    for task in tasks:
        if not task.result or "confidence" not in task.result:
            continue
            
        date_str = task.created_at.date().isoformat()
        if date_str not in daily_stats:
            daily_stats[date_str] = []
        daily_stats[date_str].append(float(task.result["confidence"]))
        
    # Calculate means
    drift_data = []
    for date_str in sorted(daily_stats.keys()):
        scores = daily_stats[date_str]
        drift_data.append({
            "date": date_str,
            "mean_confidence": round(sum(scores) / len(scores), 3),
            "sample_size": len(scores)
        })
        
    return {"drift": drift_data}


@router.get("/cost-efficiency")
def get_cost_efficiency(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Calculate cost-per-successful-task (v1.1 Safety Metric).
    """
    tenant_id = uuid.UUID(get_tenant_id())
    
    # Get total cost from usage logs
    from app.models.llm_usage_log import LLMUsageLog
    total_cost = db.query(func.sum(LLMUsageLog.cost_usd)).filter(
        LLMUsageLog.tenant_id == tenant_id
    ).scalar() or 0.0
    
    # Get total completed tasks
    completed_count = db.query(Task).filter(
        Task.tenant_id == tenant_id,
        Task.status == TaskStatus.COMPLETED
    ).count()
    
    cost_per_success = (total_cost / completed_count) if completed_count > 0 else 0.0
    
    return {
        "total_cost_usd": round(total_cost, 4),
        "completed_tasks": completed_count,
        "cost_per_success_usd": round(cost_per_success, 4)
    }
