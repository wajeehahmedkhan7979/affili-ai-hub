"""
Agent model for reputation tracking.
"""

from sqlalchemy import Column, String, DateTime, Integer, Float, ForeignKey, Index
from sqlalchemy import UUID
from datetime import datetime

from app.db.base import Base


class Agent(Base):
    """Agent reputation and health tracking."""
    __tablename__ = "agents"
    
    __table_args__ = (
        Index("ix_agents_tenant_pool", "tenant_id", "pool"),
    )
    
    id = Column(String(255), primary_key=True)  # agent_id
    tenant_id = Column(UUID(), ForeignKey("tenants.id"), nullable=False, index=True)
    pool = Column(String(100), default="default", index=True)
    
    # Task counters
    total_tasks = Column(Integer, default=0)
    successful_tasks = Column(Integer, default=0)
    failed_tasks = Column(Integer, default=0)
    captcha_count = Column(Integer, default=0)
    timeout_count = Column(Integer, default=0)
    
    # Health score (0-100)
    health_score = Column(Float, default=100.0)
    
    # Timestamps
    last_seen = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<Agent(id={self.id}, pool={self.pool}, health={self.health_score})>"
