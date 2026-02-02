
import sqlite3
import uuid

def check():
    conn = sqlite3.connect("affili_ai.db")
    cursor = conn.cursor()
    
    print("--- Table Schemas ---")
    tables = ["tenants", "users", "billing_plans", "tenant_billing"]
    for t in tables:
        schema = cursor.execute(f"SELECT sql FROM sqlite_master WHERE name='{t}'").fetchone()
        if schema:
            print(f"Table {t} schema:\n{schema[0]}\n")
            
    print("--- Billing Plans Data ---")
    plans = cursor.execute("SELECT id, name FROM billing_plans").fetchall()
    for p in plans:
        print(f"Plan: {p[1]}, ID: {p[0]}, Type: {type(p[0])}")
            
    print("\n--- Tenant Billing Data ---")
    billings = cursor.execute("SELECT tenant_id, plan_id, status FROM tenant_billing").fetchall()
    for b in billings:
        print(f"Tenant: {b[0]}, Plan: {b[1]}, Status: {b[2]}")
        
    print("\n--- Tenants Data (first 2) ---")
    ttenants = cursor.execute("SELECT id, name FROM tenants LIMIT 2").fetchall()
    for t in ttenants:
        print(f"Tenant ID: {t[0]}, Name: {t[1]}, Type: {type(t[0])}")
        
    conn.close()

if __name__ == "__main__":
    check()
