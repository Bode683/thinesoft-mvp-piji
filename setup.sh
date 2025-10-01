#!/bin/bash

set -e

echo "🚀 Setting up PostgreSQL + pgAudit and Grafana Stacks"
echo "======================================================"

# Check if .env files exist
check_env_files() {
    echo "📋 Checking environment files..."
    
    if [ ! -f "db-stack/.env" ]; then
        echo "❌ db-stack/.env not found. Please copy and configure:"
        echo "   cp db-stack/.env.template db-stack/.env"
        echo "   Edit db-stack/.env with your passwords"
        exit 1
    fi
    
    if [ ! -f "grafana-stack/.env" ]; then
        echo "❌ grafana-stack/.env not found. Please copy and configure:"
        echo "   cp grafana-stack/.env.template grafana-stack/.env"
        echo "   Edit grafana-stack/.env with your passwords"
        exit 1
    fi
    
    echo "✅ Environment files found"
}

# Check if hosts entries are added
check_hosts() {
    echo "📋 Checking /etc/hosts entries..."
    
    for hostname in "pgadmin.theddt.local" "pgaudit.theddt.local" "grafanastack.theddt.local"; do
        if ! grep -q "$hostname" /etc/hosts; then
            echo "❌ /etc/hosts entries missing ($hostname not found). Please run:"
            echo "   sudo bash -c 'cat hosts-entries.txt >> /etc/hosts'"
            exit 1
        fi
    done
    
    echo "✅ Hosts entries found"
}

# Start Grafana stack first
start_grafana_stack() {
    echo "🔄 Starting Grafana stack..."
    cd grafana-stack
    docker compose up -d
    cd ..
    
    echo "⏳ Waiting for Grafana to be accessible..."
    for i in {1..30}; do
        if curl -sSf http://grafanastack.theddt.local:3000 > /dev/null 2>&1; then
            echo "✅ Grafana is accessible"
            break
        fi
        echo "⏳ Waiting for Grafana... ($i/30)"
        sleep 5
    done

    # Wait for Loki to be ready
    echo "🔍 Checking Loki health..."
    for i in {1..30}; do
        if curl -s http://grafanastack.theddt.local:3100/ready > /dev/null 2>&1; then
            echo "✅ Loki is ready"
            break
        fi
        echo "⏳ Waiting for Loki... ($i/30)"
        sleep 5
    done

    # Wait for Prometheus to be healthy
    echo "🔍 Checking Prometheus health..."
    for i in {1..30}; do
        if curl -sSf http://grafanastack.theddt.local:9090/-/healthy > /dev/null 2>&1; then
            echo "✅ Prometheus is healthy"
            break
        fi
        echo "⏳ Waiting for Prometheus... ($i/30)"
        sleep 5
    done

    # Wait for Alertmanager to be healthy
    echo "🔍 Checking Alertmanager health..."
    for i in {1..30}; do
        if curl -sSf http://grafanastack.theddt.local:9093/-/healthy > /dev/null 2>&1; then
            echo "✅ Alertmanager is healthy"
            break
        fi
        echo "⏳ Waiting for Alertmanager... ($i/30)"
        sleep 5
    done
}

# Start DB stack
start_db_stack() {
    echo "🔄 Starting DB stack..."
    cd db-stack
    docker compose up -d
    cd ..
}

# Verify everything is working
verify_setup() {
    echo "🔍 Verifying setup..."
    
    # Check Grafana
    if curl -s http://grafanastack.theddt.local:3000 > /dev/null; then
        echo "✅ Grafana accessible at http://grafanastack.theddt.local:3000"
    else
        echo "❌ Grafana not accessible"
    fi
    
    # Check pgAdmin
    if curl -s http://pgadmin.theddt.local > /dev/null; then
        echo "✅ pgAdmin accessible at http://pgadmin.theddt.local"
    else
        echo "❌ pgAdmin not accessible"
    fi
    
    # Check pgAudit dashboard
    if curl -s http://pgaudit.theddt.local > /dev/null; then
        echo "✅ pgAudit dashboard accessible at http://pgaudit.theddt.local"
    else
        echo "❌ pgAudit dashboard not accessible"
    fi
    
    # Check Loki
    if curl -s http://grafanastack.theddt.local:3100/ready > /dev/null; then
        echo "✅ Loki ready at http://grafanastack.theddt.local:3100"
    else
        echo "❌ Loki not ready"
    fi
    
    # Check Prometheus
    if curl -s http://grafanastack.theddt.local:9090 > /dev/null; then
        echo "✅ Prometheus accessible at http://grafanastack.theddt.local:9090"
    else
        echo "❌ Prometheus not accessible"
    fi
    
    # Check PgBouncer
    echo "📊 PgBouncer should be accessible on localhost:6432"
}

main() {
    check_env_files
    check_hosts
    start_grafana_stack
    start_db_stack
    verify_setup
    
    echo ""
    echo "🎉 Setup complete!"
    echo "================================"
    echo "📊 Services accessible at:"
    echo "   • Grafana: http://grafanastack.theddt.local:3000"
    echo "   • pgAdmin: http://pgadmin.theddt.local"
    echo "   • pgAudit Dashboard: http://pgaudit.theddt.local"
    echo "   • Prometheus: http://grafanastack.theddt.local:9090"
    echo "   • Alertmanager: http://grafanastack.theddt.local:9093"
    echo "   • PgBouncer: localhost:6432"
    echo ""
    echo "🔍 To run K6 tests:"
    echo "   cd grafana-stack && docker compose run --rm k6 run /scripts/example-test.js"
    echo ""
    echo "📝 Check container logs:"
    echo "   docker compose logs -f postgres  # In db-stack/"
    echo "   docker compose logs -f promtail  # In db-stack/"
}

main "$@"
