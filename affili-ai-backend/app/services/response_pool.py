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
) -> ResponsePool:
    """Create a new Q&A response in the pool."""
    response = ResponsePool(
        question=question,
        answer=answer,
        category=category,
        embedding=embedding,
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
    query_obj = db.query(ResponsePool)
    
    if category:
        query_obj = query_obj.filter(ResponsePool.category == category)
    
    # Filter by relevance score
    if threshold > 0:
        query_obj = query_obj.filter(ResponsePool.relevance_score >= threshold)
    
    # Simple keyword search on question
    query_obj = query_obj.filter(
        ResponsePool.question.ilike(f"%{query}%")
    )
    
    return query_obj.limit(limit).all()


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
