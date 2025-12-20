#!/bin/bash
set -e

echo "Keycloak custom entrypoint: Reading Docker secrets..."

# Read keycloak DB password from secret
if [ -f /run/secrets/keycloak_db_password ]; then
  export KC_DB_PASSWORD=$(cat /run/secrets/keycloak_db_password)
  echo "✓ Keycloak DB password loaded from secret"
else
  echo "⚠ Warning: keycloak_db_password secret not found"
fi

# Read keycloak admin password from secret
if [ -f /run/secrets/keycloak_admin_password ]; then
  export KEYCLOAK_ADMIN_PASSWORD=$(cat /run/secrets/keycloak_admin_password)
  echo "✓ Keycloak admin password loaded from secret"
else
  echo "⚠ Warning: keycloak_admin_password secret not found"
fi

# Call original Keycloak entrypoint
echo "Starting Keycloak with kc.sh..."
exec /opt/keycloak/bin/kc.sh "$@"
