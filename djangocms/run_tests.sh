#!/bin/bash

# Test runner script for Django CMS
# This script runs all tests or specific test modules

set -e

# Color output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Django CMS Test Suite${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

# Change to the script directory
cd "$(dirname "$0")"

# Function to run tests
run_tests() {
    local test_path=$1
    local test_name=$2

    echo -e "${YELLOW}Running: ${test_name}${NC}"
    if python manage.py test "$test_path" --verbosity=2; then
        echo -e "${GREEN}✓ ${test_name} PASSED${NC}"
        echo ""
        return 0
    else
        echo -e "${RED}✗ ${test_name} FAILED${NC}"
        echo ""
        return 1
    fi
}

# If an argument is provided, run specific tests
if [ $# -gt 0 ]; then
    echo "Running specific tests: $@"
    python manage.py test "$@" --verbosity=2
    exit $?
fi

# Otherwise run all tests by category
echo "Running all tests..."
echo ""

failed_tests=()

# Identity app tests
echo -e "${YELLOW}=== IDENTITY APP TESTS ===${NC}"
run_tests "apps.identity.tests.test_models" "Identity Models" || failed_tests+=("Identity Models")
run_tests "apps.identity.tests.test_auth_context" "Auth Context" || failed_tests+=("Auth Context")

# Tenants app tests
echo -e "${YELLOW}=== TENANTS APP TESTS ===${NC}"
run_tests "apps.tenants.tests.test_models" "Tenant Models" || failed_tests+=("Tenant Models")
run_tests "apps.tenants.tests.test_selectors" "Tenant Selectors" || failed_tests+=("Tenant Selectors")
run_tests "apps.tenants.tests.test_services" "Tenant Services" || failed_tests+=("Tenant Services")
run_tests "apps.tenants.tests.test_permissions" "Tenant Permissions" || failed_tests+=("Tenant Permissions")

# Subscribers app tests
echo -e "${YELLOW}=== SUBSCRIBERS APP TESTS ===${NC}"
run_tests "apps.subscribers.tests.test_models" "Subscriber Models" || failed_tests+=("Subscriber Models")
run_tests "apps.subscribers.tests.test_permissions" "Subscriber Permissions" || failed_tests+=("Subscriber Permissions")

# Platform app tests
echo -e "${YELLOW}=== PLATFORM APP TESTS ===${NC}"
run_tests "apps.platform.tests.test_permissions" "Platform Permissions" || failed_tests+=("Platform Permissions")

# Summary
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}TEST SUMMARY${NC}"
echo -e "${YELLOW}========================================${NC}"

if [ ${#failed_tests[@]} -eq 0 ]; then
    echo -e "${GREEN}All tests PASSED! ✓${NC}"
    exit 0
else
    echo -e "${RED}Failed tests:${NC}"
    for test in "${failed_tests[@]}"; do
        echo -e "${RED}  ✗ $test${NC}"
    done
    exit 1
fi
