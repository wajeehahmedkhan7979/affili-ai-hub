import os
import asyncio
import psycopg
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Load environment
load_dotenv(".env.production")
DATABASE_URL = os.getenv("DATABASE_URL")

# For SQLAlchemy 2.0 + psycopg v3, ensure the scheme is correct
if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    SQLALCHEMY_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)
else:
    SQLALCHEMY_DATABASE_URL = DATABASE_URL

# Strip pgbouncer=true for SQLAlchemy if it causes issues, 
# although usually it's ignored if not known.
if SQLALCHEMY_DATABASE_URL and "?pgbouncer=true" in SQLALCHEMY_DATABASE_URL:
    # Just a simple string replace for stability in this test script
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("?pgbouncer=true", "")

# For raw psycopg v3 connection, strip pgbouncer=true as it's not a valid param for connect()
# but it IS used by some poolers for routing.
RAW_DATABASE_URL = DATABASE_URL
if RAW_DATABASE_URL and "pgbouncer=true" in RAW_DATABASE_URL:
    if "?" in RAW_DATABASE_URL:
        RAW_DATABASE_URL = RAW_DATABASE_URL.replace("pgbouncer=true", "")
        RAW_DATABASE_URL = RAW_DATABASE_URL.replace("?&", "?")
        RAW_DATABASE_URL = RAW_DATABASE_URL.rstrip("?")

def test_raw_connectivity():
    print("--- 1. Testing Raw Connectivity (psycopg v3) ---")
    try:
        # psycopg v3 uses 'connect' just like v2
        conn = psycopg.connect(RAW_DATABASE_URL)
        cur = conn.cursor()
        cur.execute("SELECT version();")
        print(f"Success! Version: {cur.fetchone()[0]}")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"FAILED: {e}")

def test_sqlalchemy_session():
    print("\n--- 2. Testing SQLAlchemy Session ---")
    try:
        print(f"Using URL: {SQLALCHEMY_DATABASE_URL}")
        engine = create_engine(SQLALCHEMY_DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        result = db.execute(text("SELECT current_database();"))
        print(f"Success! Connected to DB: {result.fetchone()[0]}")
        db.close()
    except Exception as e:
        print(f"FAILED: {e}")

async def test_concurrency_skip_locked():
    print("\n--- 3. Testing SKIP LOCKED (Concurrency) ---")
    try:
        engine = create_engine(SQLALCHEMY_DATABASE_URL)
        
        # We'll use two separate connections from the pool
        with engine.connect() as conn1:
            with engine.connect() as conn2:
                # Start transaction 1
                trans1 = conn1.begin()
                try:
                    # Check if tasks table exists
                    table_check = conn1.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'tasks')")).fetchone()[0]
                    if not table_check:
                        print("Tasks table does not exist. Run migrations first.")
                        trans1.rollback()
                        return

                    # Claim a task in T1
                    res1 = conn1.execute(text("SELECT id FROM tasks WHERE status = 'PENDING' LIMIT 1 FOR UPDATE SKIP LOCKED")).fetchone()
                    if not res1:
                        print("No PENDING tasks to test concurrency. Skipping.")
                        trans1.rollback()
                        return
                    
                    task_id = res1[0]
                    print(f"Transaction 1 locked Task ID: {task_id}")

                    # Try to claim same task in T2
                    res2 = conn2.execute(text("SELECT id FROM tasks WHERE status = 'PENDING' LIMIT 1 FOR UPDATE SKIP LOCKED")).fetchone()
                    
                    if res2:
                        print(f"Transaction 2 locked different Task ID: {res2[0]}")
                        print("✅ SKIP LOCKED is working (Parallel claiming).")
                    else:
                        print("Transaction 2 found no tasks. (Maybe only 1 task existed).")
                    
                    trans1.commit()
                except Exception as e:
                    trans1.rollback()
                    print(f"FAILED during concurrency test: {e}")
    except Exception as e:
        print(f"FAILED to initialize concurrency test: {e}")

def verify_jsonb_support():
    print("\n--- 4. Verifying JSONB Support ---")
    try:
        engine = create_engine(SQLALCHEMY_DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text("SELECT '{\"key\": \"value\"}'::jsonb;"))
            print("✅ JSONB is supported.")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    if not DATABASE_URL:
        print("ERROR: DATABASE_URL not found in .env.production")
        exit(1)
    
    test_raw_connectivity()
    test_sqlalchemy_session()
    verify_jsonb_support()
    asyncio.run(test_concurrency_skip_locked())
