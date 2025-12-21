#!/bin/bash
set -e

# PostgreSQL Custom Entrypoint Script
# Reads authenticator password from Docker secret and exports it for SQL init scripts

echo "PostgreSQL custom entrypoint starting..."

# Read authenticator password from secret and export for init scripts
if [ -f /run/secrets/authenticator_password ]; then
  export AUTHENTICATOR_PASSWORD=$(cat /run/secrets/authenticator_password)
  echo "✓ Authenticator password loaded from secret"
else
  echo "⚠ Warning: authenticator_password secret not found"
fi

# Read keycloak password from secret and export for init scripts
if [ -f /run/secrets/keycloak_db_password ]; then
  export KEYCLOAK_DB_PASSWORD=$(cat /run/secrets/keycloak_db_password)
  echo "✓ Keycloak DB password loaded from secret"
else
  echo "⚠ Warning: keycloak_db_password secret not found"
fi

# Read Django CMS password from secret and export for init scripts
if [ -f /run/secrets/djangocms_db_password ]; then
  export DJANGOCMS_DB_PASSWORD=$(cat /run/secrets/djangocms_db_password)
  echo "✓ Django CMS DB password loaded from secret"
else
  echo "⚠ Warning: djangocms_db_password secret not found"
fi

# Call original PostgreSQL entrypoint
echo "Starting PostgreSQL..."
exec docker-entrypoint.sh "$@"
