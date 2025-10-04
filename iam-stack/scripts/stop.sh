#!/bin/bash

# IAM Stack Shutdown Script
# This script stops all services gracefully

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "================================================"
echo "Stopping IAM Stack"
echo "================================================"
echo ""

# Use docker compose or docker-compose based on availability
if docker compose version &> /dev/null 2>&1; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

cd "$PROJECT_DIR"

echo "🛑 Stopping all services..."
$DOCKER_COMPOSE down

echo ""
echo "================================================"
echo "✅ IAM Stack Stopped Successfully!"
echo "================================================"
echo ""
echo "💾 Data is preserved in Docker volumes"
echo ""
echo "🔄 To restart: ./scripts/start.sh"
echo "🗑️  To remove all data: ./scripts/cleanup.sh"
echo ""
