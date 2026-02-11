import sys
import os
from sqlalchemy import create_engine, text
from app.core.config import get_settings

def list_tables():
    settings = get_settings()
    url = settings.DATABASE_URL
    print(f"Connecting to: {url}")
    
    # Force psycopg2 driver if needed, or rely on default
    # The error came from 'psycopg' (v3), so let's try to match
    
    engine = create_engine(url)
    
    with engine.connect() as conn:
        print("Connected. Querying information_schema.tables...")
        result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"))
        tables = [row[0] for row in result]
        print("\nExisting Tables:")
        for t in tables:
            print(f" - {t}")
            
        if "tenant_usage" in tables:
            print("\nSUCCESS: 'tenant_usage' table found.")
        else:
            print("\nFAILURE: 'tenant_usage' table NOT found.")

if __name__ == "__main__":
    try:
        list_tables()
    except Exception as e:
        print(f"Error: {e}")
