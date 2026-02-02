"""
Billing service for limit checks and plan management.
"""
from sqlalchemy.orm import Session
import uuid
from datetime import datetime, timedelta

from app.models.billing import BillingPlan, TenantBilling, BillingStatus
from app.models.usage import TenantUsage

def get_tenant_billing(db: Session, tenant_id: uuid.UUID) -> TenantBilling:
    """Get billing info for a tenant or assign default Free plan."""
    billing = db.query(TenantBilling).filter(TenantBilling.tenant_id == tenant_id).first()
    if not billing:
        # Assign Free plan by default
        free_plan = db.query(BillingPlan).filter(BillingPlan.name == "Free").first()
        if not free_plan:
            # Fallback if seed failed
            free_plan = BillingPlan(name="Free", task_limit=10, minute_limit=60)
            db.add(free_plan)
            db.flush()
        
        billing = TenantBilling(
            tenant_id=tenant_id,
            plan_id=free_plan.id,
            status=BillingStatus.ACTIVE,
            cycle_start=datetime.utcnow()
        )
        db.add(billing)
        db.commit()
    return billing

def check_task_limit(db: Session, tenant_id: uuid.UUID) -> bool:
    """Check if tenant can create more tasks based on their plan."""
    billing = get_tenant_billing(db, tenant_id)
    if billing.status == BillingStatus.SUSPENDED:
        return False
        
    plan = db.query(BillingPlan).filter(BillingPlan.id == billing.plan_id).first()
    if not plan:
        return True # or fallback
        
    # Get usage for current cycle (simplified: today for now, but should be cycle-based)
    # The requirement says "Convert usage metrics into billable units".
    # Implementation: Check sum of tasks_created in current cycle.
    
    usage_total = db.query(TenantUsage).filter(
        TenantUsage.tenant_id == tenant_id,
        TenantUsage.date >= billing.cycle_start.date()
    ).all()
    
    total_tasks = sum(u.tasks_created for u in usage_total)
    
    if total_tasks >= plan.task_limit:
        return False
        
    return True
