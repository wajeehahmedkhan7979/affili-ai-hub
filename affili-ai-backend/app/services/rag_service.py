"""
RAG (Retrieval-Augmented Generation) service for similarity search.

Provides similarity search on form field embeddings using cosine similarity.
Helps predict field values based on past successful submissions.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, text
from app.models.form_field_embedding import FormFieldEmbedding
from app.services.embedding_service import generate_embedding
from app.core.logging import logger
from typing import List, Dict, Any, Optional
import uuid
import json


def similarity_search(
    db: Session,
    tenant_id: uuid.UUID,
    field_label: str,
    program_id: Optional[uuid.UUID] = None,
    top_k: int = 5,
    threshold: float = 0.7
) -> List[Dict[str, Any]]:
    """
    Find similar form fields using cosine similarity on embeddings.
    
    Args:
        db: Database session
        tenant_id: Tenant UUID (for isolation)
        field_label: The field label to find similar matches for
        program_id: Optional program filter (more specific matches)
        top_k: Number of results to return
        threshold: Minimum similarity score (0-1)
        
    Returns:
        List of matches, each containing:
        {
            "field_label": str,
            "field_type": str,
            "successful_value": str,
            "similarity": float,
            "success_count": int,
            "program_id": str | null
        }
    """
    logger.info(f"RAG search: label='{field_label}', program={program_id}, top_k={top_k}")
    
    # Generate embedding for query
    try:
        query_embedding = generate_embedding(field_label)
    except Exception as e:
        logger.error(f"Failed to generate query embedding: {e}")
        return []
    
    # Check database type
    try:
        from app.db.session import get_engine_instance
        engine = get_engine_instance()
        is_sqlite = "sqlite" in str(engine.url)
    except:
        is_sqlite = False
    
    if is_sqlite:
        # SQLite fallback: cosine similarity in Python
        return _similarity_search_sqlite(
            db, tenant_id, query_embedding, program_id, top_k, threshold
        )
    else:
        # PostgreSQL with pgvector: use native vector operations
        return _similarity_search_postgres(
            db, tenant_id, query_embedding, program_id, top_k, threshold
        )


def _similarity_search_postgres(
    db: Session,
    tenant_id: uuid.UUID,
    query_embedding: List[float],
    program_id: Optional[uuid.UUID],
    top_k: int,
    threshold: float
) -> List[Dict[str, Any]]:
    """PostgreSQL similarity search using pgvector."""
    
    # Build query with pgvector's cosine distance operator (<=>)
    query = db.query(
        FormFieldEmbedding,
        FormFieldEmbedding.embedding.cosine_distance(query_embedding).label("distance")
    ).filter(
        FormFieldEmbedding.tenant_id == tenant_id
    )
    
    # Optional program filter
    if program_id:
        query = query.filter(FormFieldEmbedding.program_id == program_id)
    
    # Order by distance (lower is more similar) and limit
    results = query.order_by("distance").limit(top_k).all()
    
    # Convert to response format
    matches = []
    for embedding, distance in results:
        similarity = 1 - distance  # Convert distance to similarity (0-1)
        
        if similarity >= threshold:
            matches.append({
                "field_label": embedding.field_label,
                "field_type": embedding.field_type,
                "successful_value": embedding.successful_value,
                "similarity": round(similarity, 3),
                "success_count": embedding.success_count,
                "program_id": str(embedding.program_id) if embedding.program_id else None,
                "last_used_at": embedding.last_used_at.isoformat() if embedding.last_used_at else None
            })
    
    logger.info(f"Found {len(matches)} matches above threshold {threshold}")
    return matches


def _similarity_search_sqlite(
    db: Session,
    tenant_id: uuid.UUID,
    query_embedding: List[float],
    program_id: Optional[uuid.UUID],
    top_k: int,
    threshold: float
) -> List[Dict[str, Any]]:
    """SQLite fallback: compute cosine similarity in Python."""
    
    import numpy as np
    
    # Fetch all embeddings for this tenant
    query = db.query(FormFieldEmbedding).filter(
        FormFieldEmbedding.tenant_id == tenant_id,
        FormFieldEmbedding.embedding.isnot(None)
    )
    
    if program_id:
        query = query.filter(FormFieldEmbedding.program_id == program_id)
    
    embeddings = query.all()
    
    if not embeddings:
        logger.info("No embeddings found for tenant")
        return []
    
    # Compute similarities
    query_vec = np.array(query_embedding)
    results = []
    
    for emb in embeddings:
        try:
            # Parse JSON-stored embedding
            emb_vec = np.array(json.loads(emb.embedding))
            
            # Cosine similarity
            similarity = np.dot(query_vec, emb_vec) / (
                np.linalg.norm(query_vec) * np.linalg.norm(emb_vec)
            )
            
            if similarity >= threshold:
                results.append({
                    "embedding": emb,
                    "similarity": float(similarity)
                })
        except Exception as e:
            logger.warning(f"Failed to compute similarity for embedding {emb.id}: {e}")
            continue
    
    # Sort by similarity (descending) and take top_k
    results.sort(key=lambda x: x["similarity"], reverse=True)
    results = results[:top_k]
    
    # Convert to response format
    matches = []
    for r in results:
        emb = r["embedding"]
        matches.append({
            "field_label": emb.field_label,
            "field_type": emb.field_type,
            "successful_value": emb.successful_value,
            "similarity": round(r["similarity"], 3),
            "success_count": emb.success_count,
            "program_id": str(emb.program_id) if emb.program_id else None,
            "last_used_at": emb.last_used_at.isoformat() if emb.last_used_at else None
        })
    
    logger.info(f"Found {len(matches)} matches above threshold {threshold}")
    return matches


def get_best_match(
    db: Session,
    tenant_id: uuid.UUID,
    field_label: str,
    program_id: Optional[uuid.UUID] = None,
    min_confidence: float = 0.8
) -> Optional[Dict[str, Any]]:
    """
    Get the single best match for a field label.
    
    Returns None if no match meets the minimum confidence threshold.
    
    Args:
        db: Database session
        tenant_id: Tenant UUID
        field_label: Field label to match
        program_id: Optional program filter
        min_confidence: Minimum similarity score required
        
    Returns:
        Best match dict or None
    """
    matches = similarity_search(
        db, tenant_id, field_label, program_id, top_k=1, threshold=min_confidence
    )
    
    return matches[0] if matches else None


def get_field_suggestions(
    db: Session,
    tenant_id: uuid.UUID,
    field_labels: List[str],
    program_id: Optional[uuid.UUID] = None
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get suggestions for multiple fields at once.
    
    Args:
        db: Database session
        tenant_id: Tenant UUID  
        field_labels: List of field labels to get suggestions for
        program_id: Optional program filter
        
    Returns:
        Dict mapping field_label -> list of matches
    """
    results = {}
    
    for label in field_labels:
        try:
            matches = similarity_search(
                db, tenant_id, label, program_id, top_k=3, threshold=0.6
            )
            results[label] = matches
        except Exception as e:
            logger.error(f"Failed to get suggestions for '{label}': {e}")
            results[label] = []
    
    return results
