#!/bin/sh
set -e

BOUNCER_KEY_FILE="/var/lib/crowdsec/bouncer-key.txt"
CONFIG_FILE="/etc/traefik/crowdsec-bouncer.yaml"

echo "Waiting for CrowdSec bouncer API key..."

for i in $(seq 1 60); do
  if [ -s "$BOUNCER_KEY_FILE" ]; then
    echo "✓ Bouncer API key found"
    break
  fi
  echo "Waiting... ($i/60)"
  sleep 1
done

if [ ! -s "$BOUNCER_KEY_FILE" ]; then
  echo "✗ Bouncer API key not found"
  exit 1
fi

API_KEY=$(cat "$BOUNCER_KEY_FILE")

if [ -z "$API_KEY" ]; then
  echo "✗ Bouncer API key is empty"
  exit 1
fi

echo "✓ Injecting API key into config"

# Replace api_key value in config
sed -i "s|api_key:.*|api_key: \"$API_KEY\"|g" "$CONFIG_FILE"

echo "✓ Starting Traefik CrowdSec bouncer"
exec /traefik-crowdsec-bouncer
