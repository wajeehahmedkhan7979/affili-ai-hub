-- Enable pgvector extension for PostgreSQL/Supabase
-- This script should be run manually on the production database
-- or via Supabase SQL Editor before running Alembic migrations

-- Enable the vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify installation
SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';

-- Expected output: vector | 0.5.0 (or higher)
