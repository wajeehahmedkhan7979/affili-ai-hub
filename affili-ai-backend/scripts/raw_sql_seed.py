import sqlite3
import uuid

DB_PATH = "affili_ai.db"
DEFAULT_TENANT_ID = "00000000-0000-0000-0000-000000000000"
ADMIN_EMAIL = "admin@example.com"
# Hashed 'password' using bcrypt 4.0.1 (verified earlier)
HASHED_PW = "$2b$12$QVXVnzscpges8yOtB9z7J.Xu1Ylmboe5McAW72sKtSix0.QVuRVyC"

def seed():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 1. Ensure Tenant exists
        cursor.execute("SELECT id FROM tenants WHERE id = ?", (DEFAULT_TENANT_ID,))
        if not cursor.fetchone():
            print(f"Adding tenant {DEFAULT_TENANT_ID}")
            cursor.execute("INSERT INTO tenants (id, name, is_active) VALUES (?, ?, ?)", 
                           (DEFAULT_TENANT_ID, "Default Tenant", 1))
        
        # 2. Ensure Admin User exists
        cursor.execute("SELECT id FROM users WHERE email = ?", (ADMIN_EMAIL,))
        res = cursor.fetchone()
        if not res:
            user_id = str(uuid.uuid4())
            print(f"Adding admin user {ADMIN_EMAIL} with ID {user_id}")
            cursor.execute("""
                INSERT INTO users (id, tenant_id, email, hashed_password, role, is_active, last_login_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, DEFAULT_TENANT_ID, ADMIN_EMAIL, HASHED_PW, "admin", 1, None))
        else:
            print(f"Updating existing admin user {ADMIN_EMAIL}")
            cursor.execute("UPDATE users SET hashed_password = ?, tenant_id = ?, is_active = 1 WHERE email = ?",
                           (HASHED_PW, DEFAULT_TENANT_ID, ADMIN_EMAIL))
        
        conn.commit()
        print("✅ RAW SQL SEED SUCCESSFUL.")
        
        # Verify
        cursor.execute("SELECT email, tenant_id FROM users")
        print(f"Current users: {cursor.fetchall()}")
        
    except Exception as e:
        print(f"❌ SQL Seed failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    seed()
