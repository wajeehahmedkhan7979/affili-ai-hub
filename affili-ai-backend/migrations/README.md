# Database Migrations

## Applying Migrations to Supabase

1. **Via Supabase Dashboard:**
   - Go to SQL Editor in Supabase console
   - Copy contents of `001_create_tables.sql`
   - Execute in the SQL editor

2. **Via psql (local PostgreSQL):**
   ```bash
   psql -h localhost -U postgres -d affili_ai_db -f migrations/001_create_tables.sql
   ```

3. **For pgvector support (optional):**
   If using Supabase with pgvector extension, uncomment these lines in the migration:
   ```sql
   CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
   CREATE EXTENSION IF NOT EXISTS "pgvector";
   ```
   Then replace `FLOAT8[]` with `vector(1536)` for the embedding column.

## Adding New Migrations

Create new files following the pattern: `002_your_migration_name.sql`

Keep migrations small, idempotent, and reversible where possible.
