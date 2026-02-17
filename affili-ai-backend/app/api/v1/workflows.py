"""
API endpoints for workflow orchestration.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import uuid

from app.api.dependencies import get_db, require_roles
from app.models.user import UserRole
from app.core.tenant import get_tenant_id_dependency
from app.services.workflow_service import workflow_service
from app.models.workflow import WorkflowDefinition, WorkflowInstance, WorkflowStatus

router = APIRouter()

@router.post("/definitions", response_model=Dict[str, Any])
def create_workflow_definition(
    name: str,
    definition: Dict[str, Any],
    description: Optional[str] = None,
    tenant_id: str = Depends(get_tenant_id_dependency),
    db: Session = Depends(get_db),
    _ = Depends(require_roles([UserRole.ADMIN, UserRole.OWNER]))
):
    """Create a new workflow blueprint."""
    tenant_uuid = uuid.UUID(tenant_id)
    try:
        wf_def = workflow_service.create_definition(db, tenant_uuid, name, definition, description)
        return {
            "id": str(wf_def.id),
            "name": wf_def.name,
            "created_at": wf_def.created_at.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/definitions", response_model=List[Dict[str, Any]])
def list_workflow_definitions(
    tenant_id: str = Depends(get_tenant_id_dependency),
    db: Session = Depends(get_db)
):
    """List all workflow blueprints for the tenant."""
    tenant_uuid = uuid.UUID(tenant_id)
    definitions = db.query(WorkflowDefinition).filter(
        WorkflowDefinition.tenant_id == tenant_uuid,
        WorkflowDefinition.is_active == True
    ).all()
    
    return [
        {
            "id": str(d.id),
            "name": d.name,
            "description": d.description,
            "created_at": d.created_at.isoformat()
        } for d in definitions
    ]

@router.post("/start/{definition_id}", response_model=Dict[str, Any])
def start_workflow_instance(
    definition_id: uuid.UUID,
    payload: Dict[str, Any] = {},
    tenant_id: str = Depends(get_tenant_id_dependency),
    db: Session = Depends(get_db)
):
    """Trigger a new workflow execution."""
    tenant_uuid = uuid.UUID(tenant_id)
    try:
        instance = workflow_service.start_instance(db, tenant_uuid, definition_id, payload)
        return {
            "id": str(instance.id),
            "status": instance.status,
            "current_step": instance.current_step_id,
            "created_at": instance.created_at.isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/instances/{instance_id}", response_model=Dict[str, Any])
def get_workflow_instance(
    instance_id: uuid.UUID,
    tenant_id: str = Depends(get_tenant_id_dependency),
    db: Session = Depends(get_db)
):
    """Track the progress of a specific workflow execution."""
    tenant_uuid = uuid.UUID(tenant_id)
    instance = db.query(WorkflowInstance).filter(
        WorkflowInstance.id == instance_id,
        WorkflowInstance.tenant_id == tenant_uuid
    ).first()
    
    if not instance:
        raise HTTPException(status_code=404, detail="Workflow instance not found")
        
    return {
        "id": str(instance.id),
        "definition_id": str(instance.definition_id),
        "status": instance.status,
        "current_step": instance.current_step_id,
        "context": instance.context,
        "created_at": instance.created_at.isoformat(),
        "completed_at": instance.completed_at.isoformat() if instance.completed_at else None
    }

@router.get("/instances", response_model=List[Dict[str, Any]])
def list_workflow_instances(
    tenant_id: str = Depends(get_tenant_id_dependency),
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=100)
):
    """List recent workflow executions."""
    tenant_uuid = uuid.UUID(tenant_id)
    instances = db.query(WorkflowInstance).filter(
        WorkflowInstance.tenant_id == tenant_uuid
    ).order_by(WorkflowInstance.created_at.desc()).limit(limit).all()
    
    return [
        {
            "id": str(i.id),
            "definition_id": str(i.definition_id),
            "status": i.status,
            "current_step": i.current_step_id,
            "created_at": i.created_at.isoformat()
        } for i in instances
    ]
