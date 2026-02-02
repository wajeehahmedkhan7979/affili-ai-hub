"""
Migration script to create users table with RBAC.

Phase 7.2
"""

import sqlite3
import os


def migrate():
    """Create users table."""
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
            WHERE type='table' AND name='users'
        """)
        
        if cursor.fetchone():
            print("✓ Table 'users' already exists. Skipping migration.")
            return
        
        # Create users table
        print("Creating 'users' table...")
        cursor.execute("""
            CREATE TABLE users (
                id CHAR(36) PRIMARY KEY,
                tenant_id CHAR(36) NOT NULL,
                email VARCHAR(255) NOT NULL,
                role VARCHAR(20) NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(tenant_id) REFERENCES tenants(id),
                UNIQUE(tenant_id, email)
            )
        """)
        
        # Create indexes
        print("Creating indexes...")
        cursor.execute("CREATE INDEX ix_users_tenant_id ON users(tenant_id)")
        
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
