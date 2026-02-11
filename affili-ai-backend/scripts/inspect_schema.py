import sys
from sqlalchemy import text
from app.db.session import SessionLocal

def inspect_db():
    print("Inspecting Database Schema...")
    db = SessionLocal()
    try:
        tables = ['response_pool', 'form_field_embeddings']
        for table in tables:
            print(f"\nTable: {table}")
            # Query standard columns
            stmt = text(f"""
                SELECT column_name, data_type, udt_name 
                FROM information_schema.columns 
                WHERE table_name = '{table}';
            """)
            results = db.execute(stmt).fetchall()
            if not results:
                print(f"  Table '{table}' NOT FOUND.")
                continue
                
            for col, dtype, udt in results:
                print(f"  Column: {col:20} | Type: {dtype:15} | UDT: {udt}")
                
        # Check pg_type for vector
        res = db.execute(text("SELECT typname FROM pg_type WHERE typname = 'vector'")).fetchall()
        print(f"\nVector Type in pg_type: {'FOUND' if res else 'MISSING'}")

    except Exception as e:
        print(f"Inspection failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    inspect_db()
