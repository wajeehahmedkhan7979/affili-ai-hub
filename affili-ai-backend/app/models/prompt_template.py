"""
Prompt Template model for versioned AI prompts.
"""

from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, Index
from app.core.time import utcnow
from app.db.uuid_type import UUID
from sqlalchemy.dialects.postgresql import JSONB, JSON
from datetime import datetime
import uuid

from app.db.base import Base


class PromptTemplate(Base):
    """
    Stores versioned prompt templates for LLM operations.
    """
    __tablename__ = "prompt_templates"
    
    __table_args__ = (
        Index("ix_prompt_name_version", "name", "version", unique=True),
    )
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)  # e.g., "field_prediction"
    version = Column(Integer, nullable=False, default=1)
    
    content = Column(Text, nullable=False)  # The actual template string
    
    # Model configuration for this version
    config = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    # e.g., {"model": "gemini-1.5-flash", "temperature": 0.1, "max_tokens": 512}
    
    is_active = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    def __repr__(self) -> str:
        return f"<PromptTemplate(name='{self.name}', version={self.version}, active={self.is_active})>"