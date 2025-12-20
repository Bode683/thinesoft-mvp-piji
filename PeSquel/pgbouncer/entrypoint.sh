#!/bin/bash
set -e

# pgBouncer Custom Entrypoint Script
# Dynamically generates userlist.txt with MD5 hash of authenticator password

echo "pgBouncer custom entrypoint starting..."

# Wait for authenticator password secret
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
  if [ -f /run/secrets/authenticator_password ]; then
    echo "✓ Authenticator password secret found"
    break
  fi

  attempt=$((attempt + 1))
  echo "Waiting for authenticator password secret... (attempt $attempt/$max_attempts)"
  sleep 1
done

if [ ! -f /run/secrets/authenticator_password ]; then
  echo "✗ Authenticator password secret not found after $max_attempts attempts"
  exit 1
fi

AUTHENTICATOR_PASSWORD=$(cat /run/secrets/authenticator_password)

if [ -z "$AUTHENTICATOR_PASSWORD" ]; then
  echo "✗ Authenticator password is empty"
  exit 1
fi

echo "Generating pgBouncer userlist.txt with dynamic password hash..."

# Generate MD5 hash for pgBouncer
# Format: md5 + md5(password + username)
# The authenticator role name is "authenticator"
MD5_HASH=$(echo -n "${AUTHENTICATOR_PASSWORD}authenticator" | md5sum | cut -d' ' -f1)

# Generate userlist.txt (Bitnami path)
echo "\"authenticator\" \"md5${MD5_HASH}\"" > /opt/bitnami/pgbouncer/conf/userlist.txt

# Verify file was created
if [ -f /opt/bitnami/pgbouncer/conf/userlist.txt ]; then
  echo "✓ pgBouncer userlist.txt generated successfully"
  # Show first 50 chars of hash for verification (not the full password)
  echo "  Hash: md5${MD5_HASH:0:20}..."
else
  echo "✗ Failed to create userlist.txt"
  exit 1
fi

echo "Starting pgBouncer..."

# Start pgBouncer (Bitnami path)
exec pgbouncer /opt/bitnami/pgbouncer/conf/pgbouncer.ini
