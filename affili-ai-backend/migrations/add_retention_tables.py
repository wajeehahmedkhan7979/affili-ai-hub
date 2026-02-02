"""
Migration: Add retention tables and legal hold flag.
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

    print("Adding legal_hold to tenants table...")
    try:
        cursor.execute("ALTER TABLE tenants ADD COLUMN legal_hold BOOLEAN DEFAULT 0")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("Column legal_hold already exists.")
        else:
            print(f"Error adding legal_hold: {e}")

    print("Creating retention_rules table...")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS retention_rules (
        id CHAR(32) PRIMARY KEY,
        tenant_id CHAR(32) NOT NULL,
        entity_type VARCHAR(50) NOT NULL,
        retention_days INTEGER DEFAULT 90,
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
