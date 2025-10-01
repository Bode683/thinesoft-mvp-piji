#!/bin/bash

set -e

echo "🛑 Tearing down PostgreSQL + pgAudit and Grafana Stacks"
echo "======================================================="

# Stop DB stack
stop_db_stack() {
    echo "🔄 Stopping DB stack..."
    if [ -d "db-stack" ]; then
        cd db-stack
        docker compose down -v
        cd ..
        echo "✅ DB stack stopped"
    else
        echo "⚠️ db-stack directory not found"
    fi
}

# Stop Grafana stack
stop_grafana_stack() {
    echo "🔄 Stopping Grafana stack..."
    if [ -d "grafana-stack" ]; then
        cd grafana-stack
        docker compose down -v
        cd ..
        echo "✅ Grafana stack stopped"
    else
        echo "⚠️ grafana-stack directory not found"
    fi
}

# Clean up Docker resources
cleanup_docker() {
    echo "🧹 Cleaning up Docker resources..."
    
    # Remove dangling volumes
    echo "🔄 Removing unused volumes..."
    docker volume prune -f
    
    # Remove custom images
    echo "🔄 Removing custom PostgreSQL image..."
    docker rmi db-stack_postgres 2>/dev/null || echo "⚠️ Custom PostgreSQL image not found"
    
    echo "✅ Docker cleanup complete"
}

# Option to remove /etc/hosts entries
cleanup_hosts() {
    if [ "$1" = "--remove-hosts" ]; then
        echo "🔄 Removing /etc/hosts entries..."
        echo "You'll need to manually remove these entries from /etc/hosts:"
        echo "   127.0.0.1 pgadmin.theddt.local"
        echo "   127.0.0.1 pgaudit.theddt.local"
        echo "   127.0.0.1 grafanastack.theddt.local"
        echo ""
        echo "Or run this command:"
        echo "   sudo sed -i '/theddt\\.local/d' /etc/hosts"
    fi
}

main() {
    stop_db_stack
    stop_grafana_stack
    cleanup_docker
    cleanup_hosts "$1"
    
    echo ""
    echo "🎉 Teardown complete!"
    echo "===================="
    echo "All containers and volumes have been removed."
    echo ""
    echo "💡 To also remove /etc/hosts entries, run:"
    echo "   ./teardown.sh --remove-hosts"
}

main "$@"
