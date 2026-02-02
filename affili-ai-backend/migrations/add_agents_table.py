"""
Migration script to create agents table.

Run this script to add agent reputation tracking for Phase 6.
"""

import sqlite3
import os


def migrate():
    """Create agents table."""
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
            WHERE type='table' AND name='agents'
        """)
        
        if cursor.fetchone():
            print("✓ Table 'agents' already exists. Skipping migration.")
            return
        
        # Create agents table
        print("Creating 'agents' table...")
        cursor.execute("""
            CREATE TABLE agents (
                id VARCHAR(255) PRIMARY KEY,
                pool VARCHAR(100) DEFAULT 'default',
                total_tasks INTEGER DEFAULT 0,
                successful_tasks INTEGER DEFAULT 0,
                failed_tasks INTEGER DEFAULT 0,
                captcha_count INTEGER DEFAULT 0,
                timeout_count INTEGER DEFAULT 0,
                health_score REAL DEFAULT 100.0,
                last_seen TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create index on pool
        print("Creating index on pool...")
        cursor.execute("CREATE INDEX ix_agents_pool ON agents(pool)")
        
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
