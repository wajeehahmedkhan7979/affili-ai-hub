"""
Credential ORM model - stores encrypted API keys and secrets.
"""

from sqlalchemy import Column, String, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid

from app.db.base import Base


class Credential(Base):
    """Encrypted credential storage."""
    __tablename__ = "credentials"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    credential_type = Column(String(100), nullable=False)  # gmail, stripe, sendgrid, etc.
    encrypted_value = Column(Text, nullable=False)  # AES-256-GCM encrypted
    meta_data = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<Credential(id={self.id}, name={self.name}, type={self.credential_type})>"
