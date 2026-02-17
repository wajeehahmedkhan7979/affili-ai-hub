"""
Usage metrics model for billing and analytics.
"""

from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, Date, UniqueConstraint
from app.core.time import utcnow
from app.db.uuid_type import UUID
from datetime import datetime
import uuid

from app.db.base import Base


class TenantUsage(Base):
    """
    aggregated usage metrics per tenant per day.
    """
    __tablename__ = "tenant_usage"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(), ForeignKey("tenants.id"), nullable=False, index=True)

    date = Column(Date, nullable=False, index=True)

    # Counters
    tasks_created = Column(Integer, default=0)
    tasks_completed = Column(Integer, default=0)
    tasks_failed = Column(Integer, default=0)

    agent_minutes = Column(Float, default=0.0)  # duration_seconds / 60
    captcha_events = Column(Integer, default=0)

    created_at = Column(DateTime, default=utcnow)

    __table_args__ = (
        UniqueConstraint("tenant_id", "date", name="uix_tenant_date"),
    )

    def __repr__(self) -> str:
        return f"<TenantUsage(tenant_id={self.tenant_id}, date={self.date}, tasks={self.tasks_created})>"