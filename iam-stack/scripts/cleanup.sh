#!/bin/bash

# IAM Stack Cleanup Script
# WARNING: This script removes all data including volumes

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "================================================"
echo "⚠️  IAM Stack Cleanup"
echo "================================================"
echo ""
echo "WARNING: This will remove all containers, volumes, and data!"
echo "This action cannot be undone."
echo ""
read -p "Are you sure you want to continue? (yes/no): " -r
echo ""

if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Cleanup cancelled."
    exit 0
fi

# Use docker compose or docker-compose based on availability
if docker compose version &> /dev/null 2>&1; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

cd "$PROJECT_DIR"

echo "🗑️  Stopping and removing containers..."
$DOCKER_COMPOSE down -v

echo ""
echo "🗑️  Removing orphaned volumes..."
docker volume prune -f

echo ""
echo "================================================"
echo "✅ Cleanup Complete!"
echo "================================================"
echo ""
echo "All containers, volumes, and data have been removed."
echo ""
echo "🔄 To start fresh: ./scripts/start.sh"
echo ""
