"""
Migration script to create export_jobs table.

Phase 7.5
"""

import sqlite3
import os


def migrate():
    """Create export_jobs table."""
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
            WHERE type='table' AND name='export_jobs'
        """)
        
        if cursor.fetchone():
            print("✓ Table 'export_jobs' already exists. Skipping migration.")
            return
        
        # Create export_jobs table
        print("Creating 'export_jobs' table...")
        cursor.execute("""
            CREATE TABLE export_jobs (
                id CHAR(36) PRIMARY KEY,
                tenant_id CHAR(36) NOT NULL,
                export_type VARCHAR(50) NOT NULL,
                status VARCHAR(20) DEFAULT 'PENDING',
                filters JSON,
                file_path VARCHAR(500),
                error_message VARCHAR(500),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        """)
        
        # Create indexes
        print("Creating indexes...")
        cursor.execute("CREATE INDEX ix_export_jobs_tenant_id ON export_jobs(tenant_id)")
        cursor.execute("CREATE INDEX ix_export_jobs_status ON export_jobs(status)")
        
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
