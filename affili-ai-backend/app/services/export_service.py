"""
Export Service for generating reports.
Phase 7.5
"""

import csv
import json
import os
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.core.time import utcnow
from app.models.task import Task
from app.models.usage import TenantUsage
from app.models.export_job import ExportJob, ExportStatus
from app.core.config import get_settings

settings = get_settings()

# Directory for storing exports
EXPORT_DIR = os.path.join(os.getcwd(), "exports")
os.makedirs(EXPORT_DIR, exist_ok=True)


def create_export_job(
    db: Session,
    tenant_id: uuid.UUID,
    export_type: str,
    filters: Optional[Dict[str, Any]] = None
) -> ExportJob:
    """Create a new export job record."""
    job = ExportJob(
        tenant_id=tenant_id,
        export_type=export_type,
        filters=filters,
        status=ExportStatus.PENDING
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def process_export_job(db: Session, job_id: uuid.UUID):
    """
    Process an export job (synchronously for now, or via bg task).
    Generates the file and updates job status.
    """
    job = db.query(ExportJob).filter(ExportJob.id == job_id).first()
    if not job:
        return

    try:
        job.status = ExportStatus.PROCESSING
        db.commit()
        
        filename = f"{job.tenant_id}_{job.export_type}_{utcnow().strftime('%Y%m%d%H%M%S')}"
        file_path = os.path.join(EXPORT_DIR, filename)
        
        if job.export_type == "tasks_csv":
            file_path += ".csv"
            _generate_tasks_csv(db, job.tenant_id, file_path, job.filters)
        elif job.export_type == "metrics_json":
            file_path += ".json"
            _generate_metrics_json(db, job.tenant_id, file_path, job.filters)
        else:
            raise ValueError(f"Unknown export type: {job.export_type}")
            
        job.file_path = file_path
        job.status = ExportStatus.COMPLETED
        job.completed_at = utcnow()
        db.commit()
        
    except Exception as e:
        job.status = ExportStatus.FAILED
        job.error_message = str(e)
        db.commit()
        print(f"Export failed: {e}")


def _generate_tasks_csv(db: Session, tenant_id: uuid.UUID, file_path: str, filters: Optional[Dict] = None):
    """Generate CSV of tasks."""
    query = db.query(Task).filter(Task.tenant_id == tenant_id)
    
    # Apply simple filters
    if filters:
        if filters.get("status"):
            query = query.filter(Task.status == filters["status"])
    
    tasks = query.limit(1000).all() # Cap at 1000 for now
    
    with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['id', 'task_type', 'status', 'agent_id', 'created_at', 'completed_at']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for task in tasks:
            writer.writerow({
                'id': str(task.id),
                'task_type': task.task_type.value if hasattr(task.task_type, 'value') else str(task.task_type),
                'status': task.status,
                'agent_id': task.agent_id,
                'created_at': task.created_at.isoformat() if task.created_at else '',
                'completed_at': task.completed_at.isoformat() if task.completed_at else ''
            })


def _generate_metrics_json(db: Session, tenant_id: uuid.UUID, file_path: str, filters: Optional[Dict] = None):
    """Generate JSON of metrics."""
    query = db.query(TenantUsage).filter(TenantUsage.tenant_id == tenant_id)
    usages = query.order_by(TenantUsage.date).all()
    
    data = []
    for u in usages:
        data.append({
            "date": u.date.isoformat(),
            "tasks_created": u.tasks_created,
            "tasks_completed": u.tasks_completed,
            "tasks_failed": u.tasks_failed,
            "agent_minutes": u.agent_minutes
        })
        
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)