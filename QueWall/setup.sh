#!/bin/bash

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SECRETS_DIR="./secrets"
REALM_EXPORT_SOURCE="./keycloak/realm-export.json"
REALM_EXPORT_GENERATED="./keycloak/realm-export-generated.json"
NETWORK_NAME="quewall-network"
TIMEOUT=120

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi
    log_success "Docker found"

    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed or not in PATH"
        exit 1
    fi
    log_success "Docker Compose found"

    if ! command -v openssl &> /dev/null; then
        log_error "openssl is not installed or not in PATH"
        exit 1
    fi
    log_success "openssl found"

    log_info "All prerequisites met"
}

# Generate secure random secret
generate_secret() {
    local secret_name=$1
    local secret_file="${SECRETS_DIR}/${secret_name}.txt"

    if [ -f "$secret_file" ]; then
        log_warning "Secret $secret_name already exists, skipping generation"
        return
    fi

    log_info "Generating secret: $secret_name"

    # Generate random base64 string
    if [[ "$secret_name" == "oauth2_cookie_secret" ]]; then
        # Cookie secret needs to be URL-safe base64, 32 bytes
        openssl rand -base64 32 | tr -d '\n' > "$secret_file"
    else
        # Other secrets can be standard base64
        openssl rand -base64 32 | tr -d '\n' > "$secret_file"
    fi

    log_success "Generated secret: $secret_name"
}

# Replace placeholder in realm export
configure_realm_export() {
    log_info "Configuring Keycloak realm export..."

    if [ ! -f "$REALM_EXPORT_SOURCE" ]; then
        log_error "Realm export not found at $REALM_EXPORT_SOURCE"
        exit 1
    fi

    # Read the client secret
    local client_secret
    client_secret=$(cat "${SECRETS_DIR}/oauth2_client_secret.txt")

    # Create generated realm export with client secret substituted
    sed "s|OAUTH2_CLIENT_SECRET_PLACEHOLDER|${client_secret}|g" "$REALM_EXPORT_SOURCE" > "$REALM_EXPORT_GENERATED"

    log_success "Realm export configured"
}

# Create Docker network
create_network() {
    log_info "Creating Docker network: $NETWORK_NAME"

    if docker network ls | grep -q "$NETWORK_NAME"; then
        log_warning "Network $NETWORK_NAME already exists, skipping creation"
        return
    fi

    docker network create "$NETWORK_NAME" || {
        log_error "Failed to create network"
        exit 1
    }

    log_success "Docker network created: $NETWORK_NAME"
}

# Wait for service to be healthy
wait_for_service() {
    local service_name=$1
    local container_name=$2
    local health_check=$3
    local max_attempts=30
    local attempt=0

    log_info "Waiting for $service_name to be healthy..."

    while [ $attempt -lt $max_attempts ]; do
        if eval "$health_check" &> /dev/null; then
            log_success "$service_name is healthy"
            return 0
        fi

        attempt=$((attempt + 1))
        echo -n "."
        sleep 2
    done

    echo ""
    log_error "$service_name failed to become healthy after $((max_attempts * 2)) seconds"
    log_error "Check logs with: docker-compose logs $service_name"
    exit 1
}

# Start services
start_services() {
    log_info "Starting services..."

    # Start postgres
    log_info "Starting PostgreSQL..."
    docker-compose up -d postgres
    wait_for_service "PostgreSQL" "quewall-postgres" "docker-compose exec -T postgres pg_isready -U keycloak -d keycloak"

    # Start keycloak
    log_info "Starting Keycloak..."
    docker-compose up -d keycloak
    wait_for_service "Keycloak" "quewall-keycloak" "curl -f http://localhost:8080/health/ready 2>/dev/null"

    # Start oauth2-proxy
    log_info "Starting oauth2-proxy..."
    docker-compose up -d oauth2-proxy
    wait_for_service "oauth2-proxy" "quewall-oauth2-proxy" "curl -f http://localhost:4180/ping 2>/dev/null"

    # Start remaining services
    log_info "Starting Traefik and whoami..."
    docker-compose up -d traefik whoami

    # Wait a moment for Traefik to stabilize
    sleep 3

    log_success "All services started"
}

# Display completion information
display_info() {
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║   QueWall Setup Complete!                             ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""

    # Get the admin password
    local admin_password
    admin_password=$(cat "${SECRETS_DIR}/keycloak_admin_password.txt")

    echo -e "${YELLOW}Next Steps:${NC}"
    echo ""
    echo "1. Add these entries to your hosts file:"
    echo ""
    echo "   ${BLUE}127.0.0.1 keycloak.theddt.local${NC}"
    echo "   ${BLUE}127.0.0.1 auth.theddt.local${NC}"
    echo "   ${BLUE}127.0.0.1 app.theddt.local${NC}"
    echo ""
    echo "   Linux/macOS: /etc/hosts"
    echo "   Windows: C:\\Windows\\System32\\drivers\\etc\\hosts"
    echo ""

    echo "2. Access the services:"
    echo ""
    echo "   ${BLUE}Protected App:${NC}       http://app.theddt.local"
    echo "   ${BLUE}Keycloak Admin:${NC}      http://keycloak.theddt.local"
    echo "   ${BLUE}Traefik Dashboard:${NC}   http://localhost:8080"
    echo ""

    echo "3. Login credentials:"
    echo ""
    echo "   ${BLUE}Username:${NC} admin"
    echo "   ${BLUE}Password:${NC} $admin_password"
    echo ""

    echo "4. Test the authentication flow:"
    echo ""
    echo "   - Open http://app.theddt.local in your browser"
    echo "   - You will be redirected to Keycloak login"
    echo "   - Login with: ${BLUE}testuser${NC} / ${BLUE}password123${NC}"
    echo "   - You should be redirected to the whoami service"
    echo "   - You should see your authenticated user headers"
    echo ""

    echo "5. View OIDC discovery endpoint:"
    echo ""
    echo "   ${BLUE}http://keycloak.theddt.local/realms/theddt/.well-known/openid-configuration${NC}"
    echo ""

    echo "6. To stop all services:"
    echo ""
    echo "   ${BLUE}./teardown.sh${NC}"
    echo ""

    echo -e "${YELLOW}Useful Commands:${NC}"
    echo ""
    echo "   View service logs:       ${BLUE}docker-compose logs -f <service>{{NC}"
    echo "   List running containers: ${BLUE}docker-compose ps${NC}"
    echo "   View network info:       ${BLUE}docker network inspect quewall-network${NC}"
    echo ""
}

# Main execution
main() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║   QueWall Setup - Starting                            ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""

    check_prerequisites

    # Create secrets directory
    log_info "Creating secrets directory..."
    mkdir -p "$SECRETS_DIR"

    # Generate secrets
    generate_secret "keycloak_admin_password"
    generate_secret "postgres_password"
    generate_secret "oauth2_client_secret"
    generate_secret "oauth2_cookie_secret"

    # Configure realm export with secrets
    configure_realm_export

    # Create network
    create_network

    # Start services
    start_services

    # Display information
    display_info
}

# Run main function
main "$@"
