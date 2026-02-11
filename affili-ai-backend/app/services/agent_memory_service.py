"""
Agent memory service - lightweight context tracking for agents.

Implements read-only memory layers:
- Short-term: Current task context
- Long-term: Program-specific success patterns

NO free-form reasoning memory - deterministic only.
"""

from sqlalchemy.orm import Session
from app.models.task import Task
from app.models.form_field_embedding import FormFieldEmbedding
from app.models.metrics import TaskMetrics
from app.core.logging import logger
from typing import Dict, Any, List, Optional
import uuid


class AgentMemory:
    """
    Lightweight agent memory - read-only context tracking.
    
    NOT for free-form AI reasoning - only for deterministic patterns.
    """
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
   
    def get_short_term_context(
        self,
        task: Task
    ) -> Dict[str, Any]:
        """
        Get context for current task.
        
        Returns:
            {
                "task_id": str,
                "task_type": str,
                "program_id": str | None,
                "attempt_number": int,
                "previous_errors": List[str]
            }
        """
        return {
            "task_id": str(task.id),
            "task_type": task.task_type,
            "program_id": str(task.payload.get("program_id")) if task.payload.get("program_id") else None,
            "attempt_number": task.retry_count + 1,
            "previous_errors": self._extract_previous_errors(task)
        }
    
    def get_long_term_patterns(
        self,
        db: Session,
        tenant_id: uuid.UUID,
        program_id: Optional[uuid.UUID],
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get successful patterns for this program.
        
        Returns top-N fields by success count.
        
        Returns:
            {
                "successful_fields": List[Dict],
                "total_successes": int
            }
        """
        query = db.query(FormFieldEmbedding).filter(
            FormFieldEmbedding.tenant_id == tenant_id,
            FormFieldEmbedding.success_count > 0
        )
        
        if program_id:
            query = query.filter(FormFieldEmbedding.program_id == program_id)
        
        embeddings = query.order_by(
            FormFieldEmbedding.success_count.desc()
        ).limit(limit).all()
        
        successful_fields = [
            {
                "field_label": e.field_label,
                "field_type": e.field_type,
                "success_count": e.success_count,
                "last_used": e.last_used_at.isoformat() if e.last_used_at else None
            }
            for e in embeddings
        ]
        
        total_successes = sum(e.success_count for e in embeddings)
        
        return {
            "successful_fields": successful_fields,
            "total_successes": total_successes,
            "program_id": str(program_id) if program_id else None
        }
    
    def _extract_previous_errors(self, task: Task) -> List[str]:
        """Extract error messages from task logs."""
        if not task.error_message:
            return []
        
        # Parse error message (simple split for now)
        errors = [task.error_message]
        return errors
