"""Pydantic schemas for Task model."""

from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import uuid


class TaskBase(BaseModel):
    """Base task schema."""
    task_type: str
    payload: Optional[Dict[str, Any]] = None


class TaskCreate(TaskBase):
    """Schema for creating a task."""
    pass


class TaskUpdate(BaseModel):
    """Schema for updating a task."""
    status: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    logs: Optional[str] = None
    screenshot_url: Optional[str] = None
    error_message: Optional[str] = None


class TaskClaimRequest(BaseModel):
    """Schema for claiming a task."""
    agent_id: str


class TaskPollRequest(BaseModel):
    """Schema for agent polling tasks."""
    client_id: str
    capabilities: Optional[list[str]] = None


class TaskResponse(TaskBase):
    """Schema for task response."""
    id: uuid.UUID
    status: str
    result: Optional[Dict[str, Any]] = None
    agent_id: Optional[str] = None
    retry_count: int
    max_retries: int
    logs: Optional[str] = None
    screenshot_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    claimed_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
