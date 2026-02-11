"""
Field predictor orchestration service.

Combines RAG similarity search + LLM prediction for intelligent form field value prediction.
This is the main entry point for field prediction during automation.
"""

from app.services.rag_service import similarity_search
from app.services.llm_service import predict_field_value
from app.core.logging import logger
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
import uuid


def predict_form_field(
    db: Session,
    tenant_id: uuid.UUID,
    field_label: str,
    field_type: str,
    user_profile: Dict[str, Any],
    program_id: Optional[uuid.UUID] = None,
    task_id: Optional[uuid.UUID] = None,
    current_task_llm_calls: int = 0
) -> Dict[str, Any]:
    """
    Full pipeline: RAG → LLM → Decision.
    
    Flow:
    1. Query RAG for similar fields (cosine similarity on embeddings)
    2. Pass RAG results + user context to LLM
    3. LLM returns structured decision with confidence score
    4. Validate and return (confidence gating)
    
    Args:
        db: Database session
        tenant_id: Tenant UUID for isolation
        field_label: Form field label (e.g., "Company Name")
        field_type: Field type (text, email, url, etc.)
        user_profile: User context (name, email, website, company)
        program_id: Optional program UUID for more targeted matches
        task_id: Optional task UUID for governance tracking
        current_task_llm_calls: Number of LLM calls made in current task
        
    Returns:
        {
            "value": str or None,       # Predicted value (null if rejected)
            "confidence": float,        # 0.0-1.0
            "source": str,              # "rag" | "heuristic" | "rejected"
            "reasoning": str,           # Explanation
            "rag_matches": List[Dict]   # RAG candidates used (for debugging)
        }
    """
    logger.info(f"Predicting field: label='{field_label}', type={field_type}, program={program_id}")
    
    # Step 1: RAG lookup
    try:
        rag_results = similarity_search(
            db=db,
            tenant_id=tenant_id,
            field_label=field_label,
            program_id=program_id,
            top_k=3,
            threshold=0.6  # Lower threshold to give LLM more context
        )
        logger.info(f"Found {len(rag_results)} RAG candidates for '{field_label}'")
    except Exception as e:
        logger.error(f"RAG search failed: {e}")
        rag_results = []
    
    # Step 2: Prepare user context
    user_context = {
        "name": user_profile.get("name", ""),
        "email": user_profile.get("email", ""),
        "website": user_profile.get("website", ""),
        "company": user_profile.get("company", "")
    }
    
    # Step 3: LLM prediction with governance
    try:
        prediction = predict_field_value(
            field_label=field_label,
            field_type=field_type,
            rag_candidates=rag_results,
            user_context=user_context,
            tenant_id=tenant_id,
            task_id=task_id,
            current_task_llm_calls=current_task_llm_calls,
            db=db
        )
    except Exception as e:
        logger.error(f"LLM prediction failed: {e}")
        prediction = {
            "value": "",
            "confidence": 0.0,
            "source": "rejected",
            "reasoning": f"LLM error: {str(e)}"
        }
    
    # Step 4: Confidence gating
    MIN_CONFIDENCE = 0.5
    
    if prediction["confidence"] < MIN_CONFIDENCE:
        logger.warning(f"Low confidence ({prediction['confidence']}) for '{field_label}', rejecting prediction")
        return {
            "value": None,  # Null indicates human input needed
            "confidence": prediction["confidence"],
            "source": "rejected",
            "reasoning": f"Confidence {prediction['confidence']} below threshold {MIN_CONFIDENCE}. {prediction.get('reasoning', '')}",
            "rag_matches": rag_results
        }
    
    # High confidence - return prediction
    logger.info(f"Accepted prediction for '{field_label}': value='{prediction['value'][:50]}...', confidence={prediction['confidence']}")
    return {
        "value": prediction["value"],
        "confidence": prediction["confidence"],
        "source": prediction["source"],
        "reasoning": prediction["reasoning"],
        "rag_matches": rag_results
    }


def predict_multiple_fields(
    db: Session,
    tenant_id: uuid.UUID,
    fields: List[Dict[str, str]],
    user_profile: Dict[str, Any],
    program_id: Optional[uuid.UUID] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Predict values for multiple fields at once.
    
    More efficient than calling predict_form_field multiple times
    since RAG queries can be batched.
    
    Args:
        db: Database session
        tenant_id: Tenant UUID
        fields: List of dicts with keys: field_label, field_type
        user_profile: User context
        program_id: Optional program filter
        
    Returns:
        Dict mapping field_label -> prediction result
    """
    logger.info(f"Batch predicting {len(fields)} fields")
    
    predictions = {}
    
    for field in fields:
        field_label = field.get("field_label")
        field_type = field.get("field_type", "text")
        
        if not field_label:
            logger.warning("Skipping field with no label")
            continue
        
        try:
            prediction = predict_form_field(
                db=db,
                tenant_id=tenant_id,
                field_label=field_label,
                field_type=field_type,
                user_profile=user_profile,
                program_id=program_id
            )
            predictions[field_label] = prediction
        except Exception as e:
            logger.error(f"Failed to predict field '{field_label}': {e}")
            predictions[field_label] = {
                "value": None,
                "confidence": 0.0,
                "source": "rejected",
                "reasoning": f"Prediction error: {str(e)}",
                "rag_matches": []
            }
    
    logger.info(f"Completed batch prediction: {len(predictions)}/{len(fields)} fields processed")
    return predictions


def get_prediction_stats(predictions: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze prediction results for reporting/debugging.
    
    Args:
        predictions: Dict of field_label -> prediction result
        
    Returns:
        Stats dict with counts, avg confidence, etc.
    """
    if not predictions:
        return {
            "total_fields": 0,
            "predicted_count": 0,
            "rejected_count": 0,
            "avg_confidence": 0.0,
            "source_breakdown": {}
        }
    
    total = len(predictions)
    predicted = sum(1 for p in predictions.values() if p.get("value") is not None)
    rejected = total - predicted
    
    confidences = [p.get("confidence", 0.0) for p in predictions.values()]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
    
    sources = [p.get("source") for p in predictions.values()]
    source_breakdown = {
        "rag": sources.count("rag"),
        "heuristic": sources.count("heuristic"),
        "rejected": sources.count("rejected")
    }
    
    return {
        "total_fields": total,
        "predicted_count": predicted,
        "rejected_count": rejected,
        "avg_confidence": round(avg_confidence, 3),
        "source_breakdown": source_breakdown,
        "success_rate": round(predicted / total, 3) if total > 0 else 0.0
    }
