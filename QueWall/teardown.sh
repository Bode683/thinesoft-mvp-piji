#!/bin/bash

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
KEEP_VOLUMES=false
CLEAN_SECRETS=false
FORCE=false
NETWORK_NAME="quewall-network"

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

# Parse command line arguments
parse_args() {
    while [[ "$#" -gt 0 ]]; do
        case $1 in
            --keep-volumes)
                KEEP_VOLUMES=true
                log_info "Will keep volumes after teardown"
                ;;
            --clean-secrets)
                CLEAN_SECRETS=true
                log_info "Will remove secrets directory"
                ;;
            --force)
                FORCE=true
                log_info "Forcing teardown without confirmation"
                ;;
            *)
                log_error "Unknown option: $1"
                echo ""
                echo "Usage: $0 [--keep-volumes] [--clean-secrets] [--force]"
                echo ""
                echo "Options:"
                echo "  --keep-volumes   Keep Docker volumes (default: remove)"
                echo "  --clean-secrets  Remove secrets directory (default: keep)"
                echo "  --force          Skip confirmation prompt"
                exit 1
                ;;
        esac
        shift
    done
}

# Confirm teardown
confirm_teardown() {
    if [ "$FORCE" = true ]; then
        return 0
    fi

    echo ""
    echo -e "${YELLOW}WARNING: This will stop and remove all QueWall containers.${NC}"
    echo ""

    if [ "$KEEP_VOLUMES" = false ]; then
        echo -e "${RED}Your PostgreSQL data will be deleted unless you use --keep-volumes${NC}"
    fi

    echo ""
    read -p "Do you want to continue? (y/N) " -n 1 -r
    echo

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Teardown cancelled"
        exit 0
    fi
}

# Stop and remove containers
stop_containers() {
    log_info "Stopping and removing containers..."

    if ! command -v docker-compose &> /dev/null; then
        log_error "docker-compose is not installed or not in PATH"
        exit 1
    fi

    docker-compose down || {
        log_warning "Some containers may not have stopped cleanly"
    }

    log_success "Containers stopped and removed"
}

# Remove volumes
remove_volumes() {
    if [ "$KEEP_VOLUMES" = true ]; then
        log_warning "Keeping Docker volumes as requested"
        return
    fi

    log_info "Removing Docker volumes..."

    # Use docker-compose down with -v flag
    docker-compose down -v 2>/dev/null || {
        log_warning "Some volumes may not have been removed"
    }

    log_success "Docker volumes removed"
}

# Remove network
remove_network() {
    log_info "Removing Docker network..."

    if docker network ls | grep -q "$NETWORK_NAME"; then
        docker network rm "$NETWORK_NAME" 2>/dev/null || {
            log_warning "Network may still be in use, it will be removed automatically"
        }
        log_success "Docker network removed: $NETWORK_NAME"
    else
        log_warning "Network $NETWORK_NAME not found"
    fi
}

# Remove secrets
remove_secrets() {
    if [ "$CLEAN_SECRETS" = false ]; then
        log_warning "Keeping secrets directory (use --clean-secrets to remove)"
        return
    fi

    if [ ! -d "./secrets" ]; then
        log_warning "Secrets directory not found"
        return
    fi

    log_info "Removing secrets directory..."
    rm -rf ./secrets

    log_success "Secrets directory removed"
}

# Remove generated realm export
remove_generated_files() {
    log_info "Removing generated files..."

    if [ -f "./keycloak/realm-export-generated.json" ]; then
        rm -f ./keycloak/realm-export-generated.json
        log_success "Removed realm-export-generated.json"
    fi
}

# Display completion information
display_info() {
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║   QueWall Teardown Complete!                          ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""

    if [ "$KEEP_VOLUMES" = true ]; then
        echo -e "${YELLOW}Note:${NC} Docker volumes are still present."
        echo "      To remove them, run: ${BLUE}docker volume prune${NC}"
        echo ""
    fi

    if [ "$CLEAN_SECRETS" = false ]; then
        echo -e "${YELLOW}Note:${NC} Secrets directory is still present."
        echo "      To remove it, run: ${BLUE}./teardown.sh --clean-secrets${NC}"
        echo ""
    fi

    echo "To run setup again:"
    echo "  ${BLUE}./setup.sh${NC}"
    echo ""
}

# Main execution
main() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║   QueWall Teardown                                    ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""

    parse_args "$@"
    confirm_teardown
    stop_containers
    remove_volumes
    remove_network
    remove_generated_files
    remove_secrets
    display_info
}

# Run main function
main "$@"
