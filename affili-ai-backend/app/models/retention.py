"""
Data retention and legal hold models.
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer
from sqlalchemy import UUID
from datetime import datetime
import uuid

from app.db.base import Base

class RetentionRule(Base):
    """Configuration for data retention policies."""
    __tablename__ = "retention_rules"
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(), ForeignKey("tenants.id"), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False) # e.g. "tasks", "audit_logs", "deliveries"
    retention_days = Column(Integer, nullable=False, default=90)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
