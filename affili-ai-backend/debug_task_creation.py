"""
Debug script to test workflow task creation in isolation.
"""

from app.services.task_dispatcher import create_task
from app.db.session import get_engine_instance
from sqlalchemy.orm import Session
from app.core.tenant import set_tenant_id
import uuid
import traceback

engine = get_engine_instance()
tenant_id = "00000000-0000-0000-0000-000000000000"
set_tenant_id(tenant_id)

try:
    with Session(engine) as db:
        print(f"Creating task with tenant_id: {tenant_id}")
        task = create_task(db, "DISCOVER_PROGRAM", {"test": "data"})
        print(f"SUCCESS: Created task: {task.id}")
except Exception as e:
    print(f"ERROR: Failed to create task: {e}")
    print(f"Traceback:\n{traceback.format_exc()}")
