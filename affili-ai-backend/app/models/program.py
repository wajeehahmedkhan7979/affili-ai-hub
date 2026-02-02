"""
Program ORM model - represents an affiliate program.
"""

from sqlalchemy import Column, String, Text, DateTime, Boolean, Float, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.db.base import Base


class Program(Base):
    """Affiliate program model."""
    __tablename__ = "programs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # URLs
    base_url = Column(String(500), nullable=True)  # Original website
    signup_url = Column(String(500), nullable=True)  # Detected signup URL
    affiliate_url = Column(String(500), nullable=False)  # Legacy/manual affiliate URL
    
    # Discovery metadata
    source = Column(String(50), default="manual", index=True)  # "discovered", "manual", "api"
    confidence_score = Column(Float, nullable=True)  # 0.0-1.0 for discovered programs
    
    # Program details
    commission_rate = Column(Float, nullable=True, default=0.0)
    terms = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<Program(id={self.id}, name={self.name})>"
