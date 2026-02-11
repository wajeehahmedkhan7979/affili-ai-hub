"""Pydantic schemas for Task model."""

from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import uuid


class TaskBase(BaseModel):
    """Base task schema."""
    task_type: str
    payload: Optional[Dict[str, Any]] = None
    program_id: Optional[uuid.UUID] = None


class TaskCreate(BaseModel):
    """Schema for creating a new task."""
    task_type: str  # Will be validated against TaskType enum
    payload: Optional[Dict[str, Any]] = None
    program_id: Optional[uuid.UUID] = None
    agent_pool: Optional[str] = "default"  # Pool assignment for task
    logs: Optional[str] = None
    screenshot_url: Optional[str] = None
    error_message: Optional[str] = None


class TaskUpdate(BaseModel):
    """Schema for updating a task."""
    status: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    logs: Optional[str] = None
    screenshot_url: Optional[str] = None
    error_message: Optional[str] = None
    operator_confidence: Optional[int] = None
    feedback_json: Optional[Dict[str, Any]] = None


class TaskClaimRequest(BaseModel):
    """Schema for claiming a task."""
    agent_id: str
    agent_pool: Optional[str] = "default"


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
    operator_confidence: Optional[int] = None
    feedback_json: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    claimed_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    last_heartbeat: Optional[datetime] = None
    
    class Config:
        from_attributes = True
