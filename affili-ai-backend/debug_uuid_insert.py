"""
Debug script to identify the exact source of the UUID int casting issue.
"""
from app.db.session import SessionLocal, get_engine
from app.db.base import Base
from app.models.tenant import Tenant
from app.models.task import Task
import uuid

def debug_uuid_insertion():
    print("Testing UUID insertion and retrieval...")
    
    # Use a fresh database
    import os
    os.environ["DATABASE_URL"] = "sqlite:///debug_uuid.db"
    
    from app.db.session import get_engine
    engine = get_engine("sqlite:///debug_uuid.db")
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    
    db = SessionLocal()
    
    # Insert a tenant
    tenant = Tenant(
        id=uuid.UUID("66f36618-29a3-4a1e-8e8e-67016258410e"),
        name="Test Tenant"
    )
    db.add(tenant)
    db.commit()
    print(f"✓ Inserted tenant: {tenant.id}")
    
    # Try to retrieve it
    try:
        fetched = db.query(Tenant).first()
        print(f"✓ Fetched tenant: {fetched.id}, type: {type(fetched.id)}")
    except Exception as e:
        print(f"✗ Failed to fetch tenant: {e}")
        import traceback
        traceback.print_exc()
    
    db.close()

if __name__ == "__main__":
    debug_uuid_insertion()
