"""
Tenant runtime flags model for persistent kill-switch and governance controls.

Provides production-grade distributed kill-switch that works across multiple
backend instances.
"""

from sqlalchemy import Column, String, DateTime, Text, Boolean, ForeignKey, Integer
from sqlalchemy import UUID
from datetime import datetime
import uuid

from app.db.base import Base


class TenantRuntimeFlag(Base):
    """
    Persistent runtime flags for tenant-level governance controls.
    
    Primary use case: Distributed kill-switch for AI operations.
    """
    __tablename__ = "tenant_runtime_flags"
    
    tenant_id = Column(UUID(), ForeignKey("tenants.id"), primary_key=True)
    
    # AI Kill-switch
    ai_disabled = Column(Boolean, nullable=False, default=False, index=True)
    disable_reason = Column(Text, nullable=True)
    disabled_at = Column(DateTime, nullable=True)
    disabled_by = Column(UUID(), ForeignKey("users.id"), nullable=True)
    
    # Governance Controls
    max_tasks_per_program = Column(Integer, nullable=False, default=10)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<TenantRuntimeFlag(tenant_id={self.tenant_id}, ai_disabled={self.ai_disabled})>"
