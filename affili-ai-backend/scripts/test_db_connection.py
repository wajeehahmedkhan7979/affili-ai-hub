"""
Test database connectivity for AFFILI-AI HUB.

Validates:
1. PostgreSQL connection via Supabase pooler
2. pgvector extension availability
3. Basic query execution
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def test_connection():
    """Test basic database connectivity."""
    print("="*60)
    print("AFFILI-AI Database Connection Test")
    print("="*60)
    
    if not DATABASE_URL:
        print("❌ DATABASE_URL not found in environment")
        return False
    
    print(f"\n📡 Connecting to: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'database'}")
    
    try:
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        
        with engine.connect() as conn:
            # Test 1: Basic connectivity
            result = conn.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            assert row[0] == 1
            print("✅ Basic connectivity: PASS")
            
            # Test 2: PostgreSQL version
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ PostgreSQL version: {version.split(',')[0]}")
            
            # Test 3: Check for pgvector extension
            result = conn.execute(text("""
                SELECT EXISTS(
                    SELECT 1 FROM pg_extension WHERE extname = 'vector'
                )
            """))
            has_pgvector = result.fetchone()[0]
            if has_pgvector:
                print("✅ pgvector extension: ENABLED")
            else:
                print("⚠️  pgvector extension: NOT ENABLED")
                print("   Run: CREATE EXTENSION IF NOT EXISTS vector;")
            
            # Test 4: Check existing tables
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]
            
            if tables:
                print(f"\n✅ Existing tables ({len(tables)}):")
                for table in tables:
                    print(f"   - {table}")
            else:
                print("\n⚠️  No tables found - migrations need to run")
            
            print("\n" + "="*60)
            print("DATABASE CONNECTION: SUCCESS")
            print("="*60)
            return True
            
    except Exception as e:
        print(f"\n❌ Connection failed: {str(e)}")
        print("\n" + "="*60)
        print("DATABASE CONNECTION: FAILED")
        print("="*60)
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
