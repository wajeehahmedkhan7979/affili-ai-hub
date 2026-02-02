"""
Migration script to create tenants table and default tenant.

Run this script to add multi-tenant support for Phase 7.
"""

import sqlite3
import os
import uuid


DEFAULT_TENANT_ID = "00000000-0000-0000-0000-000000000000"
DEFAULT_TENANT_NAME = "default"


def migrate():
    """Create tenants table and insert default tenant."""
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
            WHERE type='table' AND name='tenants'
        """)
        
        if cursor.fetchone():
            print("✓ Table 'tenants' already exists. Skipping migration.")
            return
        
        # Create tenants table
        print("Creating 'tenants' table...")
        cursor.execute("""
            CREATE TABLE tenants (
                id CHAR(36) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes
        print("Creating indexes...")
        cursor.execute("CREATE INDEX ix_tenants_is_active ON tenants(is_active)")
        cursor.execute("CREATE INDEX ix_tenants_created_at ON tenants(created_at)")
        
        # Insert default tenant for backward compatibility
        print(f"Inserting default tenant (ID: {DEFAULT_TENANT_ID})...")
        cursor.execute("""
            INSERT INTO tenants (id, name, is_active, created_at, updated_at)
            VALUES (?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """, (DEFAULT_TENANT_ID, DEFAULT_TENANT_NAME))
        
        conn.commit()
        print("✓ Migration completed successfully!")
        print(f"✓ Default tenant created: {DEFAULT_TENANT_NAME}")
        
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
