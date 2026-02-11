import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import get_engine_instance
from app.db.base import Base
# Import models to ensure they are registered with Base
from app.models.usage import TenantUsage
from app.models.policy import Policy
from app.models.program import Program
from app.models.task import Task
from app.models.agent import Agent
from app.models.user import User
from app.models.tenant import Tenant

def fix_database():
    """Create all missing tables in PostgreSQL."""
    print("Connecting to database...")
    
    # Create tables
    print("Creating missing tables...")
    engine = get_engine_instance()
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables verified/created successfully!")

if __name__ == "__main__":
    try:
        fix_database()
    except Exception as e:
        print(f"\nError fixing database: {e}")
