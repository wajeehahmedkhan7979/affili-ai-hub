"""
Billing models for plan and subscription management.
"""
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Enum as SQLEnum, Float, Boolean
from sqlalchemy import UUID
from datetime import datetime
import uuid
import enum

from app.db.base import Base

class BillingStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    SOFT_LIMIT = "SOFT_LIMIT"
    SUSPENDED = "SUSPENDED"

class BillingPlan(Base):
    """Available billing plans (Free/Pro/Enterprise)."""
    __tablename__ = "billing_plans"
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), nullable=False, unique=True)
    task_limit = Column(Integer, default=10) # per month
    minute_limit = Column(Integer, default=60) # per month
    is_active = Column(Boolean, default=True)

class TenantBilling(Base):
    """Tenant-specific billing status and assigned plan."""
    __tablename__ = "tenant_billing"
    
    tenant_id = Column(UUID(), ForeignKey("tenants.id"), primary_key=True)
    plan_id = Column(UUID(), ForeignKey("billing_plans.id"), nullable=False)
    status = Column(SQLEnum(BillingStatus), default=BillingStatus.ACTIVE)
    cycle_start = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<TenantBilling(tenant_id={self.tenant_id}, status={self.status})>"
