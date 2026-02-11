"""
Feedback API endpoints for human correction of AI predictions.

Allows OWNER/ADMIN/OPERATOR to correct AI field predictions,
creating a learning loop that improves RAG over time.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.human_feedback import HumanFeedback, FeedbackVerdict
from app.services.feedback_service import (
    process_feedback_reinforcement,
    apply_embedding_decay,
    get_correction_frequency
)
from app.api.dependencies import get_current_user, require_roles
from app.models.user import User, UserRole
from app.core.tenant import get_tenant_id
from pydantic import BaseModel, Field
from typing import Optional, List
import uuid

router = APIRouter(
    prefix="/feedback",
    tags=["feedback"],
    dependencies=[Depends(require_roles(UserRole.OWNER, UserRole.ADMIN, UserRole.OPERATOR))]
)


class FeedbackSubmitRequest(BaseModel):
    """Request model for submitting feedback."""
    task_id: Optional[str] = Field(None, description="Task UUID where prediction occurred")
    program_id: Optional[str] = Field(None, description="Program UUID")
    field_label: str = Field(..., description="Form field label")
    field_type: str = Field("text", description="Field type")
    predicted_value: Optional[str] = Field(None, description="AI's prediction")
    prediction_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    prediction_source: Optional[str] = Field(None, description="rag, heuristic, or llm")
    corrected_value: str = Field(..., description="Correct value")
    verdict: FeedbackVerdict = Field(..., description="CORRECT, WRONG, or PARTIAL")
    correction_notes: Optional[str] = Field(None, description="Optional notes")


@router.post("/submit")
def submit_feedback(
    request: FeedbackSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submit human feedback on an AI prediction.
    
    This creates a learning signal that improves RAG accuracy.
    """
    tenant_id = uuid.UUID(get_tenant_id())
    
    # Create feedback record
    feedback = HumanFeedback(
        tenant_id=tenant_id,
        task_id=uuid.UUID(request.task_id) if request.task_id else None,
        program_id=uuid.UUID(request.program_id) if request.program_id else None,
        field_label=request.field_label,
        field_type=request.field_type,
        predicted_value=request.predicted_value,
        prediction_confidence=request.prediction_confidence,
        prediction_source=request.prediction_source,
        corrected_value=request.corrected_value,
        verdict=request.verdict,
        corrected_by=current_user.id,
        correction_notes=request.correction_notes
    )
    
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    
    # Process feedback immediately to update RAG
    result = process_feedback_reinforcement(db, feedback)
    
    return {
        "feedback_id": str(feedback.id),
        "verdict": request.verdict,
        "reinforcement_action": result["action"],
        "message": f"Feedback recorded and processed: {result['action']}"
    }


@router.get("/corrections")
def get_corrections(
    field_label: Optional[str] = None,
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get correction frequency stats.
    
    Identifies fields that frequently need correction.
    """
    tenant_id = uuid.UUID(get_tenant_id())
    
    stats = get_correction_frequency(
        db=db,
        tenant_id=tenant_id,
        field_label=field_label,
        days=days
    )
    
    return stats


@router.post("/decay")
def trigger_embedding_decay(
    decay_threshold_days: int = 90,
    decay_factor: float = 0.9,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Manually trigger embedding decay.
    
    Reduces weight of old embeddings to prevent stale data dominance.
    Requires OWNER/ADMIN role.
    """
    # Additional RBAC check for this sensitive operation
    if current_user.role not in [UserRole.OWNER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Only OWNER/ADMIN can trigger decay")
    
    tenant_id = uuid.UUID(get_tenant_id())
    
    result = apply_embedding_decay(
        db=db,
        tenant_id=tenant_id,
        decay_threshold_days=decay_threshold_days,
        decay_factor=decay_factor
    )
    
    return {
        "status": "completed",
        **result
    }


@router.get("/recent")
def get_recent_feedback(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get recent feedback submissions.
    
    Useful for audit and monitoring.
    """
    tenant_id = uuid.UUID(get_tenant_id())
    
    feedbacks = db.query(HumanFeedback).filter(
        HumanFeedback.tenant_id == tenant_id
    ).order_by(
        HumanFeedback.created_at.desc()
    ).limit(limit).all()
    
    return {
        "feedbacks": [
            {
                "id": str(f.id),
                "field_label": f.field_label,
                "predicted_value": f.predicted_value,
                "corrected_value": f.corrected_value,
                "verdict": f.verdict,
                "confidence": f.prediction_confidence,
                "source": f.prediction_source,
                "processed": f.processed,
                "created_at": f.created_at.isoformat()
            }
            for f in feedbacks
        ],
        "count": len(feedbacks)
    }
