"""
Audit Service for logging system events.
Phase 7.4
"""

from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog, AuditEventType
from app.core.tenant import get_tenant_id
from typing import Dict, Any, Optional
import uuid
import json


def log_audit_event(
    db: Session,
    event_type: AuditEventType,
    actor_type: str,
    actor_id: str,
    actor_email: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    tenant_id: Optional[str] = None,
) -> AuditLog:
    """
    Create an immutable audit log entry.
    
    If tenant_id is not provided, it attempts to get it from context.
    """
    if not tenant_id:
        tenant_id = get_tenant_id()
        
    # If still no tenant_id (e.g. system background task without context), 
    # we might use a default or raise error. For now, assume context or arg.
    if not tenant_id:
        # Fallback or error - but for now let's convert to UUID if present
        # If None, it will fail DB constraint (NOT NULL).
        pass

    log_entry = AuditLog(
        tenant_id=uuid.UUID(tenant_id),
        event_type=event_type,
        actor_type=actor_type,
        actor_id=actor_id,
        actor_email=actor_email,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details
    )
    
    db.add(log_entry)
    # We commit immediately for audit logs usually, or let caller handle transaction?
    # Audit logs should ideally be reliable. 
    # But if caller transaction fails, audit log might also roll back (which is correct for "action wasn't performed").
    # If we want "attempted action" logging, we'd need separate transaction.
    # For this phase: same transaction.
    
    return log_entry
