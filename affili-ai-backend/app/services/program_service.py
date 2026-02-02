"""
Program service - handles program CRUD operations and discovery.
"""

from sqlalchemy.orm import Session
from typing import Optional, List
import uuid

from app.models.program import Program


def get_program(db: Session, program_id: uuid.UUID) -> Optional[Program]:
    """Get a program by ID."""
    return db.query(Program).filter(Program.id == program_id).first()


def get_program_by_name(db: Session, name: str) -> Optional[Program]:
    """Get a program by name."""
    return db.query(Program).filter(Program.name == name).first()


def get_program_by_signup_url(db: Session, signup_url: str) -> Optional[Program]:
    """Get a program by signup URL (for duplicate detection)."""
    return db.query(Program).filter(Program.signup_url == signup_url).first()


def list_programs(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    source: Optional[str] = None
) -> List[Program]:
    """List programs with optional filtering."""
    query = db.query(Program)
    
    if source:
        query = query.filter(Program.source == source)
    
    return query.offset(skip).limit(limit).all()


def create_discovered_program(
    db: Session,
    name: str,
    base_url: str,
    signup_url: str,
    confidence_score: float
) -> Program:
    """
    Create a discovered program.
    
    Args:
        db: Database session
        name: Program name
        base_url: Original website URL
        signup_url: Detected signup URL
        confidence_score: Discovery confidence (0.0-1.0)
    
    Returns:
        Created Program instance
    """
    # Check for duplicate
    existing = get_program_by_signup_url(db, signup_url)
    if existing:
        print(f"[ProgramService] Program already exists: {existing.name}")
        return existing
    
    program = Program(
        name=name,
        base_url=base_url,
        signup_url=signup_url,
        affiliate_url=signup_url,  # Use signup_url as affiliate_url for now
        source="discovered",
        confidence_score=confidence_score,
        is_active=True
    )
    
    db.add(program)
    db.commit()
    db.refresh(program)
    
    print(f"[ProgramService] Created discovered program: {name}")
    
    return program


def create_manual_program(
    db: Session,
    name: str,
    affiliate_url: str,
    description: Optional[str] = None,
    commission_rate: Optional[float] = None
) -> Program:
    """Create a manually added program."""
    program = Program(
        name=name,
        affiliate_url=affiliate_url,
        description=description,
        commission_rate=commission_rate,
        source="manual",
        is_active=True
    )
    
    db.add(program)
    db.commit()
    db.refresh(program)
    
    return program
