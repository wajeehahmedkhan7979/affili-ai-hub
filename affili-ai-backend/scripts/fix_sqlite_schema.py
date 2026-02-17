import sqlite3
import os

DB_PATH = "affili_ai.db"

def patch_schema():
    if not os.path.exists(DB_PATH):
        print(f"❌ {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check current columns
        cursor.execute("SELECT * FROM users LIMIT 0")
        columns = [description[0] for description in cursor.description]
        
        # Add last_login_at if missing
        if "last_login_at" not in columns:
            print("➕ Adding column: last_login_at")
            cursor.execute("ALTER TABLE users ADD COLUMN last_login_at DATETIME")
            
        # Add refresh_token_hash if missing
        if "refresh_token_hash" not in columns:
            print("➕ Adding column: refresh_token_hash")
            cursor.execute("ALTER TABLE users ADD COLUMN refresh_token_hash VARCHAR(255)")
            
        conn.commit()
        print("✅ Schema patch complete.")
        
    except Exception as e:
        print(f"❌ Schema patch failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    patch_schema()
