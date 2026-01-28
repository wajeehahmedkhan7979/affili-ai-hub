import sys
sys.path.insert(0, 'D:\\PROJECTS-REPOS\\AFFILIATE-PROJ\\affili-ai-hub\\affili-ai-backend')

from app.core.config import settings
from app.db.session import get_db, get_engine_instance
from app.db.base import Base
from app.models.program import Program

print("=== DATABASE CONNECTION TEST ===\n")

# Try to create tables
try:
    print("Creating tables...")
    Base.metadata.create_all(bind=get_engine_instance())
    print("✓ Tables created successfully\n")
except Exception as e:
    print(f"✗ Error creating tables: {e}\n")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Try to query
try:
    print("Testing database query...")
    db_gen = get_db()
    db = next(db_gen)
    programs = db.query(Program).all()
    print(f"✓ Query successful, found {len(programs)} programs\n")
    db.close()
except Exception as e:
    print(f"✗ Error querying database: {e}\n")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("=== ALL TESTS PASSED ===")
