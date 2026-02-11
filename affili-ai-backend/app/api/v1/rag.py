"""
RAG API endpoints for similarity search and field predictions.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.rag_service import similarity_search, get_best_match, get_field_suggestions
from app.services.embedding_service import store_field_embedding
from app.core.tenant import get_tenant_id
from app.api.dependencies import verify_tenant, require_roles, get_current_user
from app.models.user import UserRole, User
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import uuid

router = APIRouter(prefix="/rag", tags=["rag"], dependencies=[Depends(verify_tenant)])


class RAGSearchRequest(BaseModel):
    """Request model for RAG similarity search."""
    field_label: str = Field(..., description="Form field label to search for")
    program_id: Optional[str] = Field(None, description="Optional program UUID filter")
    top_k: int = Field(5, ge=1, le=20, description="Number of results to return")
    threshold: float = Field(0.7, ge=0.0, le=1.0, description="Minimum similarity score")


class RAGSearchResponse(BaseModel):
    """Response model for RAG similarity search."""
    matches: List[Dict[str, Any]]
    query: str
    count: int


class StoreFieldRequest(BaseModel):
    """Request model for storing field embeddings."""
    program_id: Optional[str] = Field(None, description="Optional program UUID")
    field_label: str = Field(..., description="Form field label")
    field_type: str = Field(..., description="Field type (text, email, url, etc)")
    successful_value: str = Field(..., description="Value that was successfully submitted")
    form_context: Optional[Dict[str, Any]] = Field(None, description="Additional form metadata")


class BatchSearchRequest(BaseModel):
    """Request model for batch field suggestions."""
    field_labels: List[str] = Field(..., description="List of field labels to get suggestions for")
    program_id: Optional[str] = Field(None, description="Optional program UUID filter")


@router.post("/search", response_model=RAGSearchResponse)
def search_similar_fields(
    request: RAGSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search for similar form fields using RAG embeddings.
    
    Returns fields from past successful submissions that match the query.
    Useful for predicting field values based on historical data.
    """
    tenant_id = uuid.UUID(get_tenant_id())
    program_id = uuid.UUID(request.program_id) if request.program_id else None
    
    matches = similarity_search(
        db=db,
        tenant_id=tenant_id,
        field_label=request.field_label,
        program_id=program_id,
        top_k=request.top_k,
        threshold=request.threshold
    )
    
    return RAGSearchResponse(
        matches=matches,
        query=request.field_label,
        count=len(matches)
    )


@router.post("/best-match")
def get_best_field_match(
    request: RAGSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the single best match for a field label.
    
    Returns null if no match meets the confidence threshold.
    """
    tenant_id = uuid.UUID(get_tenant_id())
    program_id = uuid.UUID(request.program_id) if request.program_id else None
    
    match = get_best_match(
        db=db,
        tenant_id=tenant_id,
        field_label=request.field_label,
        program_id=program_id,
        min_confidence=request.threshold
    )
    
    if not match:
        return {"match": None, "confidence": 0.0}
    
    return {"match": match, "confidence": match["similarity"]}


@router.post("/suggestions")
def get_batch_suggestions(
    request: BatchSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get field suggestions for multiple fields at once.
    
    More efficient than calling /search multiple times.
    """
    tenant_id = uuid.UUID(get_tenant_id())
    program_id = uuid.UUID(request.program_id) if request.program_id else None
    
    suggestions = get_field_suggestions(
        db=db,
        tenant_id=tenant_id,
        field_labels=request.field_labels,
        program_id=program_id
    )
    
    return {"suggestions": suggestions}


@router.post("/store", dependencies=[Depends(require_roles(UserRole.OWNER, UserRole.ADMIN, UserRole.OPERATOR))])
def store_field(
    request: StoreFieldRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Store a successful form field submission for future RAG lookups.
    
    This should be called after a successful automation to build up
    the knowledge base.
    
    Requires OWNER, ADMIN, or OPERATOR role.
    """
    tenant_id = uuid.UUID(get_tenant_id())
    program_id = uuid.UUID(request.program_id) if request.program_id else None
    
    try:
        embedding = store_field_embedding(
            db=db,
            tenant_id=tenant_id,
            program_id=program_id,
            field_label=request.field_label,
            field_type=request.field_type,
            successful_value=request.successful_value,
            form_context=request.form_context
        )
        
        return {
            "status": "success",
            "embedding_id": str(embedding.id),
            "field_label": embedding.field_label,
            "success_count": embedding.success_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store field: {str(e)}")
