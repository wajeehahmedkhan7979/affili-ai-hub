"""
User model for RBAC.
"""

from sqlalchemy import Column, String, Boolean, DateTime, Integer, Enum as SQLEnum, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
import enum

from app.db.base import Base


class UserRole(str, enum.Enum):
    """User roles for RBAC."""
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    OPERATOR = "OPERATOR"
    VIEWER = "VIEWER"


class User(Base):
    """User model scoped to tenant."""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    email = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False)
    hashed_password = Column(String(255), nullable=True)
    refresh_token_version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Ensure email is unique per tenant
    __table_args__ = (
        UniqueConstraint('tenant_id', 'email', name='uix_tenant_email'),
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
