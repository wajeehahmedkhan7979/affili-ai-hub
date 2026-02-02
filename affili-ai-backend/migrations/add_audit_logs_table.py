"""
Migration script to create audit_logs table.

Phase 7.4
"""

import sqlite3
import os


def migrate():
    """Create audit_logs table."""
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
            WHERE type='table' AND name='audit_logs'
        """)
        
        if cursor.fetchone():
            print("✓ Table 'audit_logs' already exists. Skipping migration.")
            return
        
        # Create audit_logs table
        print("Creating 'audit_logs' table...")
        cursor.execute("""
            CREATE TABLE audit_logs (
                id CHAR(36) PRIMARY KEY,
                tenant_id CHAR(36) NOT NULL,
                event_type VARCHAR(50) NOT NULL,
                actor_type VARCHAR(50) NOT NULL,
                actor_id VARCHAR(255) NOT NULL,
                actor_email VARCHAR(255),
                resource_type VARCHAR(50),
                resource_id VARCHAR(255),
                details JSON,
                ip_address VARCHAR(45),
                user_agent VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes
        print("Creating indexes...")
        cursor.execute("CREATE INDEX ix_audit_logs_tenant_id ON audit_logs(tenant_id)")
        cursor.execute("CREATE INDEX ix_audit_logs_event_type ON audit_logs(event_type)")
        cursor.execute("CREATE INDEX ix_audit_logs_created_at ON audit_logs(created_at)")
        
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
