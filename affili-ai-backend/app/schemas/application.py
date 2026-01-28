"""Pydantic schemas for Application model."""

from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime
import uuid


class ApplicationBase(BaseModel):
    """Base application schema."""
    program_id: uuid.UUID
    user_email: str
    user_data: Optional[str] = None

    @field_validator("user_email")
    @classmethod
    def validate_user_email(cls, v: str) -> str:
        # Minimal validation without adding the optional email-validator dependency.
        v = (v or "").strip()
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Invalid email address")
        return v


class ApplicationCreate(ApplicationBase):
    """Schema for creating an application."""
    # These are required to build the Playwright payload for APPLY_PROGRAM.
    name: str
    website: str


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
