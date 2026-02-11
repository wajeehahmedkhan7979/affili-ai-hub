-- AFFILI-AI HUB - Database Schema Bootstrap
-- Run this via Supabase SQL Editor if tables don't exist yet
-- This creates all required tables and extensions

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Note: If you get "permission denied" on extension creation,
-- this is expected with pgbouncer. Run this command via Supabase SQL Editor instead.

-- The Alembic migrations will create all tables when run via direct connection (port 5432)
-- For now, we're testing with existing schema via pooler (port 6543)

SELECT 'Database bootstrap SQL ready - run via Supabase if needed' as status;
