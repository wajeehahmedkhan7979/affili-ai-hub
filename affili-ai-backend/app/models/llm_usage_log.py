"""
LLM Usage Log model for persistent cost tracking.

Provides complete audit trail of all LLM API calls with token counts and costs.
"""

from sqlalchemy import Column, String, DateTime, Integer, Numeric, ForeignKey, Index
from sqlalchemy import UUID
from sqlalchemy.dialects.postgresql import JSONB, JSON
from datetime import datetime
import uuid

from app.db.base import Base


class LLMUsageLog(Base):
    """
    Persistent ledger of all LLM API calls.
    
    Critical for cost tracking, auditing, and quota enforcement.
    """
    __tablename__ = "llm_usage_log"
    
    __table_args__ = (
        Index("ix_llm_usage_tenant_created", "tenant_id", "created_at"),
        Index("ix_llm_usage_task", "task_id"),
    )
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(), ForeignKey("tenants.id"), nullable=False, index=True)
    task_id = Column(UUID(), ForeignKey("tasks.id"), nullable=True, index=True)
    
    # LLM details
    model = Column(String(100), nullable=False)  # e.g., "gemini-1.5-flash"
    tokens_used = Column(Integer, nullable=False)
    cost_usd = Column(Numeric(10, 6), nullable=False)  # Up to $9999.999999
    
    # Request context
    operation = Column(String(50), nullable=True)  # "field_prediction", "outreach_email", etc.
    extra_metadata = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self) -> str:
        return f"<LLMUsageLog(id={self.id}, model='{self.model}', tokens={self.tokens_used}, cost=${self.cost_usd})>"
