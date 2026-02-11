"""
Initialize Alembic migration system for AFFILI-AI.

This script sets up Alembic with proper configuration and runs all migrations.
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import subprocess

load_dotenv()

def run_migrations():
    """Run all pending Alembic migrations."""
    print("="*60)
    print("AFFILI-AI Database Migration Runner")
    print("="*60)
    
    # Check database URL
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not set")
        return False
    
    # Check if using pooler (pgbouncer)
    if "pgbouncer=true" in db_url:
        print("\n⚠️  WARNING: pgbouncer pooler detected")
        print("   Migrations require direct connection (port 5432 not 6543)")
        print("   Please temporarily use direct connection or run via Supabase SQL Editor")
        return False
    
    print(f"\n📡 Database: {db_url.split('@')[1] if '@' in db_url else 'configured'}")
    
    try:
        # Test connectivity
        print("\n🔍 Testing database connectivity...")
        engine = create_engine(db_url, pool_pre_ping=True)
        
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            print("✅ Database reachable")
        
        # Check for pgvector
        print("\n🔍 Checking pgvector extension...")
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT EXISTS(
                    SELECT 1 FROM pg_extension WHERE extname = 'vector'
                )
            """))
            has_vector = result.fetchone()[0]
            
            if not has_vector:
                print("⚠️  pgvector not enabled")
                print("   Run: CREATE EXTENSION IF NOT EXISTS vector;")
                print("   Attempting to enable...")
                
                try:
                    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                    conn.commit()
                    print("✅ pgvector extension enabled")
                except Exception as e:
                    print(f   "❌ Could not enable pgvector: {e}")
                    print("   Please enable manually via Supabase SQL Editor")
                    return False
            else:
                print("✅ pgvector already enabled")
        
        # Run Alembic migrations
        print("\n🚀 Running Alembic migrations...")
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Migrations completed successfully")
            print("\n" + result.stdout)
            
            # Show final state
            print("\n📊 Migration status:")
            result = subprocess.run(
                ["alembic", "current"],
                capture_output=True,
                text=True
            )
            print(result.stdout)
            
            return True
        else:
            print(f"❌ Migration failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = run_migrations()
    
    if success:
        print("\n" + "="*60)
        print("MIGRATIONS: SUCCESS")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("MIGRATIONS: FAILED")
        print("="*60)
        print("\n💡 Next steps:")
        print("   1. Use direct DB connection (not pooler)")
        print("   2. Enable pgvector via Supabase SQL Editor")
        print("   3. Run: alembic upgrade head")
    
    sys.exit(0 if success else 1)
