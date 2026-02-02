"""
Migration script to add tenant_id to task_metrics table.

Ensures backward compatibility with default tenant.
"""

import sqlite3
import os


DEFAULT_TENANT_ID = "00000000-0000-0000-0000-000000000000"


def migrate():
    """Add tenant_id column to task_metrics table."""
    db_path = os.path.join(os.getcwd(), "affili_ai.db")
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    print(f"Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(task_metrics)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if "tenant_id" in columns:
            print("✓ Column 'tenant_id' already exists in task_metrics table. Skipping migration.")
            return
        
        # Add tenant_id column with default
        print("Adding 'tenant_id' column to task_metrics table...")
        cursor.execute(f"""
            ALTER TABLE task_metrics 
            ADD COLUMN tenant_id CHAR(36) DEFAULT '{DEFAULT_TENANT_ID}' NOT NULL
        """)
        
        # Update existing rows
        print("Setting default tenant for existing metrics...")
        cursor.execute(f"""
            UPDATE task_metrics 
            SET tenant_id = '{DEFAULT_TENANT_ID}' 
            WHERE tenant_id IS NULL OR tenant_id = ''
        """)
        
        # Create index
        print("Creating index on tenant_id...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS ix_task_metrics_tenant_id ON task_metrics(tenant_id)
        """)
        
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
