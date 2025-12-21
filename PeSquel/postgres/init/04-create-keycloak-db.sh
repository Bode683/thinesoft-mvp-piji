#!/bin/bash
# 04-create-keycloak-db.sh
# Create dedicated database for Keycloak authentication service
# Part of QueWall microservice integration

set -e

echo "Creating Keycloak database and user..."

# Check if password is set
if [ -z "$KEYCLOAK_DB_PASSWORD" ]; then
  echo "ERROR: KEYCLOAK_DB_PASSWORD environment variable not set"
  exit 1
fi

# Create keycloak database and user
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
  -- Create keycloak database
  SELECT 'CREATE DATABASE keycloak'
  WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'keycloak')\gexec

  -- Create keycloak user if it doesn't exist
  DO \$\$
  BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'keycloak') THEN
      CREATE USER keycloak WITH PASSWORD '${KEYCLOAK_DB_PASSWORD}';
    ELSE
      ALTER USER keycloak WITH PASSWORD '${KEYCLOAK_DB_PASSWORD}';
    END IF;
  END \$\$;

  -- Grant privileges
  GRANT ALL PRIVILEGES ON DATABASE keycloak TO keycloak;

  -- Log creation
  DO \$\$
  BEGIN
    RAISE NOTICE 'Keycloak database and user created/updated at %', NOW();
  END \$\$;
EOSQL

echo "✓ Keycloak database and user configured successfully"
