"""
Outreach log model for tracking merchant outreach automation.

Stores every outreach attempt for full audit trail and compliance.
"""

from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Enum as SQLEnum
from app.core.time import utcnow
from app.db.uuid_type import UUID
from sqlalchemy.dialects.postgresql import JSONB, JSON
from datetime import datetime
import uuid
import enum

from app.db.base import Base


class OutreachStatus(str, enum.Enum):
    """Outreach response status."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    NO_RESPONSE = "NO_RESPONSE"


class OutreachLog(Base):
    """
    Log every merchant outreach action for full auditability.
    
    Tenant-scoped: all queries must filter by tenant_id.
    """
    __tablename__ = "outreach_logs"
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Merchant details
    merchant_name = Column(String(255), nullable=False, index=True)
    merchant_url = Column(String(500), nullable=False)
    merchant_email = Column(String(255), nullable=True)
    
    # Outreach content
    generated_email = Column(Text, nullable=False)
    email_subject = Column(String(500), nullable=True)
    
    # Delivery info
    sent_at = Column(DateTime, default=utcnow, index=True)
    sent_via = Column(String(50), nullable=True)  # email, contact_form, etc.
    
    # Response tracking
    response_received_at = Column(DateTime, nullable=True)
    response_status = Column(SQLEnum(OutreachStatus), default=OutreachStatus.PENDING, index=True)
    response_text = Column(Text, nullable=True)
    
    # Additional metadata
    extra_metadata = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=utcnow, index=True)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    
    def __repr__(self) -> str:
        return f"<OutreachLog(id={self.id}, merchant='{self.merchant_name}', status={self.response_status})>"