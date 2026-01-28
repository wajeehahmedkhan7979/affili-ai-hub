"""
Credential ORM model - stores encrypted API keys and secrets.
"""

from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
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
    meta_data = Column(Text, nullable=True)  # JSON string for unencrypted metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<Credential(id={self.id}, name={self.name}, type={self.credential_type})>"
