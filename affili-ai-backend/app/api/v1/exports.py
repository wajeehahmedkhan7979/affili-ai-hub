"""
Export API endpoints.
Phase 7.5
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.export_job import ExportJob, ExportStatus
from app.services.export_service import create_export_job, process_export_job
from app.api.dependencies import verify_tenant, require_roles
from app.models.user import UserRole
from app.core.tenant import get_tenant_id
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uuid
import os

router = APIRouter(prefix="/exports", tags=["exports"], dependencies=[Depends(verify_tenant)])


class ExportRequest(BaseModel):
    export_type: str  # tasks_csv, metrics_json
    filters: Optional[Dict[str, Any]] = None


class ExportResponse(BaseModel):
    id: uuid.UUID
    export_type: str
    status: str
    created_at: Any
    
    class Config:
        from_attributes = True


@router.post("", response_model=ExportResponse, 
             dependencies=[Depends(require_roles(UserRole.OWNER, UserRole.ADMIN))])
def request_export(
    req: ExportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Request a new export job."""
    if req.export_type not in ["tasks_csv", "metrics_json"]:
        raise HTTPException(status_code=400, detail="Invalid export type")
        
    tenant_id = uuid.UUID(get_tenant_id())
    
    job = create_export_job(db, tenant_id, req.export_type, req.filters)
    
    # Run in background (simple async for MVP)
    background_tasks.add_task(process_export_job, db, job.id)
    
    return job


@router.get("/{export_id}", response_model=ExportResponse,
            dependencies=[Depends(require_roles(UserRole.OWNER, UserRole.ADMIN))])
def get_export_status(
    export_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Get status of an export job."""
    tenant_id = uuid.UUID(get_tenant_id())
    job = db.query(ExportJob).filter(
        ExportJob.id == export_id,
        ExportJob.tenant_id == tenant_id
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Export job not found")
        
    return job


@router.get("/{export_id}/download",
            dependencies=[Depends(require_roles(UserRole.OWNER, UserRole.ADMIN))])
def download_export(
    export_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Download the exported file."""
    tenant_id = uuid.UUID(get_tenant_id())
    job = db.query(ExportJob).filter(
        ExportJob.id == export_id,
        ExportJob.tenant_id == tenant_id
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Export job not found")
        
    if job.status != ExportStatus.COMPLETED or not job.file_path:
        raise HTTPException(status_code=400, detail="Export not ready")
        
    if not os.path.exists(job.file_path):
        raise HTTPException(status_code=500, detail="File missing on server")
        
    return FileResponse(
        path=job.file_path, 
        filename=os.path.basename(job.file_path),
        media_type='application/octet-stream'
    )
