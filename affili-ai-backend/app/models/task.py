"""
Task ORM model - represents work items for agents to execute.
"""

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, Enum as SQLEnum, Integer
from sqlalchemy.dialects.postgresql import UUID, JSON
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
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_type = Column(SQLEnum(TaskType), nullable=False, index=True)
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING, index=True)
    payload = Column(JSON, nullable=True)  # Task-specific data
    result = Column(JSON, nullable=True)  # Task result/output
    agent_id = Column(String(255), nullable=True, index=True)
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
    
    def __repr__(self) -> str:
        return f"<Task(id={self.id}, type={self.task_type}, status={self.status})>"
