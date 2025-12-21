#!/bin/bash
# 05-create-djangocms-db.sh
# Create dedicated database for Django CMS application
# Part of Django CMS microservice integration

set -e

echo "Creating Django CMS database and user..."

# Check if password is set
if [ -z "$DJANGOCMS_DB_PASSWORD" ]; then
  echo "ERROR: DJANGOCMS_DB_PASSWORD environment variable not set"
  exit 1
fi

# Create django_db database and djangocms user
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
  -- Create django_db database
  SELECT 'CREATE DATABASE django_db'
  WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'django_db')\gexec

  -- Create djangocms user if it doesn't exist
  DO \$\$
  BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'djangocms') THEN
      CREATE USER djangocms WITH PASSWORD '${DJANGOCMS_DB_PASSWORD}';
    ELSE
      ALTER USER djangocms WITH PASSWORD '${DJANGOCMS_DB_PASSWORD}';
    END IF;
  END \$\$;

  -- Grant privileges
  GRANT ALL PRIVILEGES ON DATABASE django_db TO djangocms;

  -- Log creation
  DO \$\$
  BEGIN
    RAISE NOTICE 'Django CMS database and user created/updated at %', NOW();
  END \$\$;
EOSQL

echo "✓ Django CMS database and user configured successfully"
