"""
Webhook API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.dependencies import get_current_user, require_roles
from app.models.user import User, UserRole
from app.models.webhook import WebhookConfig, WebhookDelivery
from pydantic import BaseModel, HttpUrl
from typing import List, Optional
import uuid

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

class WebhookCreate(BaseModel):
    url: HttpUrl
    secret: str
    event_types: List[str]

class WebhookResponse(BaseModel):
    id: uuid.UUID
    url: str
    event_types: List[str]
    is_active: bool

    class Config:
        from_attributes = True

@router.post("", response_model=WebhookResponse, 
             dependencies=[Depends(require_roles(UserRole.OWNER, UserRole.ADMIN))])
def create_webhook(
    hook_in: WebhookCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Register a new outbound webhook."""
    hook = WebhookConfig(
        id=uuid.uuid4(),
        tenant_id=current_user.tenant_id,
        url=str(hook_in.url),
        secret=hook_in.secret,
        event_types=hook_in.event_types
    )
    db.add(hook)
    db.commit()
    db.refresh(hook)
    return hook

@router.get("", response_model=List[WebhookResponse])
def list_webhooks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List registered webhooks for the tenant."""
    return db.query(WebhookConfig).filter(WebhookConfig.tenant_id == current_user.tenant_id).all()

@router.delete("/{hook_id}", status_code=status.HTTP_204_NO_CONTENT,
             dependencies=[Depends(require_roles(UserRole.OWNER, UserRole.ADMIN))])
def delete_webhook(
    hook_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a webhook configuration."""
    hook = db.query(WebhookConfig).filter(
        WebhookConfig.id == hook_id,
        WebhookConfig.tenant_id == current_user.tenant_id
    ).first()
    if not hook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    db.delete(hook)
    db.commit()
    return None
