#!/bin/bash

# IAM Stack Startup Script
# This script starts all services in the correct order

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "================================================"
echo "Starting IAM Stack"
echo "================================================"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running"
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null 2>&1; then
    echo "❌ Error: docker-compose is not installed"
    exit 1
fi

# Use docker compose or docker-compose based on availability
if docker compose version &> /dev/null 2>&1; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

cd "$PROJECT_DIR"

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found"
    echo "Please create .env file from .env.template"
    exit 1
fi

echo "📦 Starting services..."
echo ""

# Start PostgreSQL first
echo "1️⃣  Starting PostgreSQL..."
$DOCKER_COMPOSE up -d postgres
echo "   Waiting for PostgreSQL to be ready..."
sleep 10

# Check PostgreSQL health
until docker exec iam-postgres pg_isready -U keycloak -d keycloak > /dev/null 2>&1; do
    echo "   Waiting for PostgreSQL..."
    sleep 2
done
echo "   ✅ PostgreSQL is ready"
echo ""

# Start Keycloak
echo "2️⃣  Starting Keycloak..."
$DOCKER_COMPOSE up -d keycloak
echo "   Waiting for Keycloak to be ready (this may take a minute)..."
sleep 15

# Check Keycloak health
RETRY_COUNT=0
MAX_RETRIES=30
until curl -sf http://localhost:8080/health/ready > /dev/null 2>&1; do
    RETRY_COUNT=$((RETRY_COUNT+1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "   ❌ Keycloak failed to start within expected time"
        echo "   Check logs: docker logs iam-keycloak"
        echo "   Last few log lines:"
        docker logs iam-keycloak --tail 10
        exit 1
    fi
    echo "   Waiting for Keycloak... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 5
done
echo "   ✅ Keycloak is ready"
echo ""

# Start Observability Stack
echo "3️⃣  Starting Observability Stack..."
$DOCKER_COMPOSE up -d prometheus grafana node-exporter postgres-exporter
echo "   ✅ Observability stack started"
echo ""

# Start pgAdmin
echo "4️⃣  Starting pgAdmin..."
$DOCKER_COMPOSE up -d pgadmin
echo "   ✅ pgAdmin started"
echo ""

# Start OpenLDAP (Optional)
echo "5️⃣  Starting OpenLDAP..."
$DOCKER_COMPOSE up -d openldap phpldapadmin
echo "   ✅ OpenLDAP started"
echo ""

# Start Nginx Reverse Proxy
echo "6️⃣  Starting Nginx..."
$DOCKER_COMPOSE up -d nginx
sleep 5
echo "   ✅ Nginx started"
echo ""

# Display status
echo "================================================"
echo "✅ IAM Stack Started Successfully!"
echo "================================================"
echo ""
echo "📊 Service Status:"
$DOCKER_COMPOSE ps
echo ""
echo "================================================"
echo "🌐 Access Points:"
echo "================================================"
echo ""
echo "Keycloak Admin Console:"
echo "  URL: http://localhost:8080 (Direct)"
echo "  URL: http://auth.theddt.local:8880 (via Nginx)"
echo "  Username: admin"
echo "  Password: (check .env file)"
echo ""
echo "Keycloak Realm:"
echo "  Realm: theddt-realm"
echo "  URL: http://localhost:8080/realms/theddt-realm"
echo ""
echo "pgAdmin:"
echo "  URL: http://localhost:8883"
echo "  Email: (check .env file)"
echo ""
echo "phpLDAPadmin:"
echo "  URL: http://localhost:8884"
echo "  Login DN: cn=admin,dc=theddt,dc=local"
echo "  Password: admin123"
echo ""
echo "Grafana:"
echo "  URL: http://localhost:8881"
echo "  Username: admin"
echo "  Password: admin"
echo ""
echo "Prometheus:"
echo "  URL: http://localhost:8882"
echo ""
echo "================================================"
echo "📝 Next Steps:"
echo "================================================"
echo ""
echo "1. Access Keycloak Admin Console"
echo "2. Verify theddt-realm is imported"
echo "3. Configure LDAP federation (see docs/IMPLEMENTATION_PLAN.md)"
echo "4. Test API endpoints using Postman collections"
echo ""
echo "📚 Documentation:"
echo "  - Implementation Plan: docs/IMPLEMENTATION_PLAN.md"
echo "  - API Documentation: docs/API_DOCUMENTATION.md"
echo "  - Postman Collections: postman/"
echo ""
echo "🔍 View logs:"
echo "  docker logs iam-keycloak -f"
echo "  docker logs iam-postgres -f"
echo "  docker logs iam-openldap -f"
echo ""
echo "🛑 Stop services:"
echo "  ./scripts/stop.sh"
echo ""
