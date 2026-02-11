"""
Feedback learning service - Process human corrections to improve RAG.

Implements safe feedback loop:
- CORRECT verdicts → boost confidence
- WRONG verdicts → store correction, reduce original
- Embedding decay to prevent stale data dominance
"""

from sqlalchemy.orm import Session
from app.models.human_feedback import HumanFeedback, FeedbackVerdict
from app.models.form_field_embedding import FormFieldEmbedding
from app.services.embedding_service import store_field_embedding, generate_embedding
from app.core.logging import logger
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import uuid


def process_feedback_reinforcement(
    db: Session,
    feedback: HumanFeedback
) -> Dict[str, Any]:
    """
    Process a single feedback item to reinforce RAG learning.
    
    Args:
        db: Database session
        feedback: HumanFeedback instance
        
    Returns:
        {
            "action": str,
            "embedding_id": str | None,
            "old_success_count": int,
            "new_success_count": int
        }
    """
    if feedback.processed:
        logger.warning(f"Feedback {feedback.id} already processed, skipping")
        return {
            "action": "SKIPPED_ALREADY_PROCESSED",
            "embedding_id": None,
            "old_success_count": 0,
            "new_success_count": 0
        }
    
    logger.info(f"Processing feedback {feedback.id}: verdict={feedback.verdict}")
    
    action = None
    embedding_id = None
    old_count = 0
    new_count = 0
    
    if feedback.verdict == FeedbackVerdict.CORRECT:
        # Boost confidence of the prediction
        action = _handle_correct_feedback(db, feedback)
        
    elif feedback.verdict == FeedbackVerdict.WRONG:
        # Store correction and penalize wrong prediction
        action = _handle_wrong_feedback(db, feedback)
        
    elif feedback.verdict == FeedbackVerdict.PARTIAL:
        # Store correction as new embedding
        action = _handle_partial_feedback(db, feedback)
    
    # Mark as processed
    feedback.processed = True
    feedback.processed_at = datetime.utcnow()
    db.commit()
    
    logger.info(f"Feedback processed: action={action}")
    
    return {
        "action": action,
        "embedding_id": str(embedding_id) if embedding_id else None,
        "old_success_count": old_count,
        "new_success_count": new_count
    }


def _handle_correct_feedback(
    db: Session,
    feedback: HumanFeedback
) -> str:
    """
    Boost success count of the embedding that generated this prediction.
    
    Returns action description.
    """
    # Find the embedding that likely generated this prediction
    embedding = db.query(FormFieldEmbedding).filter(
        FormFieldEmbedding.tenant_id == feedback.tenant_id,
        FormFieldEmbedding.program_id == feedback.program_id,
        FormFieldEmbedding.field_label == feedback.field_label,
        FormFieldEmbedding.successful_value == feedback.predicted_value
    ).first()
    
    if embedding:
        old_count = embedding.success_count
        embedding.success_count += 1
        embedding.last_used_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Boosted embedding {embedding.id}: {old_count} → {embedding.success_count}")
        return f"BOOSTED_SUCCESS_COUNT_{old_count}_TO_{embedding.success_count}"
    else:
        # Embedding not found - create it
        embedding = store_field_embedding(
            db=db,
            tenant_id=feedback.tenant_id,
            program_id=feedback.program_id,
            field_label=feedback.field_label,
            field_type=feedback.field_type,
            successful_value=feedback.corrected_value,
            form_context={"source": "human_feedback_correct"}
        )
        logger.info(f"Created new embedding from correct feedback: {embedding.id}")
        return "CREATED_EMBEDDING_FROM_CORRECT"


def _handle_wrong_feedback(
    db: Session,
    feedback: HumanFeedback
) -> str:
    """
    Penalize wrong prediction and store correction.
    
    Returns action description.
    """
    # Find and penalize the wrong embedding
    wrong_embedding = db.query(FormFieldEmbedding).filter(
        FormFieldEmbedding.tenant_id == feedback.tenant_id,
        FormFieldEmbedding.field_label == feedback.field_label,
        FormFieldEmbedding.successful_value == feedback.predicted_value
    ).first()
    
    if wrong_embedding and wrong_embedding.success_count > 0:
        old_count = wrong_embedding.success_count
        wrong_embedding.success_count = max(0, wrong_embedding.success_count - 1)
        db.commit()
        logger.info(f"Penalized wrong embedding {wrong_embedding.id}: {old_count} → {wrong_embedding.success_count}")
    
    # Store the correction as a new embedding
    correct_embedding = store_field_embedding(
        db=db,
        tenant_id=feedback.tenant_id,
        program_id=feedback.program_id,
        field_label=feedback.field_label,
        field_type=feedback.field_type,
        successful_value=feedback.corrected_value,
        form_context={"source": "human_feedback_correction"}
    )
    
    logger.info(f"Stored correction as new embedding: {correct_embedding.id}")
    return "PENALIZED_WRONG_STORED_CORRECTION"


