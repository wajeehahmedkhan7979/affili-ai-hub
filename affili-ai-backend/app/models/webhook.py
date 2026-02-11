"""
Webhook models for event streaming.
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Integer, JSON
from sqlalchemy import UUID
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
import uuid

from app.db.base import Base

class WebhookConfig(Base):
    """Configuration for outbound webhooks."""
    __tablename__ = "webhook_configs"
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(), ForeignKey("tenants.id"), nullable=False, index=True)
    url = Column(String(500), nullable=False)
    secret = Column(String(255), nullable=False) # For HMAC signing
    event_types = Column(JSON().with_variant(JSONB, "postgresql"), nullable=False) # e.g. ["task.completed", "task.failed"]
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class WebhookDelivery(Base):
    """Log of webhook delivery attempts."""
    __tablename__ = "webhook_deliveries"
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(), ForeignKey("tenants.id"), nullable=False, index=True)
    config_id = Column(UUID(), ForeignKey("webhook_configs.id"), nullable=False)
    event_type = Column(String(50), nullable=False)
    payload = Column(JSON().with_variant(JSONB, "postgresql"), nullable=False)
    status_code = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    success = Column(Boolean, default=False)
    attempt_count = Column(Integer, default=1)
    delivered_at = Column(DateTime, default=datetime.utcnow)
