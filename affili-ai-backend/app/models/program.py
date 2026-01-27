"""
Program ORM model - represents an affiliate program.
"""

from sqlalchemy import Column, String, Text, DateTime, Boolean, Float, Integer
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.db.base import Base


class Program(Base):
    """Affiliate program model."""
    __tablename__ = "programs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    affiliate_url = Column(String(500), nullable=False)
    commission_rate = Column(Float, nullable=True, default=0.0)
    terms = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<Program(id={self.id}, name={self.name})>"
