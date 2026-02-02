"""
Migration: Add authentication fields to users table.
"""
import sqlite3
import os

def migrate():
    db_path = "affili_ai.db"
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("Adding hashed_password and refresh_token_version to users table...")
    
    try:
        # Add hashed_password
        cursor.execute("ALTER TABLE users ADD COLUMN hashed_password VARCHAR(255)")
        print("Added hashed_password column.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("Column hashed_password already exists.")
        else:
            print(f"Error adding hashed_password: {e}")

    try:
        # Add refresh_token_version
        cursor.execute("ALTER TABLE users ADD COLUMN refresh_token_version INTEGER DEFAULT 1")
        print("Added refresh_token_version column.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("Column refresh_token_version already exists.")
        else:
            print(f"Error adding refresh_token_version: {e}")

    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
