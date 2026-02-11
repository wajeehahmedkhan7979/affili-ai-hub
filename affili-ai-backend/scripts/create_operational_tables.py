import sys
import uuid
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import get_settings

def create_tables():
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        print("Creating tenant_runtime_flags...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS tenant_runtime_flags (
                tenant_id UUID PRIMARY KEY REFERENCES tenants(id),
                ai_disabled BOOLEAN NOT NULL DEFAULT false,
                disable_reason TEXT,
                disabled_at TIMESTAMP,
                disabled_by UUID REFERENCES users(id),
                created_at TIMESTAMP NOT NULL DEFAULT now(),
                updated_at TIMESTAMP NOT NULL DEFAULT now()
            );
        """))
        
        print("Creating llm_usage_log...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS llm_usage_log (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                tenant_id UUID NOT NULL REFERENCES tenants(id),
                task_id UUID REFERENCES tasks(id),
                model VARCHAR(100) NOT NULL,
                tokens_used INTEGER NOT NULL,
                cost_usd NUMERIC(10, 6) NOT NULL,
                operation VARCHAR(50),
                extra_metadata JSONB,
                created_at TIMESTAMP NOT NULL DEFAULT now()
            );
        """))
        
        print("Creating operator_action_log...")
        # Create enum type if it doesn't exist
        try:
            conn.execute(text("""
                CREATE TYPE operatoractiontype AS ENUM (
                    'RESUME_TASK', 'CANCEL_TASK', 'MANUAL_OVERRIDE', 
                    'FEEDBACK_SUBMITTED', 'KILLSWITCH_ENABLED', 
                    'KILLSWITCH_DISABLED', 'QUOTA_ADJUSTED'
                )
            """))
        except Exception:
            print("Enum operatoractiontype already exists or skipped")
            
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS operator_action_log (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                tenant_id UUID NOT NULL REFERENCES tenants(id),
                operator_id UUID NOT NULL REFERENCES users(id),
                task_id UUID REFERENCES tasks(id),
                action operatoractiontype NOT NULL,
                reason TEXT,
                extra_metadata JSONB,
                created_at TIMESTAMP NOT NULL DEFAULT now()
            );
        """))
        
        conn.commit()
    print("✅ Operational tables created successfully!")

if __name__ == "__main__":
    create_tables()
