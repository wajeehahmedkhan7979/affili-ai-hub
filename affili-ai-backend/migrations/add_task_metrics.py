"""
Migration script to create task_metrics table.

Run this script to add metrics tracking for Phase 6.
"""

import sqlite3
import os


def migrate():
    """Create task_metrics table."""
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
            WHERE type='table' AND name='task_metrics'
        """)
        
        if cursor.fetchone():
            print("✓ Table 'task_metrics' already exists. Skipping migration.")
            return
        
        # Create task_metrics table
        print("Creating 'task_metrics' table...")
        cursor.execute("""
            CREATE TABLE task_metrics (
                id CHAR(36) PRIMARY KEY,
                task_id CHAR(36) NOT NULL,
                program_name VARCHAR(255),
                task_type VARCHAR(50) NOT NULL,
                agent_id VARCHAR(255),
                agent_pool VARCHAR(100),
                duration_seconds REAL,
                success BOOLEAN NOT NULL,
                failure_type VARCHAR(50),
                captcha_detected BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES tasks(id)
            )
        """)
        
        # Create indexes
        print("Creating indexes...")
        cursor.execute("CREATE INDEX ix_task_metrics_task_id ON task_metrics(task_id)")
        cursor.execute("CREATE INDEX ix_task_metrics_program_name ON task_metrics(program_name)")
        cursor.execute("CREATE INDEX ix_task_metrics_task_type ON task_metrics(task_type)")
        cursor.execute("CREATE INDEX ix_task_metrics_agent_id ON task_metrics(agent_id)")
        cursor.execute("CREATE INDEX ix_task_metrics_agent_pool ON task_metrics(agent_pool)")
        cursor.execute("CREATE INDEX ix_task_metrics_failure_type ON task_metrics(failure_type)")
        cursor.execute("CREATE INDEX ix_task_metrics_captcha_detected ON task_metrics(captcha_detected)")
        cursor.execute("CREATE INDEX ix_task_metrics_created_at ON task_metrics(created_at)")
        
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
