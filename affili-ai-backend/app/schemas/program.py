"""Pydantic schemas for Program model."""

from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime
import uuid


class ProgramBase(BaseModel):
    """Base program schema."""
    name: str
    description: Optional[str] = None
    affiliate_url: str
    commission_rate: Optional[float] = 0.0
    terms: Optional[str] = None
    is_active: bool = True


class ProgramCreate(ProgramBase):
    """Schema for creating a program."""
    pass


class ProgramUpdate(BaseModel):
    """Schema for updating a program."""
    name: Optional[str] = None
    description: Optional[str] = None
    affiliate_url: Optional[str] = None
    commission_rate: Optional[float] = None
    terms: Optional[str] = None
    is_active: Optional[bool] = None


class ProgramResponse(ProgramBase):
    """Schema for program response."""
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
