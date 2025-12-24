#!/bin/sh
set -e

echo "OAuth2-Proxy custom entrypoint starting..."

# Read client secret from Docker secret file using --client-secret-file flag
echo "✓ Client secret will be loaded from /run/secrets/oauth2_client_secret"

# Read cookie secret from file using --cookie-secret-file flag
echo "✓ Cookie secret will be loaded from /run/secrets/oauth2_cookie_secret"

echo "Starting OAuth2-Proxy..."

# Execute oauth2-proxy with both secret files as command-line flags
exec /bin/oauth2-proxy \
  --client-secret-file=/run/secrets/oauth2_client_secret \
  --cookie-secret-file=/run/secrets/oauth2_cookie_secret \
  "$@"
