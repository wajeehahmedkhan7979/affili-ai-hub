"""
Policy evaluation service for automation governance.
"""
from sqlalchemy.orm import Session
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.models.policy import Policy
from app.models.usage import TenantUsage

def evaluate_action(
    db: Session,
    tenant_id: uuid.UUID,
    action_type: str,
    context: Dict[str, Any]
) -> (bool, Optional[str]):
    """
    Evaluate if an action is allowed under the tenant's active policies.
    Returns (is_allowed, reason).
    """
    policies = db.query(Policy).filter(
        Policy.tenant_id == tenant_id,
        Policy.is_active == True
    ).all()
    
    for p in policies:
        rules = p.rules
        if not rules:
            continue
            
        # Example 1: Restricted Task Types
        restricted_types = rules.get("restricted_task_types", [])
        if action_type == "create_task" and context.get("task_type") in restricted_types:
            return False, f"Policy '{p.name}' restricts task type: {context.get('task_type')}"
            
        # Example 2: Daily Task Quota (Goverance, not billing)
        max_daily = rules.get("max_tasks_per_day")
        if action_type == "create_task" and max_daily is not None:
            today_usage = db.query(TenantUsage).filter(
                TenantUsage.tenant_id == tenant_id,
                TenantUsage.date == datetime.utcnow().date()
            ).first()
            current_count = today_usage.tasks_created if today_usage else 0
            if current_count >= max_daily:
                return False, f"Policy '{p.name}' daily limit reached: {max_daily}"

    return True, None
