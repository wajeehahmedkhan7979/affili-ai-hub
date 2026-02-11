import sys
import os
import time
from sqlalchemy import create_engine, text
from app.core.config import get_settings

def create_tables():
    settings = get_settings()
    url = settings.DATABASE_URL
    print(f"Connecting to: {url}")
    
    engine = create_engine(url, isolation_level="AUTOCOMMIT")
    
    with engine.connect() as conn:
        print("Creating tenant_usage table if missing...")
        
        # We need to ensure 'tenants' exists first for FK, but we will skip FK for now if it fails,
        # or just assume it exists (since other things work).
        # Actually, let's check if tenants exists
        
        # Raw SQL creation
        sql = """
        CREATE TABLE IF NOT EXISTS tenant_usage (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            date DATE NOT NULL,
            tasks_created INTEGER DEFAULT 0,
            tasks_completed INTEGER DEFAULT 0,
            tasks_failed INTEGER DEFAULT 0,
            agent_minutes FLOAT DEFAULT 0.0,
            captcha_events INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT uix_tenant_date UNIQUE (tenant_id, date)
        );
        """
        # Note: I removed Foreign Key to avoid dependency issues for this emergency fix
        # Adding index manually
        
        try:
            conn.execute(text(sql))
            print("✓ Created/Verified tenant_usage table")
            
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_tenant_usage_tenant_id ON tenant_usage (tenant_id);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_tenant_usage_date ON tenant_usage (date);"))
            print("✓ Indexes created")
            
        except Exception as e:
            print(f"Error creating table: {e}")

if __name__ == "__main__":
    create_tables()
