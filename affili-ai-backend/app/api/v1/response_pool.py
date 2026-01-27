"""
Response Pool API endpoints for Q&A storage and similarity search.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.response_pool import ResponsePoolCreate, ResponsePoolResponse, SearchRequest
from app.services.response_pool import (
    create_response,
    search_responses,
    get_response,
    update_response,
    delete_response,
)
from typing import List
import uuid

router = APIRouter(prefix="/response-pool", tags=["response-pool"])


@router.post("", response_model=ResponsePoolResponse, status_code=status.HTTP_201_CREATED)
def create_response_endpoint(
    response_in: ResponsePoolCreate,
    db: Session = Depends(get_db),
):
    """Create a new Q&A pair in the response pool."""
    response = create_response(
        db,
        response_in.question,
        response_in.answer,
        response_in.category,
        response_in.embedding,
    )
    return response


@router.get("", response_model=List[ResponsePoolResponse])
def list_responses(
    category: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """List all Q&A pairs."""
    query = db.query(ResponsePoolCreate.__class__)
    if category:
        from app.models.response_pool import ResponsePool
        query = db.query(ResponsePool).filter(ResponsePool.category == category)
    return query.offset(skip).limit(limit).all()


@router.post("/search", response_model=List[ResponsePoolResponse])
def search_response_pool(
    search_req: SearchRequest,
    db: Session = Depends(get_db),
):
    """Search response pool by query."""
    results = search_responses(
        db,
        search_req.query,
        limit=search_req.limit,
        threshold=search_req.threshold,
    )
    return results


@router.get("/{response_id}", response_model=ResponsePoolResponse)
def get_response_endpoint(
    response_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """Get a Q&A pair by ID."""
    response = get_response(db, response_id)
    if not response:
        raise HTTPException(status_code=404, detail="Response not found")
    return response


@router.put("/{response_id}", response_model=ResponsePoolResponse)
def update_response_endpoint(
    response_id: uuid.UUID,
    update_in: ResponsePoolCreate,
    db: Session = Depends(get_db),
):
    """Update a Q&A pair."""
    response = update_response(
        db,
        response_id,
        update_in.question,
        update_in.answer,
        update_in.category,
        update_in.embedding,
    )
    if not response:
        raise HTTPException(status_code=404, detail="Response not found")
    return response


@router.delete("/{response_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_response_endpoint(
    response_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """Delete a Q&A pair."""
    success = delete_response(db, response_id)
    if not success:
        raise HTTPException(status_code=404, detail="Response not found")
