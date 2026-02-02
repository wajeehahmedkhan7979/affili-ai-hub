"""
Migration: Add billing tables.
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

    print("Recreating billing_plans and tenant_billing tables...")
    
    # Drop existing if any to ensure clean state
    cursor.execute("DROP TABLE IF EXISTS tenant_billing")
    cursor.execute("DROP TABLE IF EXISTS billing_plans")
    
    # billing_plans
    cursor.execute("""
    CREATE TABLE billing_plans (
        id CHAR(32) PRIMARY KEY,
        name VARCHAR(50) NOT NULL UNIQUE,
        task_limit INTEGER DEFAULT 10,
        minute_limit INTEGER DEFAULT 60,
        is_active BOOLEAN DEFAULT 1
    )
    """)
    
    # tenant_billing
    cursor.execute("""
    CREATE TABLE tenant_billing (
        tenant_id CHAR(32) PRIMARY KEY,
        plan_id CHAR(32) NOT NULL,
        status VARCHAR(20) DEFAULT 'ACTIVE',
        cycle_start DATETIME,
        FOREIGN KEY (tenant_id) REFERENCES tenants (id),
        FOREIGN KEY (plan_id) REFERENCES billing_plans (id)
    )
    """)

    # Seed initial plans
    plans = [
        (uuid.uuid4().hex, "Free", 10, 60, 1),
        (uuid.uuid4().hex, "Pro", 100, 600, 1),
        (uuid.uuid4().hex, "Enterprise", 1000, 6000, 1)
    ]
    
    for p in plans:
        cursor.execute("INSERT OR IGNORE INTO billing_plans (id, name, task_limit, minute_limit, is_active) VALUES (?, ?, ?, ?, ?)", p)

    conn.commit()
    conn.close()
    print("Migration and seeding complete.")

if __name__ == "__main__":
    migrate()
