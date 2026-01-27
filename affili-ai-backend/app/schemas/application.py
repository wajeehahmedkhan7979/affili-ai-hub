"""Pydantic schemas for Application model."""

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
import uuid


class ApplicationBase(BaseModel):
    """Base application schema."""
    program_id: uuid.UUID
    user_email: str
    user_data: Optional[str] = None


class ApplicationCreate(ApplicationBase):
    """Schema for creating an application."""
    pass


class ApplicationStatusUpdate(BaseModel):
    """Schema for updating application status."""
    status: str


class ApplicationResponse(ApplicationBase):
    """Schema for application response."""
    id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
