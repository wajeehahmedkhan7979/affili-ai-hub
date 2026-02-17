"""
Debug script to verify policy evaluation during task creation.
"""

from app.services.task_dispatcher import create_task
from app.db.session import get_engine_instance
from app.db.base import Base
from sqlalchemy.orm import Session
from app.core.tenant import set_tenant_id
from app.models.tenant import Tenant
import uuid
import traceback

engine = get_engine_instance()
Base.metadata.create_all(bind=engine)

with Session(engine) as db:
    # Get tenant
    tenant = db.query(Tenant).first()
    if not tenant:
        print("ERROR: No tenant found")
        exit(1)
    
    tenant_id = str(tenant.id)
    print(f"Using tenant: {tenant.name} ({tenant_id})")
    
    # Set context
    set_tenant_id(tenant_id)
    
    # Try creating a task
    try:
        print("Attempting to create task...")
        task = create_task(db, "DISCOVER_PROGRAM", {"test": "step B"})
        print(f"✅ SUCCESS: Created task: {task.id}")
        db.commit()
    except Exception as e:
        print(f"❌ ERROR: Failed to create task: {e}")
        print(f"Traceback:\n{traceback.format_exc()}")
        db.rollback()
