"""Pydantic schemas for ResponsePool model."""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid


class ResponsePoolBase(BaseModel):
    """Base response pool schema."""
    question: str
    answer: str
    category: Optional[str] = None


class ResponsePoolCreate(ResponsePoolBase):
    """Schema for creating a response."""
    embedding: Optional[List[float]] = None


class ResponsePoolUpdate(BaseModel):
    """Schema for updating a response."""
    question: Optional[str] = None
    answer: Optional[str] = None
    category: Optional[str] = None
    embedding: Optional[List[float]] = None


class ResponsePoolResponse(ResponsePoolBase):
    """Schema for response pool response."""
    id: uuid.UUID
    embedding: Optional[List[float]] = None
    relevance_score: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SearchRequest(BaseModel):
    """Schema for similarity search request."""
    query: str
    limit: int = 10
    threshold: float = 0.7
