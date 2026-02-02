"""
Task metrics model for SLA tracking.
"""

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Float, Integer, Index
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.db.base import Base


class TaskMetrics(Base):
    """Metrics for task execution - used for SLA tracking and reporting."""
    __tablename__ = "task_metrics"
    
    __table_args__ = (
        Index("ix_task_metrics_tenant_created", "tenant_id", "created_at"),
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), index=True, nullable=False)
    
    # Task details
    program_name = Column(String(255), index=True, nullable=True)
    task_type = Column(String(50), index=True, nullable=False)
    agent_id = Column(String(255), index=True, nullable=True)
    agent_pool = Column(String(100), index=True, nullable=True)
    
    # Performance metrics
    duration_seconds = Column(Float, nullable=True)
    success = Column(Boolean, nullable=False)
    
    # Failure tracking
    failure_type = Column(String(50), nullable=True, index=True)
    captcha_detected = Column(Boolean, default=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self) -> str:
        return f"<TaskMetrics(task_id={self.task_id}, success={self.success}, duration={self.duration_seconds}s)>"
