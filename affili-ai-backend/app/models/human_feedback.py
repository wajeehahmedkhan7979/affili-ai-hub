"""
Human Feedback model for learning from corrections.

Allows operators to correct AI predictions, building a feedback loop
that improves RAG accuracy over time.
"""

from sqlalchemy import Column, String, DateTime, Text, Float, ForeignKey, Enum as SQLEnum, Boolean
from app.core.time import utcnow
from app.db.uuid_type import UUID
from sqlalchemy.dialects.postgresql import JSONB, JSON
from datetime import datetime
import uuid
import enum

from app.db.base import Base


class FeedbackVerdict(str, enum.Enum):
    """Verdict on AI prediction quality."""
    CORRECT = "CORRECT"
    WRONG = "WRONG"
    PARTIAL = "PARTIAL"  # Prediction was close but needed adjustment


class HumanFeedback(Base):
    """
    Track human corrections to AI predictions for learning.
    
    Tenant-scoped: all queries must filter by tenant_id.
    """
    __tablename__ = "human_feedback"
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(), ForeignKey("tenants.id"), nullable=False, index=True)
    task_id = Column(UUID(), ForeignKey("tasks.id"), nullable=True, index=True)
    program_id = Column(UUID(), ForeignKey("programs.id"), nullable=True, index=True)
    
    # Field information
    field_label = Column(Text, nullable=False, index=True)
    field_type = Column(String(50), nullable=False)
    
    # AI prediction
    predicted_value = Column(Text, nullable=True)
    prediction_confidence = Column(Float, nullable=True)
    prediction_source = Column(String(50), nullable=True)  # "rag", "heuristic", "llm"
    
    # Human correction
    corrected_value = Column(Text, nullable=False)
    verdict = Column(SQLEnum(FeedbackVerdict), nullable=False, index=True)
    
    # Operator information
    corrected_by = Column(UUID(), ForeignKey("users.id"), nullable=False)
    correction_notes = Column(Text, nullable=True)
    
    # Whether this feedback has been processed (stored to embeddings)
    processed = Column(Boolean, default=False, index=True)
    processed_at = Column(DateTime, nullable=True)
    
    # Additional context
    extra_metadata = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=utcnow, index=True)
    
    def __repr__(self) -> str:
        return f"<HumanFeedback(id={self.id}, label='{self.field_label}', verdict={self.verdict})>"