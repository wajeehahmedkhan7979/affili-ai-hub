import sys
from sqlalchemy import text
from app.db.session import SessionLocal

def check_schema():
    db = SessionLocal()
    try:
        for table in ['response_pool', 'form_field_embeddings']:
            res = db.execute(text(f"SELECT column_name, udt_name FROM information_schema.columns WHERE table_name = '{table}' AND column_name = 'embedding'")).fetchone()
            if res:
                print(f"TABLE: {table} | COLUMN: {res[0]} | UDT: {res[1]}")
            else:
                print(f"TABLE: {table} | COLUMN NOT FOUND")
        
        ext = db.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector'")).fetchone()
        print(f"EXTENSION VECTOR: {'INSTALLED' if ext else 'MISSING'}")
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_schema()
