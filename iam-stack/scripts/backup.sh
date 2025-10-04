#!/bin/bash

# IAM Stack Backup Script
# This script backs up PostgreSQL database and Keycloak configuration

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="$PROJECT_DIR/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "================================================"
echo "IAM Stack Backup"
echo "================================================"
echo ""

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Check if PostgreSQL container is running
if ! docker ps | grep -q iam-postgres; then
    echo "❌ Error: PostgreSQL container is not running"
    exit 1
fi

echo "📦 Creating backup..."
echo ""

# Backup PostgreSQL database
echo "1️⃣  Backing up PostgreSQL database..."
docker exec iam-postgres pg_dump -U keycloak keycloak > "$BACKUP_DIR/keycloak_db_$TIMESTAMP.sql"
echo "   ✅ Database backup saved: backups/keycloak_db_$TIMESTAMP.sql"
echo ""

# Backup Keycloak realm configuration
echo "2️⃣  Backing up Keycloak realm configuration..."
cp -r "$PROJECT_DIR/config/keycloak/realms" "$BACKUP_DIR/realms_$TIMESTAMP"
echo "   ✅ Realm config backup saved: backups/realms_$TIMESTAMP/"
echo ""

# Backup OpenLDAP data (if needed)
echo "3️⃣  Backing up OpenLDAP configuration..."
cp -r "$PROJECT_DIR/config/openldap/ldif" "$BACKUP_DIR/ldap_$TIMESTAMP"
echo "   ✅ LDAP config backup saved: backups/ldap_$TIMESTAMP/"
echo ""

# Create compressed archive
echo "4️⃣  Creating compressed archive..."
cd "$BACKUP_DIR"
tar -czf "iam_backup_$TIMESTAMP.tar.gz" \
    "keycloak_db_$TIMESTAMP.sql" \
    "realms_$TIMESTAMP" \
    "ldap_$TIMESTAMP"

# Remove individual backup files
rm -rf "keycloak_db_$TIMESTAMP.sql" "realms_$TIMESTAMP" "ldap_$TIMESTAMP"

echo "   ✅ Compressed backup: backups/iam_backup_$TIMESTAMP.tar.gz"
echo ""

# Calculate backup size
BACKUP_SIZE=$(du -h "iam_backup_$TIMESTAMP.tar.gz" | cut -f1)

echo "================================================"
echo "✅ Backup Complete!"
echo "================================================"
echo ""
echo "Backup file: iam_backup_$TIMESTAMP.tar.gz"
echo "Size: $BACKUP_SIZE"
echo "Location: $BACKUP_DIR"
echo ""
echo "🔄 To restore: ./scripts/restore.sh iam_backup_$TIMESTAMP.tar.gz"
echo ""
