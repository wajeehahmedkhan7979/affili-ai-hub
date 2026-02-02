import sqlite3
import os

DB_PATH = "affili_ai.db"

def add_discovery_columns():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check existing columns
        cursor.execute("PRAGMA table_info(programs)")
        columns = [info[1] for info in cursor.fetchall()]
        
        migrations = []
        
        if "base_url" not in columns:
            migrations.append("ALTER TABLE programs ADD COLUMN base_url VARCHAR(500)")
        if "signup_url" not in columns:
            migrations.append("ALTER TABLE programs ADD COLUMN signup_url VARCHAR(500)")
        if "source" not in columns:
            migrations.append("ALTER TABLE programs ADD COLUMN source VARCHAR(50) DEFAULT 'manual'")
        if "confidence_score" not in columns:
            migrations.append("ALTER TABLE programs ADD COLUMN confidence_score FLOAT")
        
        if migrations:
            print(f"Running {len(migrations)} migrations...")
            for migration in migrations:
                print(f"  {migration}")
                cursor.execute(migration)
            conn.commit()
            print("Migrations completed successfully.")
        else:
            print("All columns already exist.")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    add_discovery_columns()
