"""
Governance API endpoints for operational controls.

Handles:
- Tenant kill-switch activation/deactivaction
- LLM cost dashboards
- Operator audit trails
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
import uuid

from app.db.session import get_db
from app.core.auth import require_roles, get_current_user
from app.models import TenantRuntimeFlag, LLMUsageLog, OperatorActionLog, OperatorActionType
from app.services.cost_governance import cost_governance
from app.core.logging import logger

router = APIRouter(prefix="/governance", tags=["governance"])


# === Request Models ===

class KillSwitchRequest(BaseModel):
    reason: str
    

class CostSummaryRequest(BaseModel):
    days: int = 30
    

# === Kill-Switch Endpoints ===

@router.post("/tenant/{tenant_id}/disable-ai")
def enable_killswitch(
    tenant_id: str,
    request: KillSwitchRequest,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["OWNER", "ADMIN"]))
):
    """
    EMERGENCY: Disable all AI operations for a tenant.
    
    This kill-switch works across all backend instances (persistent).
    
    Required role: OWNER or ADMIN
    """
    tenant_uuid = uuid.UUID(tenant_id)
    
    try:
        cost_governance.enable_tenant_killswitch(
            db=db,
            tenant_id=tenant_uuid,
            reason=request.reason,
            disabled_by=current_user.id
        )
        
        # Log operator action
        log_entry = OperatorActionLog(
            tenant_id=tenant_uuid,
            operator_id=current_user.id,
            action=OperatorActionType.KILLSWITCH_ENABLED,
            reason=request.reason
        )
        db.add(log_entry)
        db.commit()
        
        logger.critical(f"Kill-switch ENABLED by {current_user.email} for tenant {tenant_id}: {request.reason}")
        
        return {
            "status": "disabled",
            "tenant_id": str(tenant_id),
            "reason": request.reason,
            "disabled_at": datetime.utcnow().isoformat(),
            "disabled_by": str(current_user.id)
        }
    except Exception as e:
        logger.error(f"Failed to enable kill-switch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tenant/{tenant_id}/enable-ai")
def disable_killswitch(
    tenant_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["OWNER", "ADMIN"]))
):
    """
    Re-enable AI operations for a tenant.
    
    Required role: OWNER or ADMIN
    """
    tenant_uuid = uuid.UUID(tenant_id)
    
    try:
        cost_governance.disable_tenant_killswitch(db=db, tenant_id=tenant_uuid)
        
        # Log operator action
        log_entry = OperatorActionLog(
            tenant_id=tenant_uuid,
            operator_id=current_user.id,
            action=OperatorActionType.KILLSWITCH_DISABLED,
            reason="AI operations re-enabled"
        )
        db.add(log_entry)
        db.commit()
        
        logger.info(f"Kill-switch DISABLED by {current_user.email} for tenant {tenant_id}")
        
        return {
            "status": "enabled",
            "tenant_id": str(tenant_id),
            "enabled_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to disable kill-switch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tenant/{tenant_id}/status")
def get_ai_status(
    tenant_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["OWNER", "ADMIN", "OPERATOR"]))
):
    """
    Check if AI operations are enabled or disabled for a tenant.
    """
    tenant_uuid = uuid.UUID(tenant_id)
    
    flag = db.query(TenantRuntimeFlag).filter(
        TenantRuntimeFlag.tenant_id == tenant_uuid
    ).first()
    
    if not flag or not flag.ai_disabled:
        return {
            "tenant_id": str(tenant_id),
            "ai_enabled": True,
            "status": "OPERATIONAL"
        }
    
    return {
        "tenant_id": str(tenant_id),
        "ai_enabled": False,
        "status": "DISABLED",
        "reason": flag.disable_reason,
        "disabled_at": flag.disabled_at.isoformat() if flag.disabled_at else None
    }


# === LLM Cost Endpoints ===

@router.get("/llm-costs")
def get_llm_costs(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["OWNER", "ADMIN"]))
):
    """
    Get LLM cost summary for current tenant.
    
    Returns total cost, token usage, and breakdown by model.
    """
    tenant_id = current_user.tenant_id
    since = datetime.utcnow() - timedelta(days=days)
    
    # Query  LLM usage
    logs = db.query(LLMUsageLog).filter(
        and_(
            LLMUsageLog.tenant_id == tenant_id,
            LLMUsageLog.created_at >= since
        )
    ).all()
    
    if not logs:
        return {
            "tenant_id": str(tenant_id),
            "period_days": days,
            "total_calls": 0,
            "total_tokens": 0,
            "total_cost_usd": 0.0,
            "models": {}
        }
    
    # Aggregate metrics
    total_tokens = sum(log.tokens_used for log in logs)
    total_cost = sum(float(log.cost_usd) for log in logs)
    
    # Breakdown by model
    models = {}
    for log in logs:
        if log.model not in models:
            models[log.model] = {"calls": 0, "tokens": 0, "cost_usd": 0.0}
        models[log.model]["calls"] += 1
        models[log.model]["tokens"] += log.tokens_used
        models[log.model]["cost_usd"] += float(log.cost_usd)
    
    return {
        "tenant_id": str(tenant_id),
        "period_days": days,
        "total_calls": len(logs),
        "total_tokens": total_tokens,
        "total_cost_usd": round(total_cost, 4),
        "models": models
    }


# === Operator Audit Trail ===

@router.get("/audit/operator-actions")
def get_operator_actions(
    days: int = 7,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["OWNER", "ADMIN"]))
):
    """
    Get audit trail of operator actions.
    
    Returns recent human interventions for compliance/debugging.
    """
    tenant_id = current_user.tenant_id
    since = datetime.utcnow() - timedelta(days=days)
    
    actions = db.query(OperatorActionLog).filter(
        and_(
            OperatorActionLog.tenant_id == tenant_id,
            OperatorActionLog.created_at >= since
        )
    ).order_by(OperatorActionLog.created_at.desc()).limit(limit).all()
    
    return {
        "tenant_id": str(tenant_id),
        "period_days": days,
        "total_actions": len(actions),
        "actions": [
            {
                "id": str(action.id),
                "operator_id": str(action.operator_id),
                "task_id": str(action.task_id) if action.task_id else None,
                "action": action.action.value,
                "reason": action.reason,
                "created_at": action.created_at.isoformat()
            }
            for action in actions
        ]
    }
