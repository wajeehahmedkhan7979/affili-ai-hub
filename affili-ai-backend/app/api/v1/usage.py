"""
Usage API endpoint.
Phase 7.3
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import extract
from app.db.session import get_db
from app.models.usage import TenantUsage
from app.api.dependencies import verify_tenant, require_roles
from app.models.user import UserRole
from app.core.tenant import get_tenant_id
from datetime import date, datetime
from typing import Dict, Any, List
import uuid

router = APIRouter(prefix="/usage", tags=["usage"], dependencies=[Depends(verify_tenant)])


@router.get("", dependencies=[Depends(require_roles(UserRole.OWNER, UserRole.ADMIN))])
def get_usage(
    year: int = None,
    month: int = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get aggregated usage metrics for the current tenant.
    Defaults to current month if not specified.
    """
    today = date.today()
    tenant_id_str = get_tenant_id()
    
    if not year:
        year = today.year
    if not month:
        month = today.month
        
    # Get daily records for the specified month
    usage_records = db.query(TenantUsage).filter(
        TenantUsage.tenant_id == uuid.UUID(tenant_id_str),
        extract('year', TenantUsage.date) == year,
        extract('month', TenantUsage.date) == month
    ).order_by(TenantUsage.date).all()
    
    # Aggregate
    totals = {
        "tasks_created": sum(u.tasks_created for u in usage_records),
        "tasks_completed": sum(u.tasks_completed for u in usage_records),
        "tasks_failed": sum(u.tasks_failed for u in usage_records),
        "agent_minutes": round(sum(u.agent_minutes for u in usage_records), 2),
        "captcha_events": sum(u.captcha_events for u in usage_records)
    }
    
    # Breakdowns
    daily_breakdown = []
    for u in usage_records:
        daily_breakdown.append({
            "date": u.date.isoformat(),
            "tasks_created": u.tasks_created,
            "tasks_completed": u.tasks_completed,
            "tasks_failed": u.tasks_failed,
            "agent_minutes": round(u.agent_minutes, 2),
            "captcha_events": u.captcha_events
        })
        
    return {
        "tenant_id": tenant_id_str,
        "period": f"{year}-{month:02d}",
        "totals": totals,
        "daily_breakdown": daily_breakdown
    }
