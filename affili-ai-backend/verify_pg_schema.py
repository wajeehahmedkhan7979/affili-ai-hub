import sys
from sqlalchemy import create_engine, text
from sqlalchemy.schema import CreateTable
from app.db.base import Base
import app.models  # Ensure all models are loaded

def verify_pg_schema():
    print("--- AFFILI-AI HUB v1.1 POSTGRES PARITY VALIDATION (STATIC) ---")
    
    # Create a mock postgres engine (doesn't need connection)
    engine = create_engine("postgresql+psycopg://postgres:postgres@localhost/mock_db")
    
    print("\n[1] Verifying Postgres DDL Generation for Core Models...")
    
    models_to_verify = Base.metadata.sorted_tables
    
    critical_pg_types = ["JSONB", "UUID", "VECTOR"]
    parity_errors = []
    
    for table in models_to_verify:
        print(f"    Checking table: {table.name}")
        try:
            ddl = str(CreateTable(table).compile(engine))
            
            # Verify critical production types
            for pg_type in critical_pg_types:
                if pg_type == "JSONB" and "JSONB" not in ddl:
                    # Some tables might intentionally use JSON or strings, but for v1.1 production 
                    # we prefer JSONB for tasks, audit_logs, and payload storage.
                    if table.name in ["tasks", "audit_logs", "programs", "llm_usage_logs"]:
                         print(f"      [WARNING] {table.name} might be missing JSONB optimization.")
                
                if pg_type == "UUID" and "UUID" not in ddl.upper():
                    # SQLite uses strings, but Postgres MUST use UUID types in production v1.1
                    if "ID" in [c.name.upper() for c in table.columns]:
                         # Check if the primary key column is indeed UUID
                         pk_col = list(table.primary_key.columns)[0]
                         if "UUID" not in str(pk_col.type).upper():
                             print(f"      [ERROR] {table.name}.{pk_col.name} is {pk_col.type}, expected UUID for production.")
                             parity_errors.append(f"{table.name}.{pk_col.name} type mismatch")

            # Check pgvector usage if applicable
            if table.name == "form_field_embeddings" and "VECTOR" not in ddl.upper():
                 parity_errors.append("form_field_embeddings missing VECTOR type")

            # Check for Foreign Key enforcement in DDL
            if table.foreign_keys and "REFERENCES" not in ddl.upper():
                 parity_errors.append(f"{table.name} might be missing Foreign Key enforcement in DDL.")

        except Exception as e:
            print(f"      [CRITICAL] Could not generate DDL for {table.name}: {e}")
            parity_errors.append(f"DDL Generation Error: {table.name}")

    print("\n" + "="*50)
    if not parity_errors:
        print("PRODUCTION PARITY: [OK] - Schema is Postgres-Ready (v1.1).")
    else:
        print(f"PRODUCTION PARITY: [FAILED] - {len(parity_errors)} Dialect Conflicts Detected.")
        for err in parity_errors:
            print(f"  - {err}")
    print("="*50)
    
    return len(parity_errors) == 0

if __name__ == "__main__":
    success = verify_pg_schema()
    sys.exit(0 if success else 1)
