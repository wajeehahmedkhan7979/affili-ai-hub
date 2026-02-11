import sys
import os
from sqlalchemy import text
from app.db.session import SessionLocal
from app.models.response_pool import ResponsePool
from pgvector.sqlalchemy import Vector
import uuid
import numpy as np

def verify_rag():
    print("Verifying RAG System (Vector Search)...")
    db = SessionLocal()
    try:
        # 1. Create a dummy vector (384 dim)
        # We'll use a random vector for testing
        test_vec = np.random.rand(384).tolist()
        
        # 2. Insert a test record
        item_id = uuid.uuid4()
        item = ResponsePool(
            id=item_id,
            tenant_id=uuid.UUID("00000000-0000-0000-0000-000000000000"),
            question="Test Question Vector",
            answer="Test Answer",
            category="Test",
            embedding=test_vec,
            relevance_score=1.0
        )
        db.add(item)
        db.commit()
        print(f"Inserted test item {item_id}")
        
        # 3. Perform Similarity Search
        # search for same vector, should be top result
        print("Searching for similar vector...")
        
        # Using l2_distance or cosine_distance
        # Note: pgvector supports <-> (L2), <=> (Cosine), <#> (Inner Product)
        # SQLAlchemy usage: ResponsePool.embedding.l2_distance(vec)
        
        results = db.query(ResponsePool).order_by(
            ResponsePool.embedding.cosine_distance(test_vec)
        ).limit(1).all()
        
        if results:
            print(f"Found {len(results)} results.")
            top = results[0]
            print(f"Top result: {top.question} (ID: {top.id})")
            if top.id == item_id:
                print("✓ RAG Verification PASSED: Retrieved seeded item correctly.")
            else:
                print("⚠️ RAG Verification WARNING: Retrieved different item.")
        else:
            print("❌ RAG Verification FAILED: No results found.")
            
        # Cleanup
        db.delete(item)
        db.commit()
        
    except Exception as e:
        print(f"RAG Verification FAILED: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    verify_rag()
