#!/bin/bash
set -e

# Wait for Postgres to be ready
if [ -n "$DATABASE_URL" ]; then
  # Extract host from DATABASE_URL
  # format: postgresql://user:pass@host:port/dbname
  DB_HOST=$(echo $DATABASE_URL | sed -e 's|.*@||' -e 's|:.*||' -e 's|/.*||')
  echo "Waiting for postgres at $DB_HOST..."
  until pg_isready -h "$DB_HOST" -U "${POSTGRES_USER:-postgres}"; do
    echo "Postgres is unavailable - sleeping"
    sleep 2
  done
  echo "Postgres is up - executing migrations"
  
  # Run migrations
  alembic upgrade head
fi

# Execute CMD
exec "$@"
