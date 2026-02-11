import sys
from sqlalchemy import text
from app.db.session import SessionLocal
from pgvector.sqlalchemy import Vector

def check_vector():
    print("Verifying pgvector extension...")
    db = SessionLocal()
    try:
        # 1. Check extension
        res = db.execute(text("SELECT * FROM pg_extension WHERE extname = 'vector'")).fetchone()
        if res:
            print("Extension 'vector' is INSTALLED.")
        else:
            print("Extension 'vector' is MISSING.")
            return

        # 2. Test vector operation
        # We can try a simple query if we have data, or just a SELECT with vector math
        try:
            # Simple vector math test in SQL
            vec_test = db.execute(text("SELECT '[1,2,3]'::vector + '[4,5,6]'::vector")).scalar()
            print(f"Vector math test passed: {vec_test}")
        except Exception as e:
            print(f"Vector math failed: {e}")

    except Exception as e:
        print(f"Verification failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_vector()
