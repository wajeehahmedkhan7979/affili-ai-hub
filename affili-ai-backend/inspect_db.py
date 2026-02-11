import sqlite3
import uuid

def inspect_db():
    conn = sqlite3.connect('affili_ai.db')
    cursor = conn.cursor()
    
    print("--- TABLE SCHEMAS ---")
    tables = ['tasks', 'tenants', 'users', 'tenant_runtime_flags']
    for table in tables:
        print(f"\nSchema for {table}:")
        try:
            cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}'")
            row = cursor.fetchone()
            if row:
                print(row[0])
            else:
                print("Table not found.")
        except Exception as e:
            print(f"Error: {e}")

    print("\n--- DATA INTEGRITY CHECK (Non-text UUIDs) ---")
    try:
        cursor.execute("SELECT id, typeof(id) FROM tasks WHERE typeof(id) != 'text'")
        bad_tasks = cursor.fetchall()
        print(f"Bad tasks: {len(bad_tasks)}")
        for r in bad_tasks[:5]:
            print(f"ID: {r[0]}, Type: {r[1]}")
            
        cursor.execute("SELECT id, typeof(id) FROM tenants WHERE typeof(id) != 'text'")
        bad_tenants = cursor.fetchall()
        print(f"Bad tenants: {len(bad_tenants)}")
        for r in bad_tenants[:5]:
            print(f"ID: {r[0]}, Type: {r[1]}")
    except Exception as e:
        print(f"Error: {e}")
        
    conn.close()

if __name__ == "__main__":
    inspect_db()
