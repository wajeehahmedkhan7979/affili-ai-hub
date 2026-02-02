"""
Billing API endpoints.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.billing import BillingPlan, TenantBilling
from app.services.billing_service import get_tenant_billing
from app.models.usage import TenantUsage
import uuid
from datetime import date

router = APIRouter(prefix="/billing", tags=["billing"])

@router.get("/status")
def get_billing_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current plan and usage status for the tenant."""
    billing = get_tenant_billing(db, current_user.tenant_id)
    plan = db.query(BillingPlan).filter(BillingPlan.id == billing.plan_id).first()
    
    # Calculate current usage
    usage_total = db.query(TenantUsage).filter(
        TenantUsage.tenant_id == current_user.tenant_id,
        TenantUsage.date >= billing.cycle_start.date()
    ).all()
    
    total_tasks = sum(u.tasks_created for u in usage_total)
    total_minutes = sum(u.agent_minutes for u in usage_total)
    
    return {
        "plan_name": plan.name if plan else "Unknown",
        "status": billing.status,
        "cycle_start": billing.cycle_start,
        "limits": {
            "task_limit": plan.task_limit if plan else 0,
            "minute_limit": plan.minute_limit if plan else 0
        },
        "usage": {
            "tasks_created": total_tasks,
            "agent_minutes": total_minutes
        }
    }

@router.get("/plans")
def list_available_plans(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all available billing plans."""
    plans = db.query(BillingPlan).filter(BillingPlan.is_active == True).all()
    return plans
