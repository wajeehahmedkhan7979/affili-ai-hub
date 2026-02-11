import sys
from sqlalchemy import text
from app.db.session import SessionLocal

def migrate_to_vector():
    print("Migrating database to use pgvector...")
    db = SessionLocal()
    try:
        # 1. Enable extension
        print("Enabling vector extension...")
        db.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        db.commit()
        print("✓ Extension enabled.")

        # 2. Migrate response_pool
        print("Checking response_pool.embedding...")
        res = db.execute(text("SELECT udt_name FROM information_schema.columns WHERE table_name = 'response_pool' AND column_name = 'embedding'")).fetchone()
        if not res:
            print("  Column missing. Adding embedding as vector(384)...")
            db.execute(text("ALTER TABLE response_pool ADD COLUMN embedding vector(384);"))
            db.commit()
            print("✓ response_pool column added.")
        elif res[0] != 'vector':
            print(f"  Current type: {res[0]}. Converting to vector(384)...")
            db.execute(text("""
                ALTER TABLE response_pool 
                ALTER COLUMN embedding TYPE vector(384) 
                USING (
                    CASE 
                        WHEN embedding IS NULL THEN NULL 
                        ELSE trim(both '[]' from embedding::text)::vector 
                    END
                );
            """))
            db.commit()
            print("✓ response_pool migrated.")
        else:
            print("  response_pool already has vector type.")

        # 3. Migrate form_field_embeddings
        print("Checking form_field_embeddings.embedding...")
        res = db.execute(text("SELECT udt_name FROM information_schema.columns WHERE table_name = 'form_field_embeddings' AND column_name = 'embedding'")).fetchone()
        if not res:
            print("  Column missing. Adding embedding as vector(384)...")
            db.execute(text("ALTER TABLE form_field_embeddings ADD COLUMN embedding vector(384);"))
            db.commit()
            print("✓ form_field_embeddings column added.")
        elif res[0] != 'vector':
            print(f"  Current type: {res[0]}. Converting to vector(384)...")
            db.execute(text("""
                ALTER TABLE form_field_embeddings 
                ALTER COLUMN embedding TYPE vector(384) 
                USING (
                    CASE 
                        WHEN embedding IS NULL THEN NULL 
                        ELSE trim(both '[]' from embedding::text)::vector 
                    END
                );
            """))
            db.commit()
            print("✓ form_field_embeddings migrated.")
        else:
            print("  form_field_embeddings already has vector type.")

    except Exception as e:
        print(f"Migration failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    migrate_to_vector()
