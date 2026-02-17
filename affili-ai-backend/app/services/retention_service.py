"""
Data retention service for automated cleanup.
"""
from sqlalchemy.orm import Session
from sqlalchemy import delete, and_
from datetime import datetime, timedelta
import uuid

from app.core.time import utcnow
from app.models.retention import RetentionRule
from app.models.tenant import Tenant
from app.models.task import Task
from app.models.webhook import WebhookDelivery
from app.models.metrics import TaskMetrics
from app.models.audit_log import AuditLog

def run_cleanup_for_tenant(db: Session, tenant_id: uuid.UUID):
    """Run data cleanup for a specific tenant based on their rules."""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant or tenant.legal_hold:
        return 0 # No cleanup during legal hold

    rules = db.query(RetentionRule).filter(
        RetentionRule.tenant_id == tenant_id,
        RetentionRule.is_active == True
    ).all()
    
    deleted_count = 0
    for rule in rules:
        cutoff = utcnow() - timedelta(days=rule.retention_days)
        
        if rule.entity_type == "tasks":
            # Only delete terminal tasks
            stmt = delete(Task).where(
                and_(
                    Task.tenant_id == tenant_id,
                    Task.created_at < cutoff,
                    Task.status.in_(["COMPLETED", "FAILED"])
                )
            )
            res = db.execute(stmt)
            deleted_count += res.rowcount
            
        elif rule.entity_type == "webhook_deliveries":
            stmt = delete(WebhookDelivery).where(
                and_(
                    WebhookDelivery.tenant_id == tenant_id,
                    WebhookDelivery.delivered_at < cutoff
                )
            )
            res = db.execute(stmt)
            deleted_count += res.rowcount

        elif rule.entity_type == "audit_logs":
            stmt = delete(AuditLog).where(
                and_(
                    AuditLog.tenant_id == tenant_id,
                    AuditLog.created_at < cutoff
                )
            )
            res = db.execute(stmt)
            deleted_count += res.rowcount
            
    db.commit()
    return deleted_count

def run_system_cleanup(db: Session):
    """Run cleanup for all tenants."""
    tenants = db.query(Tenant).filter(Tenant.is_active == True).all()
    total = 0
    for t in tenants:
        total += run_cleanup_for_tenant(db, t.id)
    return total