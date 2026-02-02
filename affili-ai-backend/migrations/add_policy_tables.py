"""
Migration: Add policies table.
"""
import sqlite3
import os
import uuid

def migrate():
    db_path = "affili_ai.db"
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("Creating policies table...")
    
    # policies
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS policies (
        id CHAR(32) PRIMARY KEY,
        tenant_id CHAR(32) NOT NULL,
        name VARCHAR(255) NOT NULL,
        description TEXT,
        rules TEXT NOT NULL,
        is_active BOOLEAN DEFAULT 1,
        created_at DATETIME,
        updated_at DATETIME,
        FOREIGN KEY (tenant_id) REFERENCES tenants (id)
    )
    """)

    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
