from app.db.session import get_db
from app.models.program import Program
from app.api.dependencies import verify_tenant
from app.core.tenant import set_tenant_id

# Simulate context
set_tenant_id("00000000-0000-0000-0000-000000000000")

db = next(get_db())
programs = db.query(Program).all()

print(f"Total Programs: {len(programs)}")
for p in programs:
    print(f" - {p.name} ({p.url})")
