"""
Embedding service for generating and managing vector embeddings.

Uses sentence-transformers for local embedding generation (no API costs).
Model: all-MiniLM-L6-v2 (384 dimensions, fast, good quality)
"""

from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session
from app.models.form_field_embedding import FormFieldEmbedding
from app.core.logging import logger
from typing import List, Dict, Any, Optional
import numpy as np
import uuid
import json

# Global model instance (loaded once, reused)
_embedding_model: Optional[SentenceTransformer] = None


def get_embedding_model() -> SentenceTransformer:
    """
    Get the singleton embedding model instance.
    
    Loads the model on first call, then reuses the same instance.
    This avoids the overhead of loading the model multiple times.
    """
    global _embedding_model
    
    if _embedding_model is None:
        logger.info("Loading sentence-transformers model: all-MiniLM-L6-v2")
        _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("Embedding model loaded successfully")
    
    return _embedding_model


def generate_embedding(text: str) -> List[float]:
    """
    Generate a 384-dimensional embedding vector for the given text.
    
    Args:
        text: Input text to encode
        
    Returns:
        List of 384 floats representing the embedding vector
    """
    if not text or not text.strip():
        raise ValueError("Cannot generate embedding for empty text")
    
    model = get_embedding_model()
    
    # Normalize text
    text = text.strip()
    
    # Generate embedding
    embedding = model.encode(text, convert_to_numpy=True)
    
    # Convert to Python list for JSON serialization
    return embedding.tolist()


def store_field_embedding(
    db: Session,
    tenant_id: uuid.UUID,
    program_id: Optional[uuid.UUID],
    field_label: str,
    field_type: str,
    successful_value: str,
    form_context: Optional[Dict[str, Any]] = None
) -> FormFieldEmbedding:
    """
    Store a successful form field response with its embedding.
    
    This is called after a successful form submission to build up
    the RAG knowledge base for future predictions.
    
    Args:
        db: Database session
        tenant_id: Tenant UUID (for isolation)
        program_id: Optional program UUID this field belongs to
        field_label: The form field label (e.g., "Company Name")
        field_type: Field type (text, email, url, etc.)
        successful_value: The value that was successfully submitted
        form_context: Optional metadata about the form
        
    Returns:
        The created FormFieldEmbedding instance
    """
    logger.info(f"Storing field embedding: label='{field_label}', type={field_type}")
    
    # Check if similar entry exists (update instead of creating duplicate)
    existing = db.query(FormFieldEmbedding).filter(
        FormFieldEmbedding.tenant_id == tenant_id,
        FormFieldEmbedding.program_id == program_id,
        FormFieldEmbedding.field_label == field_label,
        FormFieldEmbedding.field_type == field_type
    ).first()
    
    if existing:
        # Update existing entry
        logger.info(f"Updating existing embedding for field: {field_label}")
        existing.successful_value = successful_value
        existing.success_count += 1
        existing.last_used_at = db.query(db.func.now()).scalar()
        if form_context:
            existing.form_context = form_context
        
        db.commit()
        db.refresh(existing)
        return existing
    
    # Generate embedding
    try:
        embedding_vector = generate_embedding(field_label)
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        raise
    
    # For SQLite (development), store embedding as JSON string
    # For PostgreSQL (production), pgvector handles it natively
    try:
        from app.db.session import get_engine_instance
        engine = get_engine_instance()
        is_sqlite = "sqlite" in str(engine.url)
        
        if is_sqlite:
            # Store as JSON string for SQLite
            embedding_data = json.dumps(embedding_vector)
        else:
            # pgvector handles list directly
            embedding_data = embedding_vector
    except:
        # Default to list format
        embedding_data = embedding_vector
    
    # Create new entry
    entry = FormFieldEmbedding(
        tenant_id=tenant_id,
        program_id=program_id,
        field_label=field_label,
        field_type=field_type,
        successful_value=successful_value,
        embedding=embedding_data,
        form_context=form_context or {},
        success_count=1
    )
    
    db.add(entry)
    db.commit()
    db.refresh(entry)
    
    logger.info(f"Stored new field embedding: id={entry.id}")
    return entry


def batch_store_embeddings(
    db: Session,
    tenant_id: uuid.UUID,
    program_id: Optional[uuid.UUID],
    field_data: List[Dict[str, str]]
) -> List[FormFieldEmbedding]:
    """
    Store multiple field embeddings in a batch (more efficient).
    
    Args:
        db: Database session
        tenant_id: Tenant UUID
        program_id: Optional program UUID
        field_data: List of dicts with keys: field_label, field_type, successful_value
        
    Returns:
        List of created/updated FormFieldEmbedding instances
    """
    logger.info(f"Batch storing {len(field_data)} field embeddings")
    
    results = []
    for field in field_data:
        try:
            entry = store_field_embedding(
                db=db,
                tenant_id=tenant_id,
                program_id=program_id,
                field_label=field['field_label'],
                field_type=field['field_type'],
                successful_value=field['successful_value'],
                form_context=field.get('form_context')
            )
            results.append(entry)
        except Exception as e:
            logger.error(f"Failed to store field '{field.get('field_label')}': {e}")
            continue
    
    logger.info(f"Successfully stored {len(results)}/{len(field_data)} embeddings")
    return results
