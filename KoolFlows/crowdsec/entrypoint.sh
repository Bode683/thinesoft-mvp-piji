#!/bin/bash


# CrowdSec Initialization Script
# Initializes CrowdSec engine with collections and registers pre-generated bouncer key
# Configured for LOCAL-ONLY operation due to network firewall restrictions

# Disable cloud API calls due to ISP firewall blocking api.crowdsec.net
echo "Disabling CrowdSec Cloud API (local-only mode)..."
if [ -f /etc/crowdsec/config.yaml ]; then
  # Comment out the online_client section in config to disable cloud API
  sed -i 's/^    online_client:/#    online_client:/' /etc/crowdsec/config.yaml
  sed -i 's/^      credentials_path/#      credentials_path/' /etc/crowdsec/config.yaml
  echo "✓ Cloud API disabled in config for local-only operation"
fi

# Remove CAPI credentials to prevent registration attempts
rm -f /etc/crowdsec/online_api_credentials.yaml 2>/dev/null || true
echo "✓ Removed cloud API credentials file"

# Start CrowdSec in background to allow cscli commands
echo "Starting CrowdSec in background..."
/docker_start.sh &
CROWDSEC_PID=$!

# Wait for CrowdSec API to be ready
echo "Waiting for CrowdSec API to be ready..."
for i in {1..30}; do
  if cscli version >/dev/null 2>&1; then
    echo "✓ CrowdSec API is ready"
    break
  fi
  echo "Waiting... ($i/30)"
  sleep 2
done

# Check if this is the first run
if [ ! -f /etc/crowdsec/.first-run ]; then
  echo "First run - initializing CrowdSec..."

  # Install base collections (skip if network access is restricted)
  echo "Installing CrowdSec base collections..."
  if cscli hub update 2>/dev/null; then
    cscli collections install crowdsecurity/traefik || echo "⚠ Failed to install traefik collection (network issue?)"
    cscli collections install crowdsecurity/http-cve || echo "⚠ Failed to install http-cve collection (network issue?)"

    # Install AppSec collections for WAF functionality
    echo "Installing AppSec collections..."
    cscli collections install crowdsecurity/appsec-generic-rules || echo "⚠ Failed to install appsec-generic-rules"
    cscli collections install crowdsecurity/appsec-virtual-patching || echo "⚠ Failed to install appsec-virtual-patching"
    cscli collections install crowdsecurity/appsec-crs || echo "⚠ Failed to install appsec-crs"
    cscli collections install crowdsecurity/http-dos || echo "⚠ Failed to install http-dos"
  else
    echo "⚠ CrowdSec hub not accessible - skipping collection installation"
    echo "⚠ Collections must be pre-installed in the image or network access configured"
  fi
  echo "✓ Collection installation attempted"

  # Register bouncer with pre-generated key from secret
  if [ -f /run/secrets/crowdsec_bouncer_key ]; then
    BOUNCER_KEY=$(cat /run/secrets/crowdsec_bouncer_key)
    echo "Registering Traefik plugin bouncer..."

    # Add bouncer (this creates a random key)
    cscli bouncers add traefik-plugin || true

    # Update bouncer key in database to use our pre-generated key
    sqlite3 /var/lib/crowdsec/data/crowdsec.db \
      "UPDATE bouncers SET api_key='${BOUNCER_KEY}' WHERE name='traefik-plugin';" || true

    echo "✓ Bouncer registered with pre-generated API key"
  else
    echo "⚠ Bouncer key secret not found at /run/secrets/crowdsec_bouncer_key"
    echo "⚠ Generating new bouncer key as fallback..."
    cscli bouncers add traefik-plugin || true
  fi

  # Mark first run as complete
  touch /etc/crowdsec/.first-run
  echo "✓ CrowdSec initialization complete"
else
  echo "CrowdSec already initialized"
fi

# Stop the background CrowdSec process and restart in foreground
echo "Stopping background CrowdSec process..."
kill $CROWDSEC_PID 2>/dev/null || true
wait $CROWDSEC_PID 2>/dev/null || true

# Replace this shell with the CrowdSec process (foreground)
echo "Starting CrowdSec in foreground..."
exec /docker_start.sh
