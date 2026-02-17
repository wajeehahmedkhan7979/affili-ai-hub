"""
Operator Action Log model for audit trail of human interventions.

Tracks every manual action taken by operators on tasks and system.
"""

from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Enum as SQLEnum
from app.core.time import utcnow
from app.db.uuid_type import UUID
from sqlalchemy.dialects.postgresql import JSONB, JSON
from datetime import datetime
import uuid
import enum

from app.db.base import Base


class OperatorActionType(str, enum.Enum):
    """Types of operator actions."""
    RESUME_TASK = "RESUME_TASK"
    CANCEL_TASK = "CANCEL_TASK"
    MANUAL_OVERRIDE = "MANUAL_OVERRIDE"
    FEEDBACK_SUBMITTED = "FEEDBACK_SUBMITTED"
    KILLSWITCH_ENABLED = "KILLSWITCH_ENABLED"
    KILLSWITCH_DISABLED = "KILLSWITCH_DISABLED"
    QUOTA_ADJUSTED = "QUOTA_ADJUSTED"


class OperatorActionLog(Base):
    """
    Audit trail of all human operator actions.
    
    Required for compliance, debugging, and incident response.
    """
    __tablename__ = "operator_action_log"
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(), ForeignKey("tenants.id"), nullable=False, index=True)
    operator_id = Column(UUID(), ForeignKey("users.id"), nullable=False, index=True)
    task_id = Column(UUID(), ForeignKey("tasks.id"), nullable=True, index=True)
    
    # Action details
    action = Column(SQLEnum(OperatorActionType), nullable=False, index=True)
    reason = Column(Text, nullable=True)
    
    # Additional context
    extra_metadata = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, default=utcnow, index=True)
    
    def __repr__(self) -> str:
        return f"<OperatorActionLog(id={self.id}, action={self.action}, operator={self.operator_id})>"