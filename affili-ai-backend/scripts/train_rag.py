import sys
import os
import uuid
import time
from sqlalchemy import text
from app.db.session import SessionLocal
from app.models.response_pool import ResponsePool
from app.services.embedding_service import generate_embedding

def train_rag():
    print("Initializing RAG Training...")
    db = SessionLocal()
    
    try:
        # Check pgvector extension
        db.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        db.commit()
        print("✓ pgvector extension verified")
        
        # Fetch all responses
        # We process ALL of them to ensure embeddings are up to date
        responses = db.query(ResponsePool).all()
        print(f"Found {len(responses)} items in Response Pool.")
        
        updated_count = 0
        
        for item in responses:
            print(f"Processing: {item.question[:50]}...")
            
            # Text to embed: Using "Question" primarily for retrieval matching
            # Could also use "Question + Answer" but usually we match Query vs Question
            text_to_embed = item.question
            
            try:
                embedding = generate_embedding(text_to_embed)
                item.embedding = embedding
                updated_count += 1
            except Exception as e:
                print(f"Failed to generate embedding for {item.id}: {e}")
        
        db.commit()
        print(f"\n✓ Successfully trained {updated_count} items with vector embeddings.")
        print("✓ RAG System is now ready for semantic search!")
        
    except Exception as e:
        print(f"Training failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    train_rag()
