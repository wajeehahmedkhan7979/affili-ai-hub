from app.db.session import get_db
from app.models.task import Task
from app.api.dependencies import verify_tenant
from app.core.tenant import set_tenant_id

# Simulate context
set_tenant_id("00000000-0000-0000-0000-000000000000")

db = next(get_db())
tasks = db.query(Task).order_by(Task.created_at.desc()).limit(1).all()

print(f"Total Tasks: {len(tasks)}")
for t in tasks:
    print(f" - ID: {t.id}")
    print(f"   Type: {t.task_type}")
    print(f"   Status: {t.status}")
    print(f"   Payload: {t.payload}")
    print(f"   Result: {t.result}")
    print(f"   Error Details:")
    print(t.error_message)
    print("-" * 20)
