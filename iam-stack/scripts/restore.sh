#!/bin/bash

# IAM Stack Restore Script
# This script restores PostgreSQL database and Keycloak configuration from backup

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="$PROJECT_DIR/backups"

if [ -z "$1" ]; then
    echo "Usage: $0 <backup-file.tar.gz>"
    echo ""
    echo "Available backups:"
    ls -lh "$BACKUP_DIR"/*.tar.gz 2>/dev/null || echo "No backups found"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_DIR/$BACKUP_FILE" ]; then
    echo "❌ Error: Backup file not found: $BACKUP_DIR/$BACKUP_FILE"
    exit 1
fi

echo "================================================"
echo "⚠️  IAM Stack Restore"
echo "================================================"
echo ""
echo "WARNING: This will overwrite existing data!"
echo "Backup file: $BACKUP_FILE"
echo ""
read -p "Are you sure you want to continue? (yes/no): " -r
echo ""

if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Restore cancelled."
    exit 0
fi

# Check if PostgreSQL container is running
if ! docker ps | grep -q iam-postgres; then
    echo "❌ Error: PostgreSQL container is not running"
    echo "Start the stack first: ./scripts/start.sh"
    exit 1
fi

echo "📦 Restoring from backup..."
echo ""

# Extract backup
echo "1️⃣  Extracting backup archive..."
cd "$BACKUP_DIR"
tar -xzf "$BACKUP_FILE"
echo "   ✅ Backup extracted"
echo ""

# Find extracted files
DB_BACKUP=$(ls keycloak_db_*.sql 2>/dev/null | head -1)
REALM_BACKUP=$(ls -d realms_* 2>/dev/null | head -1)
LDAP_BACKUP=$(ls -d ldap_* 2>/dev/null | head -1)

# Restore PostgreSQL database
if [ -n "$DB_BACKUP" ]; then
    echo "2️⃣  Restoring PostgreSQL database..."
    docker exec -i iam-postgres psql -U keycloak -d keycloak < "$DB_BACKUP"
    echo "   ✅ Database restored"
    rm "$DB_BACKUP"
else
    echo "⚠️  No database backup found in archive"
fi
echo ""

# Restore Keycloak realm configuration
if [ -n "$REALM_BACKUP" ]; then
    echo "3️⃣  Restoring Keycloak realm configuration..."
    rm -rf "$PROJECT_DIR/config/keycloak/realms"
    mv "$REALM_BACKUP" "$PROJECT_DIR/config/keycloak/realms"
    echo "   ✅ Realm configuration restored"
else
    echo "⚠️  No realm backup found in archive"
fi
echo ""

# Restore OpenLDAP configuration
if [ -n "$LDAP_BACKUP" ]; then
    echo "4️⃣  Restoring OpenLDAP configuration..."
    rm -rf "$PROJECT_DIR/config/openldap/ldif"
    mv "$LDAP_BACKUP" "$PROJECT_DIR/config/openldap/ldif"
    echo "   ✅ LDAP configuration restored"
else
    echo "⚠️  No LDAP backup found in archive"
fi
echo ""

echo "5️⃣  Restarting services..."
cd "$PROJECT_DIR"

# Use docker compose or docker-compose based on availability
if docker compose version &> /dev/null 2>&1; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

$DOCKER_COMPOSE restart keycloak
echo "   ✅ Services restarted"
echo ""

echo "================================================"
echo "✅ Restore Complete!"
echo "================================================"
echo ""
echo "The IAM stack has been restored from backup."
echo "Please verify that all data is correct."
echo ""
