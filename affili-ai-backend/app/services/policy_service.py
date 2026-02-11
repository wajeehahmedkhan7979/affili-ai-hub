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
    try:
        policies = db.query(Policy).filter(
            Policy.tenant_id == tenant_id,
            Policy.is_active == True
        ).all()
    except Exception as e:
        # If policies table doesn't exist or query fails, skip custom policies
        # but still enforce global safety policies below
        policies = []
    
    for p in policies:
        rules = p.rules
        if not rules:
            continue
            
        # Example 1: Restricted Task Types
        restricted_types = rules.get("restricted_task_types", [])
        if action_type == "create_task" and context.get("task_type") in restricted_types:
            return False, f"Policy '{p.name}' restricts task type: {context.get('task_type')}"
            
        # Example 2: Daily Task Quota (Goverance, not billing)
        # Note: current_count and max_daily are placeholders in v1.1 and may cause NameError
        # max_daily = rules.get("max_daily_tasks", 100)
        # if current_count >= max_daily:
        #    return False, f"Policy '{p.name}' daily limit reached: {max_daily}"

    # === v1.1 GLOBAL SAFETY POLICIES (Hardcoded Enforcement) ===
    
    # 1. No Autonomous Submissions
    if action_type == "submit_application":
        is_human_reviewed = context.get("is_human_reviewed", False)
        if is_human_reviewed is not True:
            return False, "HARD_POLICY: Fully autonomous submissions are disabled in v1.1. Human review required."

    # 2. Site Stability Whitelist (Pilot Restriction)
    if action_type == "create_task" and context.get("task_type") == "APPLY_PROGRAM":
        STABILITY_WHITELIST = ["shareasale.com", "impact.com", "cj.com"]
        program_domain = str(context.get("program_domain", "unknown")).lower()
        if program_domain not in STABILITY_WHITELIST:
            return False, f"HARD_POLICY: Automation on '{program_domain}' is disabled for pilot phase stability."

    return True, None
