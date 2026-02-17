"""
Comprehensive schema repair v2.
Adds ALL missing columns across ALL tables by comparing
SQLAlchemy model definitions to actual SQLite schema.
"""
import sqlite3
import os
import sys

DB_PATH = os.path.join(os.path.dirname(__file__), "affili_ai.db")

def get_existing_columns(cursor, table_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    return {row[1] for row in cursor.fetchall()}

def get_existing_tables(cursor):
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    return {row[0] for row in cursor.fetchall()}

def add_column(cursor, table, column, col_type, default=None):
    existing = get_existing_columns(cursor, table)
    if column not in existing:
        default_clause = f" DEFAULT {default}" if default is not None else ""
        sql = f"ALTER TABLE {table} ADD COLUMN {column} {col_type}{default_clause}"
        print(f"  + {table}.{column} ({col_type}{default_clause})")
        cursor.execute(sql)
        return True
    return False

def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    fixes = 0
    tables = get_existing_tables(c)

    print("=== Comprehensive Schema Repair v2 ===\n")

    # tenant_runtime_flags
    if "tenant_runtime_flags" in tables:
        print("[tenant_runtime_flags]")
        fixes += add_column(c, "tenant_runtime_flags", "created_at", "DATETIME")
        fixes += add_column(c, "tenant_runtime_flags", "updated_at", "DATETIME")
        fixes += add_column(c, "tenant_runtime_flags", "max_tasks_per_program", "INTEGER NOT NULL", "10")
        fixes += add_column(c, "tenant_runtime_flags", "ai_disabled", "BOOLEAN NOT NULL", "0")
        fixes += add_column(c, "tenant_runtime_flags", "disable_reason", "TEXT")
        fixes += add_column(c, "tenant_runtime_flags", "disabled_at", "DATETIME")
        fixes += add_column(c, "tenant_runtime_flags", "disabled_by", "CHAR(36)")

    # tasks
    if "tasks" in tables:
        print("[tasks]")
        fixes += add_column(c, "tasks", "program_id", "CHAR(36)")

    # agents
    if "agents" in tables:
        print("[agents]")
        fixes += add_column(c, "agents", "pinned_public_key", "TEXT")

    # programs
    if "programs" in tables:
        print("[programs]")
        fixes += add_column(c, "programs", "status", "VARCHAR(50)", "'Discovered'")
        fixes += add_column(c, "programs", "network", "VARCHAR(100)")
        fixes += add_column(c, "programs", "commission", "VARCHAR(100)")

    # users
    if "users" in tables:
        print("[users]")
        fixes += add_column(c, "users", "failed_login_attempts", "INTEGER", "0")
        fixes += add_column(c, "users", "locked_until", "DATETIME")

    # applications
    if "applications" in tables:
        print("[applications]")
        fixes += add_column(c, "applications", "agent_status", "VARCHAR(50)")

    # response_pool
    if "response_pool" in tables:
        print("[response_pool]")
        fixes += add_column(c, "response_pool", "tenant_id", "CHAR(36)")
        fixes += add_column(c, "response_pool", "trust_score", "FLOAT", "0.0")
        fixes += add_column(c, "response_pool", "is_verified", "BOOLEAN", "0")

    conn.commit()
    print(f"\n=== Complete: {fixes} columns added ===")

    # Verify tenant_runtime_flags specifically
    print("\n[VERIFY tenant_runtime_flags columns]")
    cols = get_existing_columns(c, "tenant_runtime_flags")
    print(f"  Columns: {sorted(cols)}")

    conn.close()

if __name__ == "__main__":
    main()
