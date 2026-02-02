"""
Migration script to add agent_pool column to tasks table.

Run this script to update the database schema for Phase 6.
"""

import sqlite3
import os

def migrate():
    """Add agent_pool column to tasks table."""
    db_path = os.path.join(os.getcwd(), "affili_ai.db")
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    print(f"Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(tasks)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if "agent_pool" in columns:
            print("✓ Column 'agent_pool' already exists. Skipping migration.")
            return
        
        # Add agent_pool column
        print("Adding 'agent_pool' column to tasks table...")
        cursor.execute("""
            ALTER TABLE tasks 
            ADD COLUMN agent_pool VARCHAR(100) DEFAULT 'default'
        """)
        
        # Create index on agent_pool
        print("Creating index on agent_pool...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS ix_tasks_agent_pool ON tasks(agent_pool)
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
