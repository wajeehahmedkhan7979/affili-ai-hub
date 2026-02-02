"""
Migration: Add webhook tables.
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

    print("Creating webhook_configs and webhook_deliveries tables...")
    
    # webhook_configs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS webhook_configs (
        id CHAR(32) PRIMARY KEY,
        tenant_id CHAR(32) NOT NULL,
        url VARCHAR(500) NOT NULL,
        secret VARCHAR(255) NOT NULL,
        event_types TEXT NOT NULL,
        is_active BOOLEAN DEFAULT 1,
        created_at DATETIME,
        FOREIGN KEY (tenant_id) REFERENCES tenants (id)
    )
    """)
    
    # webhook_deliveries
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS webhook_deliveries (
        id CHAR(32) PRIMARY KEY,
        tenant_id CHAR(32) NOT NULL,
        config_id CHAR(32) NOT NULL,
        event_type VARCHAR(50) NOT NULL,
        payload TEXT NOT NULL,
        status_code INTEGER,
        response_body TEXT,
        success BOOLEAN DEFAULT 0,
        attempt_count INTEGER DEFAULT 1,
        delivered_at DATETIME,
        FOREIGN KEY (tenant_id) REFERENCES tenants (id),
        FOREIGN KEY (config_id) REFERENCES webhook_configs (id)
    )
    """)

    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
