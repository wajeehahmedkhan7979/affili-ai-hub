"""
Task ORM model - represents work items for agents to execute.
"""

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, Enum as SQLEnum, Integer, Index, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid
import enum

from app.db.base import Base


class TaskType(str, enum.Enum):
    """Task type enumeration."""
    DISCOVER_PROGRAM = "DISCOVER_PROGRAM"
    APPLY_PROGRAM = "APPLY_PROGRAM"
    PUBLISH_OFFER = "PUBLISH_OFFER"


class TaskStatus(str, enum.Enum):
    """Task status enumeration."""
    PENDING = "PENDING"
    CLAIMED = "CLAIMED"
    RUNNING = "RUNNING"
    PAUSED_FOR_CAPTCHA = "PAUSED_FOR_CAPTCHA"
    RESUMED = "RESUMED"
    SUBMITTED = "SUBMITTED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Task(Base):
    """Agent task model."""
    __tablename__ = "tasks"
    
    __table_args__ = (
        Index("ix_tasks_tenant_status", "tenant_id", "status"),
        Index("ix_tasks_pool_status", "agent_pool", "status"),
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    task_type = Column(SQLEnum(TaskType), nullable=False, index=True)
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING, index=True)
    # Use JSON with JSONB variant for Postgres performance
    payload = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    result = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    agent_id = Column(String(255), nullable=True, index=True)
    agent_pool = Column(String(100), nullable=True, index=True, default="default")
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    logs = Column(Text, nullable=True)
    screenshot_url = Column(String(500), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    claimed_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    last_heartbeat = Column(DateTime, nullable=True)
    
    def __repr__(self) -> str:
        return f"<Task(id={self.id}, type={self.task_type}, status={self.status})>"
