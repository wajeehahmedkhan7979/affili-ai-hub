"""
Response Pool ORM model - stores Q&A pairs for vector search.
"""

from sqlalchemy import Column, String, DateTime, Text, Float, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid

from app.db.base import Base


class ResponsePool(Base):
    """Response pool for Q&A storage and similarity search."""
    __tablename__ = "response_pool"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question = Column(Text, nullable=False, index=True)
    answer = Column(Text, nullable=False)
    category = Column(String(100), nullable=True, index=True)
    # Vector field for embeddings (1536 dims for OpenAI) - stored as JSONB for performance in Postgres
    embedding = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    relevance_score = Column(Float, nullable=True, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<ResponsePool(id={self.id}, category={self.category})>"
