"""
Data Retention API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.dependencies import get_current_user, require_roles
from app.models.user import User, UserRole
from app.models.tenant import Tenant
from app.models.retention import RetentionRule
from app.services.retention_service import run_cleanup_for_tenant
from pydantic import BaseModel
from typing import List, Optional
import uuid

router = APIRouter(prefix="/retention", tags=["retention"])

class RetentionRuleCreate(BaseModel):
    entity_type: str
    retention_days: int
    is_active: bool = True

class RetentionRuleResponse(BaseModel):
    id: uuid.UUID
    entity_type: str
    retention_days: int
    is_active: bool

    class Config:
        from_attributes = True

@router.post("/rules", response_model=RetentionRuleResponse,
             dependencies=[Depends(require_roles(UserRole.OWNER, UserRole.ADMIN))])
def create_retention_rule(
    rule_in: RetentionRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create or update a data retention rule."""
    # Check if rule exists
    rule = db.query(RetentionRule).filter(
        RetentionRule.tenant_id == current_user.tenant_id,
        RetentionRule.entity_type == rule_in.entity_type
    ).first()
    
    if rule:
        rule.retention_days = rule_in.retention_days
        rule.is_active = rule_in.is_active
    else:
        rule = RetentionRule(
            id=uuid.uuid4(),
            tenant_id=current_user.tenant_id,
            entity_type=rule_in.entity_type,
            retention_days=rule_in.retention_days,
            is_active=rule_in.is_active
        )
        db.add(rule)
        
    db.commit()
    db.refresh(rule)
    return rule

@router.post("/cleanup", dependencies=[Depends(require_roles(UserRole.OWNER, UserRole.ADMIN))])
def trigger_cleanup(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Manually trigger data cleanup for the tenant."""
    deleted_count = run_cleanup_for_tenant(db, current_user.tenant_id)
    return {"deleted_count": deleted_count}

@router.post("/legal-hold", dependencies=[Depends(require_roles(UserRole.OWNER, UserRole.ADMIN))])
def set_legal_hold(
    hold: bool,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Set or release legal hold for the tenant."""
    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
    tenant.legal_hold = hold
    db.commit()
    return {"legal_hold": tenant.legal_hold}
