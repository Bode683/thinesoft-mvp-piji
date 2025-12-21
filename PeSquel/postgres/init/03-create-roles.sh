#!/bin/bash
# 03-create-roles.sh
# Create database roles for PostgREST
# Defines roles and permissions for the API

set -e

echo "Creating database roles for PostgREST..."

# Check if password is set
if [ -z "$AUTHENTICATOR_PASSWORD" ]; then
  echo "ERROR: AUTHENTICATOR_PASSWORD environment variable not set"
  exit 1
fi

# Create roles
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
  -- Create anonymous role (for unauthenticated requests)
  DO \$\$
  BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'api_anon') THEN
      CREATE ROLE api_anon NOLOGIN;
    END IF;
  END \$\$;

  -- Create authenticator role (for pgBouncer connection)
  DO \$\$
  BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'authenticator') THEN
      CREATE ROLE authenticator NOINHERIT LOGIN PASSWORD '${AUTHENTICATOR_PASSWORD}';
    ELSE
      ALTER ROLE authenticator WITH PASSWORD '${AUTHENTICATOR_PASSWORD}';
    END IF;
  END \$\$;

  -- Grant necessary permissions
  GRANT api_anon TO authenticator;
  GRANT USAGE ON SCHEMA api TO api_anon;
  GRANT ALL ON ALL TABLES IN SCHEMA api TO api_anon;
  GRANT ALL ON ALL SEQUENCES IN SCHEMA api TO api_anon;
  GRANT ALL ON ALL FUNCTIONS IN SCHEMA api TO api_anon;

  -- Set default privileges for future objects
  ALTER DEFAULT PRIVILEGES IN SCHEMA api
    GRANT ALL ON TABLES TO api_anon;

  ALTER DEFAULT PRIVILEGES IN SCHEMA api
    GRANT ALL ON SEQUENCES TO api_anon;

  ALTER DEFAULT PRIVILEGES IN SCHEMA api
    GRANT ALL ON FUNCTIONS TO api_anon;

  -- Log role creation
  DO \$\$
  BEGIN
    RAISE NOTICE 'Database roles created successfully at %', NOW();
  END \$\$;
EOSQL

echo "✓ Database roles configured successfully"
