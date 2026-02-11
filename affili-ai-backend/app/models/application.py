"""
Application ORM model - user application to an affiliate program.
"""

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, Enum as SQLEnum, JSON
from sqlalchemy import UUID
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
import uuid
import enum

from app.db.base import Base


class ApplicationStatus(str, enum.Enum):
    """Application status enumeration."""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    COMPLETED = "COMPLETED"


class Application(Base):
    """User application to an affiliate program."""
    __tablename__ = "applications"
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(), ForeignKey("tenants.id"), nullable=False, index=True)
    program_id = Column(UUID(), ForeignKey("programs.id"), nullable=False, index=True)
    user_email = Column(String(255), nullable=False, index=True)
    user_data = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    status = Column(SQLEnum(ApplicationStatus), default=ApplicationStatus.PENDING, index=True)
    agent_status = Column(String(50), default="IDLE", index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<Application(id={self.id}, program_id={self.program_id}, status={self.status})>"
