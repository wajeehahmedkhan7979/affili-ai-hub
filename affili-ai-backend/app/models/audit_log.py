"""
Audit Log model for security and compliance.
Phase 7.4
"""

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Integer, Enum as SQLEnum, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.base import Base
import uuid
import enum
from datetime import datetime


class AuditEventType(str, enum.Enum):
    """Types of audit events."""
    TASK_CREATED = "TASK_CREATED"
    TASK_EXECUTED = "TASK_EXECUTED"
    AGENT_CLAIMED = "AGENT_CLAIMED"
    TASK_FAILED = "TASK_FAILED"
    CAPTCHA_PAUSED = "CAPTCHA_PAUSED"
    CREDENTIAL_CREATED = "CREDENTIAL_CREATED"
    ADMIN_ACTION = "ADMIN_ACTION"
    PROGRAM_CREATED = "PROGRAM_CREATED"
    PROGRAM_UPDATED = "PROGRAM_UPDATED"
    LOGIN_ATTEMPT = "LOGIN_ATTEMPT"
    RBAC_DENIED = "RBAC_DENIED"


class AuditLog(Base):
    """
    Immutable audit log entry.
    Tracks who did what, when, and where.
    """
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), index=True, nullable=False)
    
    event_type = Column(SQLEnum(AuditEventType), nullable=False, index=True)
    
    # Actor (Who)
    actor_type = Column(String(50), nullable=False)  # user, agent, system
    actor_id = Column(String(255), nullable=False)
    actor_email = Column(String(255), nullable=True) # specialized for users
    
    # Resource (What)
    resource_type = Column(String(50), nullable=True)  # task, program
    resource_id = Column(String(255), nullable=True)
    
    # Details
    details = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self) -> str:
        return f"<AuditLog({self.event_type}, actor={self.actor_email}, resource={self.resource_type})>"
