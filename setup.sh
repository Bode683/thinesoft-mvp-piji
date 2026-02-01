#!/bin/bash

# ITLDS MVP Setup Script
# Initializes all microservices with centralized orchestration

set -e

echo "=========================================="
echo "ITLDS MVP Setup - Multi-Microservice Architecture"
echo "=========================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }

# Check prerequisites
check_prerequisites() {
    echo "Checking prerequisites..."

    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker."
        exit 1
    fi
    print_success "Docker is running"

    if ! docker compose version > /dev/null 2>&1; then
        print_error "Docker Compose is not available."
        exit 1
    fi
    print_success "Docker Compose is available"
}

# Create directory structure
create_directories() {
    echo "Creating directory structure..."

    # Centralized secrets
    mkdir -p secrets

    # KoolFlows directories
    mkdir -p KoolFlows/traefik/dynamic
    mkdir -p KoolFlows/crowdsec/config
    mkdir -p KoolFlows/crowdsec/data
    mkdir -p KoolFlows/bouncer

    # PeSquel directories
    mkdir -p PeSquel/postgres/init
    mkdir -p PeSquel/postgres/data
    mkdir -p PeSquel/pgbouncer
    mkdir -p PeSquel/pgadmin/data

    # QueWall directories
    mkdir -p QueWall/keycloak

    print_success "Directories created"
}

