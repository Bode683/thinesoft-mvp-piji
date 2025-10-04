#!/bin/bash

# IAM Stack Logs Script
# This script displays logs for IAM stack services

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

SERVICE=${1:-all}
FOLLOW=${2:--f}

cd "$PROJECT_DIR"

echo "================================================"
echo "IAM Stack Logs"
echo "================================================"
echo ""

case $SERVICE in
    keycloak)
        echo "📋 Keycloak logs:"
        docker logs $FOLLOW iam-keycloak
        ;;
    postgres)
        echo "📋 PostgreSQL logs:"
        docker logs $FOLLOW iam-postgres
        ;;
    openldap)
        echo "📋 OpenLDAP logs:"
        docker logs $FOLLOW iam-openldap
        ;;
    prometheus)
        echo "📋 Prometheus logs:"
        docker logs $FOLLOW iam-prometheus
        ;;
    grafana)
        echo "📋 Grafana logs:"
        docker logs $FOLLOW iam-grafana
        ;;
    pgadmin)
        echo "📋 pgAdmin logs:"
        docker logs $FOLLOW iam-pgadmin
        ;;
    all)
        # Use docker compose or docker-compose based on availability
        if docker compose version &> /dev/null 2>&1; then
            docker compose logs $FOLLOW
        else
            docker-compose logs $FOLLOW
        fi
        ;;
    *)
        echo "Usage: $0 [service] [options]"
        echo ""
        echo "Services:"
        echo "  keycloak    - Keycloak IAM server"
        echo "  postgres    - PostgreSQL database"
        echo "  openldap    - OpenLDAP directory"
        echo "  prometheus  - Prometheus metrics"
        echo "  grafana     - Grafana dashboards"
        echo "  pgadmin     - pgAdmin database tool"
        echo "  all         - All services (default)"
        echo ""
        echo "Options:"
        echo "  -f          - Follow log output (default)"
        echo "  --tail=N    - Show last N lines"
        echo ""
        echo "Examples:"
        echo "  $0 keycloak"
        echo "  $0 postgres --tail=100"
        echo "  $0 all"
        ;;
esac
