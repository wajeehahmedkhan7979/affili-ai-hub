"""
Export Job model for asynchronous reporting.
Phase 7.5
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Enum as SQLEnum, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.base import Base
import uuid
import enum
from datetime import datetime


class ExportStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ExportJob(Base):
    """
    Tracks asynchronous export jobs.
    """
    __tablename__ = "export_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), index=True, nullable=False)
    
    export_type = Column(String(50), nullable=False)  # csv, json, zip
    status = Column(SQLEnum(ExportStatus), default=ExportStatus.PENDING, index=True)
    
    filters = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)  # date range, task type, etc
    file_path = Column(String(500), nullable=True) # Local path or S3 URL
    error_message = Column(String(500), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<ExportJob({self.id}, type={self.export_type}, status={self.status})>"
