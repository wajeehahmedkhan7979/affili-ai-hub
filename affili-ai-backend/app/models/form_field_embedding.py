"""
Form Field Embedding model for RAG-based form intelligence.
Stores successful form field responses with vector embeddings for similarity search.
"""

from sqlalchemy import Column, String, DateTime, Text, Float, ForeignKey, Index, Integer, JSON
from sqlalchemy import UUID
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
import uuid

from app.db.base import Base

# pgvector import - conditional to support SQLite dev mode
try:
    from pgvector.sqlalchemy import Vector
    PGVECTOR_AVAILABLE = True
except ImportError:
    PGVECTOR_AVAILABLE = False
    # Fallback to TEXT for SQLite compatibility
    Vector = lambda dim: Text


class FormFieldEmbedding(Base):
    """
    Store form field labels and their embeddings for RAG-based field prediction.
    
    This model enables the system to learn from successful form submissions
    and suggest values for similar fields in future automations.
    
    Tenant-scoped: all queries must filter by tenant_id.
    """
    __tablename__ = "form_field_embeddings"
    
    __table_args__ = (
        Index("ix_embeddings_tenant", "tenant_id"),
        Index("ix_embeddings_program", "program_id"),
        Index("ix_embeddings_field_label", "field_label"),
    )
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(), ForeignKey("tenants.id"), nullable=False, index=True)
    program_id = Column(UUID(), ForeignKey("programs.id"), nullable=True, index=True)
    
    # Field metadata
    field_label = Column(Text, nullable=False)  # e.g. "Company Name", "Website URL"
    field_type = Column(String(50), nullable=False)  # text, email, url, select, textarea, etc.
    successful_value = Column(Text, nullable=True)  # Last successful value used
    
    # Embedding vector (384 dimensions for all-MiniLM-L6-v2)
    # Uses pgvector on PostgreSQL, falls back to TEXT on SQLite
    if PGVECTOR_AVAILABLE:
        embedding = Column(Vector(384), nullable=True)
    else:
        embedding = Column(Text, nullable=True)  # Store as JSON string in SQLite
    
    # Usage tracking
    success_count = Column(Integer, default=0)
    last_used_at = Column(DateTime, nullable=True)
    
    # Full form context (stores additional metadata about the form)
    # Use JSONB on PostgreSQL for better performance, fallback to JSON on SQLite
    form_context = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<FormFieldEmbedding(id={self.id}, label='{self.field_label[:30]}', type={self.field_type})>"
