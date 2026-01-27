"""
Programs API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.program import Program
from app.schemas.program import ProgramCreate, ProgramUpdate, ProgramResponse
from typing import List
import uuid

router = APIRouter(prefix="/programs", tags=["programs"])


@router.post("", response_model=ProgramResponse, status_code=status.HTTP_201_CREATED)
def create_program(
    program_in: ProgramCreate,
    db: Session = Depends(get_db),
):
    """Create a new affiliate program."""
    program = Program(**program_in.model_dump())
    db.add(program)
    db.commit()
    db.refresh(program)
    return program


@router.get("", response_model=List[ProgramResponse])
def list_programs(
    skip: int = 0,
    limit: int = 100,
    is_active: bool = None,
    db: Session = Depends(get_db),
):
    """List all affiliate programs."""
    query = db.query(Program)
    if is_active is not None:
        query = query.filter(Program.is_active == is_active)
    return query.offset(skip).limit(limit).all()


@router.get("/{program_id}", response_model=ProgramResponse)
def get_program(
    program_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """Get a specific program by ID."""
    program = db.query(Program).filter(Program.id == program_id).first()
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    return program


@router.put("/{program_id}", response_model=ProgramResponse)
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


@router.delete("/{program_id}", status_code=status.HTTP_204_NO_CONTENT)
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
