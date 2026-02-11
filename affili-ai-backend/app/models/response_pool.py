"""
Response Pool ORM model - stores Q&A pairs for vector search.
"""

from app.db.base import Base
from sqlalchemy import Column, String, Float, DateTime, Text, JSON, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from app.db.uuid_type import UUID
from pgvector.sqlalchemy import Vector
import uuid
from datetime import datetime

class ResponsePool(Base):
    __tablename__ = "response_pool"
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(), ForeignKey("tenants.id"), nullable=False, index=True)
    question = Column(Text, nullable=False, index=True)
    answer = Column(Text, nullable=False)
    category = Column(String(100), nullable=True, index=True)
    # Use Vector(384) for all-MiniLM-L6-v2
    embedding = Column(Vector(384), nullable=True)
    # Trust & Verification (v1.1)
    trust_score = Column(Float, nullable=False, default=1.0)
    is_verified = Column(Boolean, nullable=False, default=False)
    relevance_score = Column(Float, nullable=True, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<ResponsePool(id={self.id}, category={self.category})>"
