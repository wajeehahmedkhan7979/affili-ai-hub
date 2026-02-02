import sqlite3
import os

DB_PATH = "affili_ai.db"

def add_column():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(tasks)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if "last_heartbeat" in columns:
            print("Column 'last_heartbeat' already exists.")
        else:
            print("Adding 'last_heartbeat' column...")
            cursor.execute("ALTER TABLE tasks ADD COLUMN last_heartbeat DATETIME")
            conn.commit()
            print("Column added successfully.")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    add_column()
