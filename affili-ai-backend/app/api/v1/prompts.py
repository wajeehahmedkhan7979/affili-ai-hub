"""
API endpoints for managing versioned prompt templates.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import uuid

from app.db.session import get_db
from app.api.dependencies import get_current_user, require_roles
from app.models.user import UserRole
from app.models.prompt_template import PromptTemplate
from app.services.prompt_service import prompt_service
from pydantic import BaseModel

router = APIRouter()

class PromptCreate(BaseModel):
    name: str
    content: str
    config: Optional[Dict[str, Any]] = None
    activate: bool = False

class PromptUpdate(BaseModel):
    is_active: bool

class PromptResponse(BaseModel):
    id: uuid.UUID
    name: str
    version: int
    content: str
    config: Optional[Dict[str, Any]]
    is_active: bool
    created_at: Any
    
    class Config:
        from_attributes = True


@router.get("/", response_model=List[PromptResponse])
async def list_prompts(
    db: Session = Depends(get_db),
    current_user = Depends(require_roles([UserRole.ADMIN.value, UserRole.OWNER.value]))
):
    """List all prompt templates and versions."""
    return db.query(PromptTemplate).order_by(
        PromptTemplate.name.asc(), 
        PromptTemplate.version.desc()
    ).all()


@router.post("/", response_model=PromptResponse)
async def create_prompt_version(
    prompt_in: PromptCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles([UserRole.ADMIN.value, UserRole.OWNER.value]))
):
    """Create a new version of a prompt template."""
    return prompt_service.create_prompt_version(
        db=db,
        name=prompt_in.name,
        content=prompt_in.content,
        config=prompt_in.config,
        activate=prompt_in.activate
    )


@router.patch("/{prompt_id}/activate", response_model=PromptResponse)
async def activate_prompt_version(
    prompt_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles([UserRole.ADMIN.value, UserRole.OWNER.value]))
):
    """Activate a specific version of a prompt template."""
    success = prompt_service.activate_version(db, prompt_id)
    if not success:
        raise HTTPException(status_code=404, detail="Prompt version not found")
        
    return db.query(PromptTemplate).filter(PromptTemplate.id == prompt_id).first()


@router.get("/active/{name}", response_model=PromptResponse)
async def get_active_prompt(
    name: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get the currently active version of a prompt."""
    prompt = prompt_service.get_active_prompt(db, name)
    if not prompt:
        raise HTTPException(status_code=404, detail=f"No active prompt found for '{name}'")
    return prompt
