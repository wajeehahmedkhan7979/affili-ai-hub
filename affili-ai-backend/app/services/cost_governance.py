"""
Cost and safety governance service.

Implements:
- Per-tenant LLM quota enforcement
- Per-task max LLM calls
- Tenant kill-switch
- Cost tracking
- Alert thresholds
"""

from sqlalchemy.orm import Session
from app.core.time import utcnow
from app.models.tenant import Tenant
from app.core.logging import logger
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import uuid


# Global kill-switch registry (in-memory, shared across workers)
# In production, use Redis for distributed state
_TENANT_KILLSWITCHES: Dict[str, bool] = {}


class CostGovernance:
    """
    Cost and safety controls for AI operations.
    """
    
    def __init__(
        self,
        default_daily_llm_quota: int = 1000,
        default_max_llm_per_task: int = 10
    ):
        self.default_daily_llm_quota = default_daily_llm_quota
        self.default_max_llm_per_task = default_max_llm_per_task
    
    def check_llm_quota(
        self,
        db: Session,
        tenant_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        Check if tenant has remaining LLM quota for today.
        
        Returns:
            {
                "allowed": bool,
                "remaining": int,
                "quota": int,
                "used_today": int
            }
        """
        # Check kill-switch first (PERSISTENT)
        if self.is_tenant_disabled(db, tenant_id):
            logger.warning(f"Tenant {tenant_id} is disabled via kill-switch")
            return {
                "allowed": False,
                "remaining": 0,
                "quota": 0,
                "used_today": 0,
                "reason": "TENANT_DISABLED"
            }
        
        # Get tenant's LLM usage today
        used_today = self._get_llm_usage_today(db, tenant_id)
        quota = self._get_tenant_llm_quota(db, tenant_id)
        remaining = max(0, quota - used_today)
        
        allowed = remaining > 0
        
        if not allowed:
            logger.warning(f"Tenant {tenant_id} exceeded daily LLM quota: {used_today}/{quota}")
        
        return {
            "allowed": allowed,
            "remaining": remaining,
            "quota": quota,
            "used_today": used_today
        }
    
    def check_task_llm_limit(
        self,
        task_id: uuid.UUID,
        current_calls: int
    ) -> Dict[str, Any]:
        """
        Check if task has exceeded max LLM calls.
        
        Args:
            task_id: Task UUID
            current_calls: Number of LLM calls made so far
            
        Returns:
            {
                "allowed": bool,
                "max_calls": int,
                "current_calls": int
            }
        """
        max_calls = self.default_max_llm_per_task
        allowed = current_calls < max_calls
        
        if not allowed:
            logger.warning(f"Task {task_id} exceeded max LLM calls: {current_calls}/{max_calls}")
        
        return {
            "allowed": allowed,
            "max_calls": max_calls,
            "current_calls": current_calls,
            "remaining": max(0, max_calls - current_calls)
        }
    
    def check_program_task_limit(
        self,
        db: Session,
        tenant_id: uuid.UUID,
        program_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        Check if program has exceeded its active task limit.
        """
        from app.models.task import Task, TaskStatus
        from app.models.tenant_runtime_flag import TenantRuntimeFlag
        
        # Get limit from tenant flags
        flag = db.query(TenantRuntimeFlag).filter(TenantRuntimeFlag.tenant_id == tenant_id).first()
        limit = flag.max_tasks_per_program if flag else 10
        
        # Count active tasks for this program
        active_count = db.query(Task).filter(
            Task.tenant_id == tenant_id,
            Task.program_id == program_id,
            Task.status.in_([TaskStatus.PENDING, TaskStatus.CLAIMED, TaskStatus.RUNNING, TaskStatus.PAUSED_FOR_CAPTCHA])
        ).count()
        
        allowed = active_count < limit
        
        if not allowed:
            logger.warning(f"Program {program_id} exceeded active task limit: {active_count}/{limit}")
            
        return {
            "allowed": allowed,
            "active_count": active_count,
            "limit": limit
        }
    
    def record_llm_call(
        self,
        db: Session,
        tenant_id: uuid.UUID,
        task_id: Optional[uuid.UUID],
        tokens_used: int,
        cost_usd: float,
        model: str = "gemini-1.5-flash",
        operation: Optional[str] = None,
        prompt_version_id: Optional[uuid.UUID] = None,
        confidence: Optional[float] = None,
        latency_ms: Optional[int] = None
    ):
        """
        Record an LLM API call for cost tracking (PERSISTENT).
        
        Args:
            db: Database session
            tenant_id: Tenant UUID
            task_id: Optional task UUID
            tokens_used: Number of tokens consumed
            cost_usd: Cost in USD
            model: Model name
            operation: Operation type (e.g., "field_prediction")
        """
        from app.models.llm_usage_log import LLMUsageLog
        
        log_entry = LLMUsageLog(
            tenant_id=tenant_id,
            task_id=task_id,
            model=model,
            tokens_used=tokens_used,
            cost_usd=cost_usd,
            operation=operation,
            prompt_version_id=prompt_version_id,
            confidence=confidence,
            latency_ms=latency_ms
        )
        
        try:
            db.add(log_entry)
            db.commit()
            logger.info(f"LLM call recorded: tenant={tenant_id}, task={task_id}, tokens={tokens_used}, cost=${cost_usd:.4f}")
        except Exception as e:
            db.rollback()
            logger.warning(f"Failed to record LLM call: {e}")
    
    def enable_tenant_killswitch(self, db: Session, tenant_id: uuid.UUID, reason: str, disabled_by: uuid.UUID):
        """
        Disable all AI operations for a tenant (kill-switch).
        
        PERSISTENT: Uses database, works across all backend instances.
        
        Args:
            db: Database session
            tenant_id: Tenant UUID to disable
            reason: Reason for disabling (for audit)
            disabled_by: User UUID who activated kill-switch
        
        Use in emergencies (runaway costs, abuse, etc.).
        """
        from app.models.tenant_runtime_flag import TenantRuntimeFlag
        
        flag = db.query(TenantRuntimeFlag).filter(
            TenantRuntimeFlag.tenant_id == tenant_id
        ).first()
        
        if not flag:
            flag = TenantRuntimeFlag(
                tenant_id=tenant_id,
                ai_disabled=True,
                disable_reason=reason,
                disabled_at=utcnow(),
                disabled_by=disabled_by
            )
            db.add(flag)
        else:
            flag.ai_disabled = True
            flag.disable_reason = reason
            flag.disabled_at = utcnow()
            flag.disabled_by = disabled_by
        
        db.commit()
        
        # Kill-switch Recovery: Cleanup active tasks
        self.cleanup_disabled_tenant_tasks(db, tenant_id, reason)
        
        logger.critical(f"GOVERNANCE_ACTION [KILL-SWITCH_ACTIVATED] tenant_id={tenant_id} region=all reason='{reason}' operator_id={disabled_by}")
    
    def cleanup_disabled_tenant_tasks(self, db: Session, tenant_id: uuid.UUID, reason: str):
        """
        Cancel all active tasks for a disabled tenant.
        """
        from app.models.task import Task, TaskStatus
        from sqlalchemy import text
        
        # Use raw SQL to avoid selecting non-existent columns (program_id, operator_confidence)
        # compatible with v1.1 frozen schema
        sql = text("""
            SELECT id
            FROM tasks
            WHERE tenant_id = :tenant_id
            AND status IN (:pending, :claimed, :running, :paused)
        """)
        
        result_rows = db.execute(sql, {
            'tenant_id': str(tenant_id),
            'pending': TaskStatus.PENDING.value,
            'claimed': TaskStatus.CLAIMED.value,
            'running': TaskStatus.RUNNING.value,
            'paused': TaskStatus.PAUSED_FOR_CAPTCHA.value
        }).fetchall()
        
        if not result_rows:
            return
        
        # Update using raw SQL to avoid ORM column selection issues
        # PostgreSQL uses || for string concatenation
        update_sql = text("""
            UPDATE tasks
            SET status = :failed, error_message = :error_message, logs = COALESCE(logs, '') || :log_suffix
            WHERE tenant_id = :tenant_id
            AND status IN (:pending, :claimed, :running, :paused)
        """)
        
        error_msg = f"Task canceled: {reason} (Tenant Kill-switch Active)"
        log_suffix = f"\n[{utcnow()}] KILL-SWITCH: {reason}"
        
        db.execute(update_sql, {
            'failed': TaskStatus.FAILED.value,
            'error_message': error_msg,
            'log_suffix': log_suffix,
            'tenant_id': str(tenant_id),
            'pending': TaskStatus.PENDING.value,
            'claimed': TaskStatus.CLAIMED.value,
            'running': TaskStatus.RUNNING.value,
            'paused': TaskStatus.PAUSED_FOR_CAPTCHA.value
        })
        
        db.commit()
        logger.info(f"GOVERNANCE_ACTION [TASK_PURGE] tenant_id={tenant_id} count={len(result_rows)} reason='Kill-switch active'")
    
    def disable_tenant_killswitch(self, db: Session, tenant_id: uuid.UUID):
        """
        Re-enable AI operations for a tenant.
        
        Args:
            db: Database session
            tenant_id: Tenant UUID to re-enable
        """
        from app.models.tenant_runtime_flag import TenantRuntimeFlag
        
        flag = db.query(TenantRuntimeFlag).filter(
            TenantRuntimeFlag.tenant_id == tenant_id
        ).first()
        
        if flag:
            flag.ai_disabled = False
            flag.disable_reason = None
            db.commit()
            logger.info(f"GOVERNANCE_ACTION [KILL-SWITCH_DEACTIVATED] tenant_id={tenant_id} status=normal")
            db.commit()
            logger.info(f"Kill-switch deactivated for tenant {tenant_id}")
    
    def is_tenant_disabled(self, db: Session, tenant_id: uuid.UUID) -> bool:
        """
        Check if tenant is disabled via kill-switch (persistent check).
        
        Args:
            db: Database session
            tenant_id: Tenant UUID
            
        Returns:
            True if AI operations disabled
        """
        from app.models.tenant_runtime_flag import TenantRuntimeFlag
        
        flag = db.query(TenantRuntimeFlag).filter(
            TenantRuntimeFlag.tenant_id == tenant_id
        ).first()
        
        return flag.ai_disabled if flag else False
    
    def _get_llm_usage_today(
        self,
        db: Session,
        tenant_id: uuid.UUID
    ) -> int:
        """
        Get LLM calls made by tenant today (ACTUAL IMPLEMENTATION).
        """
        from app.models.llm_usage_log import LLMUsageLog
        from sqlalchemy import func
        
        today = utcnow().date()
        
        count = db.query(LLMUsageLog).filter(
            LLMUsageLog.tenant_id == tenant_id,
            func.date(LLMUsageLog.created_at) == today
        ).count()
        
        return count
    
    def _get_tenant_llm_quota(
        self,
        db: Session,
        tenant_id: uuid.UUID
    ) -> int:
        """
        Get tenant's daily LLM quota.
        
        Could be customized per tenant based on billing plan.
        """
        # In production: query tenant's billing plan
        # tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        # return tenant.llm_quota if tenant else self.default_daily_llm_quota
        
        return self.default_daily_llm_quota  # Placeholder


# Singleton instance
cost_governance = CostGovernance()


def check_llm_allowed(
    db: Session,
    tenant_id: uuid.UUID,
    task_id: Optional[uuid.UUID] = None,
    current_task_calls: int = 0
) -> Dict[str, Any]:
    """
    Combined check: tenant quota + task limit + kill-switch.
    
    Returns:
        {
            "allowed": bool,
            "reason": str | None,
            "quota_check": Dict,
            "task_limit_check": Dict | None
        }
    """
    # Check tenant quota
    quota_check = cost_governance.check_llm_quota(db, tenant_id)
    
    if not quota_check["allowed"]:
        return {
            "allowed": False,
            "reason": quota_check.get("reason", "QUOTA_EXCEEDED"),
            "quota_check": quota_check,
            "task_limit_check": None
        }
    
    # Check task limit if task_id provided
    task_limit_check = None
    if task_id:
        task_limit_check = cost_governance.check_task_llm_limit(
            task_id, current_task_calls
        )
        
        if not task_limit_check["allowed"]:
            return {
                "allowed": False,
                "reason": "TASK_LIMIT_EXCEEDED",
                "quota_check": quota_check,
                "task_limit_check": task_limit_check
            }
    
    return {
        "allowed": True,
        "reason": None,
        "quota_check": quota_check,
        "task_limit_check": task_limit_check
    }