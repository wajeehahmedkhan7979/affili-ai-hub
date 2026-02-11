import sys
import os
from sqlalchemy import text
from app.db.session import SessionLocal

def migrate_vector():
    print("Migrating ResponsePool to use Vector type...")
    db = SessionLocal()
    try:
        # 1. Ensure extension exists
        db.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        
        # 2. Check if column is already vector (simplified: just try ALTER)
        # We need to cast JSON to Vector.
        # JSON array -> text -> vector
        # Handle case where column might already be vector (catch error?) or check schema.
        # Simple approach: ALTER TABLE ... TYPE ... USING ...
        
        print("Altering table column...")
        # Note: If embedding is null, safe. If JSON array, cast.
        # Casting straight from jsonb/json to vector might fail if not explicit.
        # CAST(embedding::text as vector) might be needed.
        
        migration_sql = """
        DO $$
        BEGIN
            -- Check if column type is already vector
            IF EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name = 'response_pool' 
                AND column_name = 'embedding' 
                AND data_type = 'USER-DEFINED' 
                AND udt_name = 'vector'
            ) THEN
                RAISE NOTICE 'Column is already vector type';
            ELSE
                -- Alter column
                -- Make sure to handle existing JSON data by casting to text then vector
                -- Only works if data is proper array format in text
                ALTER TABLE response_pool 
                ALTER COLUMN embedding TYPE vector(384) 
                USING (
                    CASE 
                        WHEN embedding IS NULL THEN NULL 
                        ELSE trim(both '[]' from embedding::text)::vector
                    END
                );
            END IF;
        END $$;
        """
        
        db.execute(text(migration_sql))
        db.commit()
        print("✓ Migration successful")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    migrate_vector()
