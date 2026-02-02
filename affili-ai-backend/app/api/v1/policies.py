"""
Policy API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.dependencies import get_current_user, require_roles
from app.models.user import User, UserRole
from app.models.policy import Policy
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uuid

router = APIRouter(prefix="/policies", tags=["policies"])

class PolicyCreate(BaseModel):
    name: str = "New Policy"
    description: Optional[str] = None
    rules: Dict[str, Any]
    is_active: bool = True

class PolicyResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    rules: Dict[str, Any]
    is_active: bool

    class Config:
        from_attributes = True

@router.post("", response_model=PolicyResponse,
             dependencies=[Depends(require_roles(UserRole.OWNER, UserRole.ADMIN))])
def create_policy(
    policy_in: PolicyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new automation policy."""
    policy = Policy(
        id=uuid.uuid4(),
        tenant_id=current_user.tenant_id,
        name=policy_in.name,
        description=policy_in.description,
        rules=policy_in.rules,
        is_active=policy_in.is_active
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy

@router.get("", response_model=List[PolicyResponse])
def list_policies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all policies for the tenant."""
    return db.query(Policy).filter(Policy.tenant_id == current_user.tenant_id).all()

@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT,
             dependencies=[Depends(require_roles(UserRole.OWNER, UserRole.ADMIN))])
def delete_policy(
    policy_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a policy."""
    policy = db.query(Policy).filter(
        Policy.id == policy_id,
        Policy.tenant_id == current_user.tenant_id
    ).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    db.delete(policy)
    db.commit()
    return None
