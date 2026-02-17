"""
Response Pool service for Q&A storage and similarity search.
"""

from sqlalchemy.orm import Session
from app.models.response_pool import ResponsePool
from typing import Optional, List
import uuid


def create_response(
    db: Session,
    question: str,
    answer: str,
    category: Optional[str] = None,
    embedding: Optional[List[float]] = None,
    tenant_id: Optional[uuid.UUID] = None,
) -> ResponsePool:
    """Create a new Q&A response in the pool."""
    response = ResponsePool(
        question=question,
        answer=answer,
        category=category,
        embedding=embedding,
        tenant_id=tenant_id,
    )
    db.add(response)
    db.commit()
    db.refresh(response)
    return response


def search_responses(
    db: Session,
    query: str,
    category: Optional[str] = None,
    limit: int = 10,
    threshold: float = 0.0,
) -> List[ResponsePool]:
    """Search responses by category and similarity.
    
    NOTE: Full vector similarity requires pgvector extension on PostgreSQL.
    TODO: Implement vector search with pgvector:
    - Use cosine similarity: <=> operator
    - Example: SELECT * FROM response_pool
               ORDER BY embedding <=> query_vector LIMIT limit
    
    For now, implements keyword-based filtering as fallback.
    """
    # Generate embedding for query
    try:
        from app.services.embedding_service import generate_embedding
        query_vector = generate_embedding(query)
        
        # Vector search using pgvector (<=> operator for cosine distance)
        # We order by distance ASC (closest match first)
        query_obj = db.query(
            ResponsePool,
            ResponsePool.embedding.cosine_distance(query_vector).label("distance")
        )
        
        if category:
            query_obj = query_obj.filter(ResponsePool.category == category)
            
        # Filter by threshold (distance < 1 - threshold)
        if threshold > 0:
            # cosine_distance is 0 for identical, 1 for orthogonal, 2 for opposite
            # similarity = 1 - distance
            # distance = 1 - similarity
            max_distance = 1.0 - threshold
            query_obj = query_obj.filter(ResponsePool.embedding.cosine_distance(query_vector) <= max_distance)
            
        # Order by distance
        return [r[0] for r in query_obj.order_by("distance").limit(limit).all()]
        
    except Exception as e:
        print(f"Vector search failed (using keyword fallback): {e}")
        # Fallback to keyword search
        query_obj = db.query(ResponsePool)
        if category:
            query_obj = query_obj.filter(ResponsePool.category == category)
        
        return query_obj.filter(ResponsePool.question.ilike(f"%{query}%")).limit(limit).all()


def get_response(db: Session, response_id: uuid.UUID) -> Optional[ResponsePool]:
    """Get a response by ID."""
    return db.query(ResponsePool).filter(ResponsePool.id == response_id).first()


def update_response(
    db: Session,
    response_id: uuid.UUID,
    question: Optional[str] = None,
    answer: Optional[str] = None,
    category: Optional[str] = None,
    embedding: Optional[List[float]] = None,
) -> Optional[ResponsePool]:
    """Update a response."""
    response = get_response(db, response_id)
    if not response:
        return None
    
    if question is not None:
        response.question = question
    if answer is not None:
        response.answer = answer
    if category is not None:
        response.category = category
    if embedding is not None:
        response.embedding = embedding
    
    db.commit()
    db.refresh(response)
    return response


def delete_response(db: Session, response_id: uuid.UUID) -> bool:
    """Delete a response."""
    response = get_response(db, response_id)
    if not response:
        return False
    
    db.delete(response)
    db.commit()
    return True


def prune_low_trust_responses(db: Session, threshold: float = 0.5) -> int:
    """
    Remove low-trust, unverified responses from the pool.
    """
    from sqlalchemy import and_
    
    stale_responses = db.query(ResponsePool).filter(
        and_(
            ResponsePool.trust_score < threshold,
            ResponsePool.is_verified == False
        )
    ).all()
    
    count = 0
    for resp in stale_responses:
        db.delete(resp)
        count += 1
        
    db.commit()
    return count


def verify_response(db: Session, response_id: uuid.UUID, trust_score: float = 1.0) -> Optional[ResponsePool]:
    """
    Mark a response as human-verified.
    """
    response = get_response(db, response_id)
    if not response:
        return None
        
    response.is_verified = True
    response.trust_score = trust_score
    db.commit()
    db.refresh(response)
    return response
