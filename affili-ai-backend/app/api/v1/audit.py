"""
Audit API endpoints.
Phase 7.4
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db.session import get_db
from app.models.audit_log import AuditLog
from app.api.dependencies import verify_tenant, require_roles
from app.models.user import UserRole
from app.core.tenant import get_tenant_id
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid


class AuditLogResponse(BaseModel):
    id: uuid.UUID
    event_type: str
    actor_type: str
    actor_email: Optional[str]
    resource_type: Optional[str]
    resource_id: Optional[str]
    details: Optional[dict]
    created_at: datetime
    ip_address: Optional[str]

    class Config:
        from_attributes = True


router = APIRouter(prefix="/audit", tags=["audit"], dependencies=[Depends(verify_tenant)])


@router.get("", response_model=List[AuditLogResponse], 
            dependencies=[Depends(require_roles(UserRole.OWNER))])
def get_audit_logs(
    limit: int = 50,
    offset: int = 0,
    event_type: Optional[str] = None,
    actor_email: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get audit logs for the tenant.
    Only OWNER can access.
    """
    tenant_id = get_tenant_id()
    
    query = db.query(AuditLog).filter(AuditLog.tenant_id == uuid.UUID(tenant_id))
    
    if event_type:
        query = query.filter(AuditLog.event_type == event_type)
        
    if actor_email:
        query = query.filter(AuditLog.actor_email == actor_email)
        
    query = query.order_by(desc(AuditLog.created_at))
    
    return query.offset(offset).limit(limit).all()