def _handle_partial_feedback(
    db: Session,
    feedback: HumanFeedback
) -> str:
    """
    Store partial correction as new embedding.
    
    Returns action description.
    """
    embedding = store_field_embedding(
        db=db,
        tenant_id=feedback.tenant_id,
        program_id=feedback.program_id,
        field_label=feedback.field_label,
        field_type=feedback.field_type,
        successful_value=feedback.corrected_value,
        form_context={"source": "human_feedback_partial"}
    )
    
    logger.info(f"Stored partial correction: {embedding.id}")
    return "STORED_PARTIAL_CORRECTION"


def apply_embedding_decay(
    db: Session,
    tenant_id: uuid.UUID,
    decay_threshold_days: int = 90,
    decay_factor: float = 0.9
) -> Dict[str, Any]:
    """
    Apply time-based decay to old embeddings.
    
    Prevents stale data from dominating predictions.
    
    Args:
        db: Database session
        tenant_id: Tenant UUID
        decay_threshold_days: Embeddings older than this get decayed
        decay_factor: Multiply success_count by this (0.9 = 10% reduction)
        
    Returns:
        {
            "decayed_count": int,
            "total_embeddings": int
        }
    """
    logger.info(f"Applying embedding decay for tenant {tenant_id}")
    
    threshold_date = datetime.utcnow() - timedelta(days=decay_threshold_days)
    
    # Find old embeddings
    old_embeddings = db.query(FormFieldEmbedding).filter(
        FormFieldEmbedding.tenant_id == tenant_id,
        FormFieldEmbedding.created_at < threshold_date,
        FormFieldEmbedding.success_count > 0
    ).all()
    
    decayed_count = 0
    for emb in old_embeddings:
        old_count = emb.success_count
        emb.success_count = int(emb.success_count * decay_factor)
        
        if emb.success_count != old_count:
            decayed_count += 1
    
    db.commit()
    
    total_embeddings = db.query(FormFieldEmbedding).filter(
        FormFieldEmbedding.tenant_id == tenant_id
    ).count()
    
    logger.info(f"Decayed {decayed_count}/{total_embeddings} embeddings")
    
    return {
        "decayed_count": decayed_count,
        "total_embeddings": total_embeddings,
        "threshold_days": decay_threshold_days,
        "decay_factor": decay_factor
    }


def get_correction_frequency(
    db: Session,
    tenant_id: uuid.UUID,
    field_label: Optional[str] = None,
    days: int = 30
) -> Dict[str, Any]:
    """
    Get correction frequency stats for fields.
    
    Helps identify problematic fields that need attention.
    
    Args:
        db: Database session
        tenant_id: Tenant UUID
        field_label: Optional specific field to check
        days: Lookback period
        
    Returns:
        {
            "field_label": str,
            "total_predictions": int,
            "wrong_count": int,
            "correct_count": int,
            "accuracy": float
        }
    """
    since = datetime.utcnow() - timedelta(days=days)
    
    query = db.query(HumanFeedback).filter(
        HumanFeedback.tenant_id == tenant_id,
        HumanFeedback.created_at >= since
    )
    
    if field_label:
        query = query.filter(HumanFeedback.field_label == field_label)
    
    feedbacks = query.all()
    
    if not feedbacks:
        return {
            "field_label": field_label or "all",
            "total_predictions": 0,
            "wrong_count": 0,
            "correct_count": 0,
            "accuracy": 0.0
        }
    
    wrong_count = sum(1 for f in feedbacks if f.verdict == FeedbackVerdict.WRONG)
    correct_count = sum(1 for f in feedbacks if f.verdict == FeedbackVerdict.CORRECT)
    total = len(feedbacks)
    
    accuracy = (correct_count / total * 100) if total > 0 else 0.0
    
    return {
        "field_label": field_label or "all",
        "total_predictions": total,
        "wrong_count": wrong_count,
        "correct_count": correct_count,
        "accuracy": round(accuracy, 2),
        "period_days": days
    }
