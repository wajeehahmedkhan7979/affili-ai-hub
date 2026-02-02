"""
Applications API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.application import Application, ApplicationStatus
from app.models.program import Program
from app.api.dependencies import verify_tenant, require_roles
from app.core.tenant import get_tenant_id
from app.models.user import UserRole
from pydantic import BaseModel
from typing import List, Optional
import uuid
import json
from app.models.task import TaskType
from app.services.task_dispatcher import create_task

# Use dependencies for multi-tenancy
router = APIRouter(prefix="/applications", tags=["applications"], dependencies=[Depends(verify_tenant)])


class ApplicationCreate(BaseModel):
    program_id: uuid.UUID
    user_email: str
    user_data: Optional[str] = None


class ApplicationResponse(BaseModel):
    id: uuid.UUID
    program_id: uuid.UUID
    user_email: str
    status: str
    
    class Config:
        from_attributes = True


class ApplicationStatusUpdate(BaseModel):
    status: str


@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_roles(UserRole.OWNER, UserRole.ADMIN, UserRole.OPERATOR))])
def create_application(app_in: ApplicationCreate, db: Session = Depends(get_db)):
    """Submit a new application."""
    # Verify program exists and belongs to tenant
    program = db.query(Program).filter(
        Program.id == app_in.program_id,
        Program.tenant_id == uuid.UUID(get_tenant_id())
    ).first()
    
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    
    user_data_obj = {}
    if app_in.user_data:
        # We do not attempt to parse/merge arbitrary JSON here to keep this minimal and robust.
        user_data_obj["user_data_raw"] = app_in.user_data

    application = Application(
        program_id=app_in.program_id,
        user_email=str(app_in.user_email),
        user_data=json.dumps(user_data_obj),
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    
    # Create associated task for the agent
    task_payload = {
        "application_id": str(application.id),
        "program_name": program.name,
        "email": application.user_email,
        "name": app_in.name,
        "website": app_in.website,
    }
    create_task(db, TaskType.APPLY_PROGRAM, task_payload)
    
    return application


@router.get("", response_model=List[ApplicationResponse])
def list_applications(
    skip: int = 0,
    limit: int = 100,
    user_email: str = None,
    status: str = None,
    db: Session = Depends(get_db),
):
    """List all applications."""
    query = db.query(Application)
    if user_email:
        query = query.filter(Application.user_email == user_email)
    if status:
        query = query.filter(Application.status == status)
    return query.offset(skip).limit(limit).all()


@router.get("/{application_id}", response_model=ApplicationResponse)
def get_application(
    application_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """Get a specific application."""
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return application


@router.put("/{application_id}/status", response_model=ApplicationResponse)
def update_application_status(
    application_id: uuid.UUID,
    status_update: ApplicationStatusUpdate,
    db: Session = Depends(get_db),
):
    """Update application status."""
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    application.status = status_update.status
    db.commit()
    db.refresh(application)
    return application
