import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from app.core.config import get_settings
from app.db.base import Base

# Import all models
from app.models.usage import TenantUsage
from app.models.policy import Policy
from app.models.program import Program
from app.models.task import Task
from app.models.agent import Agent
from app.models.user import User
from app.models.tenant import Tenant

def force_create():
    print("Loading settings...")
    settings = get_settings()
    url = settings.DATABASE_URL
    
    # Ensure correct driver for SQLAlchemy
    if url.startswith("postgresql://"):
        # Check if we need to swap to psycopg (v3) or psycopg2
        # Trying standard compatible URL first
        pass 
        
    print(f"Connecting to database...") 
    # Create engine directly, bypassing session.py complexity
    engine = create_engine(url, echo=True)
    
    print("Creating all tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Tables created successfully!")

if __name__ == "__main__":
    try:
        force_create()
    except Exception as e:
        print(f"Error: {e}")
