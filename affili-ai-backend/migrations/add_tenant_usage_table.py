"""
Migration script to create tenant_usage table.

Phase 7.3
"""

import sqlite3
import os


def migrate():
    """Create tenant_usage table."""
    db_path = os.path.join(os.getcwd(), "affili_ai.db")
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    print(f"Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if table already exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='tenant_usage'
        """)
        
        if cursor.fetchone():
            print("✓ Table 'tenant_usage' already exists. Skipping migration.")
            return
        
        # Create tenant_usage table
        print("Creating 'tenant_usage' table...")
        cursor.execute("""
            CREATE TABLE tenant_usage (
                id CHAR(36) PRIMARY KEY,
                tenant_id CHAR(36) NOT NULL,
                date DATE NOT NULL,
                tasks_created INTEGER DEFAULT 0,
                tasks_completed INTEGER DEFAULT 0,
                tasks_failed INTEGER DEFAULT 0,
                agent_minutes REAL DEFAULT 0.0,
                captcha_events INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(tenant_id) REFERENCES tenants(id),
                UNIQUE(tenant_id, date)
            )
        """)
        
        # Create indexes
        print("Creating indexes...")
        cursor.execute("CREATE INDEX ix_tenant_usage_tenant_id ON tenant_usage(tenant_id)")
        cursor.execute("CREATE INDEX ix_tenant_usage_date ON tenant_usage(date)")
        
        conn.commit()
        print("✓ Migration completed successfully!")
        
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