# Generate secrets
generate_secrets() {
    echo "Generating secrets..."

    # PostgreSQL secrets
    if [ ! -f secrets/postgres_user.txt ]; then
        echo "pesequel_user" > secrets/postgres_user.txt
        print_success "Generated postgres_user.txt"
    else
        print_warning "postgres_user.txt already exists, skipping"
    fi

    if [ ! -f secrets/postgres_password.txt ]; then
        openssl rand -base64 32 > secrets/postgres_password.txt
        print_success "Generated postgres_password.txt"
    else
        print_warning "postgres_password.txt already exists, skipping"
    fi

    if [ ! -f secrets/postgres_db.txt ]; then
        echo "pesequel_db" > secrets/postgres_db.txt
        print_success "Generated postgres_db.txt"
    else
        print_warning "postgres_db.txt already exists, skipping"
    fi

    # pgAdmin secrets
    if [ ! -f secrets/pgadmin_email.txt ]; then
        echo "admin@theddt.com" > secrets/pgadmin_email.txt
        print_success "Generated pgadmin_email.txt"
    else
        print_warning "pgadmin_email.txt already exists, skipping"
    fi

    if [ ! -f secrets/pgadmin_password.txt ]; then
        openssl rand -base64 32 > secrets/pgadmin_password.txt
        print_success "Generated pgadmin_password.txt"
    else
        print_warning "pgadmin_password.txt already exists, skipping"
    fi

    # Authenticator password (FIXED - dynamic generation)
    if [ ! -f secrets/authenticator_password.txt ]; then
        openssl rand -base64 32 > secrets/authenticator_password.txt
        print_success "Generated authenticator_password.txt"
    else
        print_warning "authenticator_password.txt already exists, skipping"
    fi

    # CrowdSec bouncer API key (pre-generated)
    if [ ! -f secrets/crowdsec_bouncer_key.txt ]; then
        # Generate a random API key for the bouncer (hex format for compatibility)
        BOUNCER_KEY=$(openssl rand -hex 32)
        echo "$BOUNCER_KEY" > secrets/crowdsec_bouncer_key.txt
        print_success "Generated crowdsec_bouncer_key.txt"
    else
        print_warning "crowdsec_bouncer_key.txt already exists, skipping"
        BOUNCER_KEY=$(cat secrets/crowdsec_bouncer_key.txt)
    fi

    # QueWall / Keycloak secrets
    if [ ! -f secrets/keycloak_admin_password.txt ]; then
        openssl rand -base64 32 > secrets/keycloak_admin_password.txt
        print_success "Generated keycloak_admin_password.txt"
    else
        print_warning "keycloak_admin_password.txt already exists, skipping"
    fi

    if [ ! -f secrets/keycloak_db_password.txt ]; then
        openssl rand -base64 32 > secrets/keycloak_db_password.txt
        print_success "Generated keycloak_db_password.txt"
    else
        print_warning "keycloak_db_password.txt already exists, skipping"
    fi

    if [ ! -f secrets/oauth2_client_secret.txt ]; then
        openssl rand -base64 32 > secrets/oauth2_client_secret.txt
        print_success "Generated oauth2_client_secret.txt"
    else
        print_warning "oauth2_client_secret.txt already exists, skipping"
    fi

    if [ ! -f secrets/oauth2_cookie_secret.txt ]; then
        # Generate 32 random bytes as binary (not base64) for oauth2-proxy AES cipher
        python3 << 'PYSCRIPT'
import secrets
with open('secrets/oauth2_cookie_secret.txt', 'wb') as f:
    f.write(secrets.token_bytes(32))
PYSCRIPT
        print_success "Generated oauth2_cookie_secret.txt (32 bytes)"
    else
        print_warning "oauth2_cookie_secret.txt already exists, skipping"
    fi

    # Django CMS secrets
    if [ ! -f secrets/djangocms_db_password.txt ]; then
        openssl rand -base64 32 > secrets/djangocms_db_password.txt
        print_success "Generated djangocms_db_password.txt"
    else
        print_warning "djangocms_db_password.txt already exists, skipping"
    fi

    if [ ! -f secrets/django_secret_key.txt ]; then
        openssl rand -base64 50 > secrets/django_secret_key.txt
        print_success "Generated django_secret_key.txt"
    else
        print_warning "django_secret_key.txt already exists, skipping"
    fi

    if [ ! -f secrets/django_superuser_password.txt ]; then
        openssl rand -base64 32 > secrets/django_superuser_password.txt
        print_success "Generated django_superuser_password.txt"
    else
        print_warning "django_superuser_password.txt already exists, skipping"
    fi

    if [ ! -f secrets/djangocms_keycloak_client_secret.txt ]; then
        openssl rand -base64 32 > secrets/djangocms_keycloak_client_secret.txt
        print_success "Generated djangocms_keycloak_client_secret.txt"
    else
        print_warning "djangocms_keycloak_client_secret.txt already exists, skipping"
    fi

    # OmniScope / Grafana secrets
    if [ ! -f secrets/grafana_admin_password.txt ]; then
        openssl rand -base64 32 > secrets/grafana_admin_password.txt
        print_success "Generated grafana_admin_password.txt"
    else
        print_warning "grafana_admin_password.txt already exists, skipping"
    fi

    if [ ! -f secrets/grafana_oauth_client_secret.txt ]; then
        openssl rand -base64 32 > secrets/grafana_oauth_client_secret.txt
        print_success "Generated grafana_oauth_client_secret.txt"
    else
        print_warning "grafana_oauth_client_secret.txt already exists, skipping"
    fi

    # Set permissions (644 allows container users to read secrets)
    chmod 644 secrets/*.txt
    print_success "Permissions set on secrets"
}

# Create .env file
create_env_file() {
    echo "Creating .env file for environment variables..."

    if [ ! -f .env ]; then
        # Get the bouncer key from the secrets file
        BOUNCER_KEY=$(cat secrets/crowdsec_bouncer_key.txt)

        cat > .env << EOF
# CrowdSec Bouncer API Key
# Generated by setup.sh on $(date)
# Do not commit this file to version control!
CROWDSEC_BOUNCER_KEY=$BOUNCER_KEY
EOF
        chmod 600 .env
        print_success "Created .env file with CROWDSEC_BOUNCER_KEY"
    else
        print_warning ".env file already exists, skipping (delete and re-run setup.sh to regenerate)"
    fi
}

# Generate Traefik dynamic config from template
generate_traefik_config() {
    echo "Generating Traefik dynamic configuration..."

    if [ ! -f secrets/crowdsec_bouncer_key.txt ]; then
        print_error "Bouncer key not found. Run generate_secrets first."
        exit 1
    fi

    BOUNCER_KEY=$(cat secrets/crowdsec_bouncer_key.txt)

    # Generate config.yml from template
    sed "s/__CROWDSEC_BOUNCER_KEY__/$BOUNCER_KEY/" \
        KoolFlows/traefik/dynamic/config.yml.template > \
        KoolFlows/traefik/dynamic/config.yml

    print_success "Generated KoolFlows/traefik/dynamic/config.yml"
}

# Setup Keycloak realm and update client secrets (after services are running)
setup_keycloak_realm() {
    echo "Setting up Keycloak realm and OAuth2-proxy client..."

    # Wait for Keycloak to be ready
    for i in {1..30}; do
        if docker exec pesequel-postgres curl -s http://quewall-keycloak:8080/realms/master > /dev/null 2>&1; then
            print_success "Keycloak is ready"
            break
        fi
        if [ $i -eq 30 ]; then
            print_error "Keycloak did not become ready in time"
            return 1
        fi
        sleep 2
    done

    KEYCLOAK_PASSWORD=$(cat secrets/keycloak_admin_password.txt)
    OAUTH2_SECRET=$(cat secrets/oauth2_client_secret.txt)
    DJANGOCMS_SECRET=$(cat secrets/djangocms_keycloak_client_secret.txt)
    GRAFANA_SECRET=$(cat secrets/grafana_oauth_client_secret.txt)

    # Get admin token
    TOKEN=$(docker exec pesequel-postgres bash -c "curl -s -X POST http://quewall-keycloak:8080/realms/master/protocol/openid-connect/token \
      -H 'Content-Type: application/x-www-form-urlencoded' \
      -d 'client_id=admin-cli' \
      -d 'username=admin' \
      -d 'password=${KEYCLOAK_PASSWORD}' \
      -d 'grant_type=password'" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

    if [ -z "$TOKEN" ]; then
        print_error "Failed to obtain Keycloak admin token"
        return 1
    fi

    # Wait for theddt realm to be imported from realm-export.json
    echo "Waiting for theddt realm to be imported..."
    for i in {1..30}; do
        REALM_EXISTS=$(docker exec pesequel-postgres curl -s http://quewall-keycloak:8080/realms/theddt 2>&1 | grep -c "theddt" || echo "0")
        if [ "$REALM_EXISTS" -gt 0 ]; then
            print_success "TheDDT realm imported successfully"
            break
        fi
        if [ $i -eq 30 ]; then
            print_error "TheDDT realm was not imported. Check realm-export.json"
            return 1
        fi
        sleep 2
    done

    # Update client secrets for oauth2-proxy-client and djangocms-client
    # (Clients are defined in realm-export.json but secrets are masked)
    update_client_secret "oauth2-proxy-client" "$OAUTH2_SECRET" "$TOKEN"
    update_client_secret "djangocms-client" "$DJANGOCMS_SECRET" "$TOKEN"

    # Note: grafana-client must be created manually in Keycloak admin console
    # After creating it, you can run: update_client_secret "grafana-client" "$GRAFANA_SECRET" "$TOKEN"
    # Or re-export the realm with the client included
}

# Update client secret in Keycloak
update_client_secret() {
    local CLIENT_ID=$1
    local SECRET=$2
    local TOKEN=$3

    # Get client UUID
    CLIENT_UUID=$(docker exec pesequel-postgres bash -c "curl -s -X GET \
      http://quewall-keycloak:8080/admin/realms/theddt/clients \
      -H 'Authorization: Bearer ${TOKEN}' \
      -H 'Content-Type: application/json'" | \
      grep -o "\"id\":\"[^\"]*\",\"clientId\":\"${CLIENT_ID}\"" | \
      grep -o "\"id\":\"[^\"]*\"" | cut -d'"' -f4)

    if [ -z "$CLIENT_UUID" ]; then
        print_error "Failed to find client ${CLIENT_ID} in realm theddt"
        echo "Available clients:"
        docker exec pesequel-postgres bash -c "curl -s -X GET \
          http://quewall-keycloak:8080/admin/realms/theddt/clients \
          -H 'Authorization: Bearer ${TOKEN}' \
          -H 'Content-Type: application/json'" | grep -o "\"clientId\":\"[^\"]*\"" | cut -d'"' -f4
        return 1
    fi

    # Update client secret
    docker exec pesequel-postgres bash -c "curl -s -X PUT \
      http://quewall-keycloak:8080/admin/realms/theddt/clients/${CLIENT_UUID} \
      -H 'Authorization: Bearer ${TOKEN}' \
      -H 'Content-Type: application/json' \
      -d '{
        \"secret\": \"${SECRET}\"
      }'" > /dev/null 2>&1

    print_success "Updated ${CLIENT_ID} secret in Keycloak"
}

# Update hosts file instructions
show_dns_instructions() {
    echo ""
    echo "=========================================="
    echo "DNS Configuration Required"
    echo "=========================================="
    echo "Please add the following entries to your /etc/hosts file:"
    echo ""
    echo "127.0.0.1 theddt.local"
    echo "127.0.0.1 pgadmin.theddt.local"
    echo "127.0.0.1 traefik.theddt.local"
    echo "127.0.0.1 keycloak.theddt.local"
    echo "127.0.0.1 auth.theddt.local"
    echo "127.0.0.1 omniscope.theddt.local"
    echo "127.0.0.1 prometheus.theddt.local"
    echo "127.0.0.1 alertmanager.theddt.local"
    echo ""
    echo "Linux/Mac: sudo nano /etc/hosts"
    echo "Windows: C:\\Windows\\System32\\drivers\\etc\\hosts (Run as Administrator)"
    echo ""
    print_warning "You need to edit the hosts file manually"
    echo ""
    read -p "Press Enter after you've updated the hosts file..."
}

# Create Docker network
create_network() {
    echo "Creating Docker network 'web'..."
    if docker network inspect web > /dev/null 2>&1; then
        print_warning "Network 'web' already exists, skipping"
    else
        docker network create web
        print_success "Network 'web' created"
    fi
}

# Build and start services
start_services() {
    echo "Building custom Docker images..."
    docker compose build
    print_success "Images built"

    echo "Starting services..."
    docker compose up -d
    print_success "Services started"
}

# Wait for health checks
wait_for_health() {
    echo "Waiting for services to be healthy..."
    sleep 10

    # Check each service (removed crowdsec-traefik-bouncer - we migrated to plugin)
    services=("crowdsec" "traefik" "postgres" "pgbouncer" "pgadmin" "keycloak" "oauth2-proxy" "grafana" "prometheus" "loki" "alertmanager")

    for service in "${services[@]}"; do
        echo "Checking $service..."
        for i in {1..30}; do
            # Try koolflows-, pesequel-, quewall-, or omniscope- prefixes
            health=$(docker inspect --format='{{.State.Health.Status}}' "koolflows-$service" 2>/dev/null || \
                     docker inspect --format='{{.State.Health.Status}}' "pesequel-$service" 2>/dev/null || \
                     docker inspect --format='{{.State.Health.Status}}' "quewall-$service" 2>/dev/null || \
                     docker inspect --format='{{.State.Health.Status}}' "omniscope-$service" 2>/dev/null || \
                     echo "unknown")
            if [ "$health" = "healthy" ]; then
                print_success "$service is healthy"
                break
            fi
            if [ $i -eq 30 ]; then
                print_warning "$service is not healthy yet (status: $health)"
            fi
            sleep 2
        done
    done
}

# Display final information
show_summary() {
    echo ""
    echo "=========================================="
    echo "Setup Complete!"
    echo "=========================================="
    echo ""
    echo "Services are now running:"
    echo "  • Traefik Dashboard: http://traefik.theddt.local (protected by CrowdSec)"
    echo "  • pgAdmin: http://pgadmin.theddt.local"
    echo "  • Keycloak Admin: http://keycloak.theddt.local"
    echo "  • OAuth2 Auth: http://auth.theddt.local"
    echo "  • PostgreSQL: localhost:5432"
    echo "  • pgBouncer: localhost:6432"
    echo ""
    echo "OmniScope Monitoring Stack:"
    echo "  • Grafana: http://omniscope.theddt.local (Keycloak SSO)"
    echo "  • Prometheus: http://prometheus.theddt.local"
    echo "  • AlertManager: http://alertmanager.theddt.local"
    echo ""
    echo "Credentials:"
    echo "  • PostgreSQL User: $(cat secrets/postgres_user.txt)"
    echo "  • PostgreSQL Password: $(cat secrets/postgres_password.txt)"
    echo "  • pgAdmin Email: $(cat secrets/pgadmin_email.txt)"
    echo "  • pgAdmin Password: $(cat secrets/pgadmin_password.txt)"
    echo "  • Keycloak Admin: admin"
    echo "  • Keycloak Password: $(cat secrets/keycloak_admin_password.txt)"
    echo "  • Grafana Admin: admin"
    echo "  • Grafana Password: $(cat secrets/grafana_admin_password.txt)"
    echo ""
    echo "Useful Commands:"
    echo "  • View logs: docker compose logs -f [service_name]"
    echo "  • Check status: docker compose ps"
    echo "  • CrowdSec decisions: docker exec koolflows-crowdsec cscli decisions list"
    echo "  • Stop services: ./teardown.sh"
    echo ""
    print_success "Happy coding!"
}

# Main execution
main() {
    check_prerequisites
    create_directories
    generate_secrets
    create_env_file
    generate_traefik_config
    show_dns_instructions
    create_network
    start_services
    wait_for_health
    setup_keycloak_realm
    show_summary
}

main "$@"
