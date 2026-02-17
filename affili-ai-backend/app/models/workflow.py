"""
ORM models for workflow orchestration.
"""

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, Enum as SQLEnum, Integer, Index, JSON
from sqlalchemy.dialects.postgresql import JSONB
from app.core.time import utcnow
from app.db.uuid_type import UUID
from datetime import datetime
import uuid
import enum

from app.db.base import Base


class WorkflowStatus(str, enum.Enum):
    """Workflow instance status."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class WorkflowDefinition(Base):
    """Blueprint for a multi-step automation."""
    __tablename__ = "workflow_definitions"
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(), ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # The DAG or sequence of steps
    # Example Step: {"id": "step1", "type": "DISCOVER_PROGRAM", "config": {}, "next": "step2"}
    definition = Column(JSON().with_variant(JSONB, "postgresql"), nullable=False)
    
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=utcnow, index=True)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    
    def __repr__(self) -> str:
        return f"<WorkflowDefinition(id={self.id}, name={self.name})>"


class WorkflowInstance(Base):
    """A specific execution of a workflow."""
    __tablename__ = "workflow_instances"
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(), ForeignKey("tenants.id"), nullable=False, index=True)
    definition_id = Column(UUID(), ForeignKey("workflow_definitions.id"), nullable=False, index=True)
    
    status = Column(SQLEnum(WorkflowStatus), default=WorkflowStatus.PENDING, index=True)
    current_step_id = Column(String(100), nullable=True)
    
    # Shared memory between steps
    context = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True, default={})
    
    created_at = Column(DateTime, default=utcnow, index=True)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    def __repr__(self) -> str:
        return f"<WorkflowInstance(id={self.id}, definition_id={self.definition_id}, status={self.status})>"


class WorkflowStepInstance(Base):
    """Link between a WorkflowInstance and a specific Task."""
    __tablename__ = "workflow_step_instances"
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    instance_id = Column(UUID(), ForeignKey("workflow_instances.id"), nullable=False, index=True)
    task_id = Column(UUID(), ForeignKey("tasks.id"), nullable=False, index=True)
    
    # Identifier from the definition's steps
    step_id = Column(String(100), nullable=False)
    
    created_at = Column(DateTime, default=utcnow)
    
    def __repr__(self) -> str:
        return f"<WorkflowStepInstance(instance_id={self.instance_id}, task_id={self.task_id})>"