from sqlalchemy import create_engine
from app.db.base import Base
import app.models # register all models
from app.core.config import settings

def test_compile():
    url = settings.DATABASE_URL
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    
    print(f"Testing compilation with URL: {url}")
    engine = create_engine(url)
    try:
        # This will trigger compilation of the schema
        # We don't even need to execute it, just ask for the SQL
        # for a create table statement.
        from sqlalchemy.schema import CreateTable
        from sqlalchemy.dialects import postgresql, sqlite
        
        for table in Base.metadata.sorted_tables:
            print(f"Compiling table for Postgres: {table.name}")
            CreateTable(table).compile(dialect=postgresql.dialect())
            
            print(f"Compiling table for SQLite: {table.name}")
            try:
                CreateTable(table).compile(dialect=sqlite.dialect())
            except Exception as e:
                print(f"  FAILED for SQLite: {e}")
            
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_compile()
