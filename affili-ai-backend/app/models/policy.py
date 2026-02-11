"""
Policy models for automation governance.
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy import UUID
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
import uuid

from app.db.base import Base

class Policy(Base):
    """Governance policies for tenant-scoped automation."""
    __tablename__ = "policies"
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(), ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    # Policy rules: e.g. {"max_tasks_per_day": 100, "allowed_domains": ["*.com"]}
    rules = Column(JSON().with_variant(JSONB, "postgresql"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
