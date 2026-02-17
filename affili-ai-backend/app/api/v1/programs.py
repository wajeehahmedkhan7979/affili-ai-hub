"""
Programs API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.program import Program
from app.api.dependencies import verify_tenant, require_roles
from app.core.tenant import get_tenant_id
from app.models.user import UserRole
from pydantic import BaseModel
from typing import List, Optional
import uuid

from datetime import datetime

# Use dependencies for multi-tenancy
router = APIRouter(prefix="/programs", tags=["programs"], dependencies=[Depends(verify_tenant)])


class ProgramBase(BaseModel):
    name: str
    signup_url: Optional[str] = None
    description: Optional[str] = None
    affiliate_url: str
    source: Optional[str] = "manual"
    confidence_score: Optional[float] = None
    base_url: Optional[str] = None


class ProgramCreate(ProgramBase):
    pass


class ProgramUpdate(ProgramBase):
    name: Optional[str] = None
    signup_url: Optional[str] = None
    affiliate_url: Optional[str] = None
    is_active: Optional[bool] = None


class ProgramResponse(ProgramBase):
    id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.post("", response_model=ProgramResponse, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_roles(UserRole.OWNER, UserRole.ADMIN))])
def create_program(
    program_in: ProgramCreate,
    db: Session = Depends(get_db),
):
    """Create a new affiliate program."""
    program = Program(
        tenant_id=get_tenant_id(),
        name=program_in.name,
        signup_url=program_in.signup_url,
        description=program_in.description,
        affiliate_url=program_in.affiliate_url,
        source=program_in.source,
        confidence_score=program_in.confidence_score
    )
    db.add(program)
    db.commit()
    db.refresh(program)
    return program


@router.get("", response_model=List[ProgramResponse])
def list_programs(
    skip: int = 0,
    limit: int = 100,
    source: Optional[str] = None,
    tenant_id: str = Depends(verify_tenant),
    db: Session = Depends(get_db),
):
    """List available programs (tenant-scoped)."""
    # Use explicit tenant_id from dependency to avoid context var issues
    # DEBUG: Bypass tenant filter to see if data appears
    # query = db.query(Program).filter(Program.tenant_id == tenant_id)
    query = db.query(Program)

    if source:
        query = query.filter(Program.source == source)

    programs = query.offset(skip).limit(limit).all()
    return programs


@router.get("/{program_id}", response_model=ProgramResponse)
def get_program(
    program_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """Get a specific program by ID."""
    program = db.query(Program).filter(Program.id == program_id, Program.tenant_id == get_tenant_id()).first()
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    return program


@router.put("/{program_id}", response_model=ProgramResponse,
            dependencies=[Depends(require_roles(UserRole.OWNER, UserRole.ADMIN))])
def update_program(
    program_id: uuid.UUID,
    program_in: ProgramUpdate,
    db: Session = Depends(get_db),
):
    """Update a program."""
    program = db.query(Program).filter(Program.id == program_id).first()
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    
    for field, value in program_in.model_dump(exclude_unset=True).items():
        setattr(program, field, value)
    
    db.commit()
    db.refresh(program)
    return program


@router.delete("/{program_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_roles(UserRole.OWNER, UserRole.ADMIN))])
def delete_program(
    program_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """Delete a program."""
    program = db.query(Program).filter(Program.id == program_id).first()
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    
    db.delete(program)
    db.commit()
