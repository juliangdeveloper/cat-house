#!/bin/bash
# Generate Alembic migrations for all services
#
# This script generates migration files for all services that need them.
# It should be run when models are modified and new migrations are needed.
#
# Usage: ./scripts/generate-migrations.sh

set -euo pipefail

echo -e "\033[0;36mGenerating database migrations for all services...\033[0m"
echo ""

# Function to generate migration for a service
generate_service_migration() {
    local service_name=$1
    local migration_message=$2
    local step_number=$3
    local total_steps=$4
    
    echo -e "\033[0;33m  [$step_number/$total_steps] Generating $service_name migration...\033[0m"
    
    if docker-compose exec -T "$service_name" alembic revision --autogenerate -m "$migration_message"; then
        echo -e "\033[0;32m✓ $service_name migration generated successfully\033[0m"
        echo ""
        return 0
    else
        echo -e "\033[0;31mERROR: Failed to generate $service_name migration\033[0m"
        return 1
    fi
}

# Ensure services are running
echo -e "\033[0;36mEnsuring services are running...\033[0m"
docker-compose up -d
sleep 5
echo ""

# Generate migrations for each service
success=true

# Auth service
if ! generate_service_migration "auth-service" "Schema update" 1 3; then
    success=false
fi

# Catalog service
if ! generate_service_migration "catalog-service" "Schema update" 2 3; then
    success=false
fi

# Installation service
if ! generate_service_migration "installation-service" "Schema update" 3 3; then
    success=false
fi

if [ "$success" = true ]; then
    echo -e "\033[0;32mAll migrations generated successfully!\033[0m"
    echo ""
    echo -e "\033[0;36mNext steps:\033[0m"
    echo "  1. Review the generated migration files in each service's alembic/versions/ folder"
    echo "  2. Run ./scripts/init-local-db.sh to apply migrations to local database"
    echo "  3. Commit the migration files to git"
    echo ""
    exit 0
else
    echo -e "\033[0;31mSome migrations failed to generate. Check the errors above.\033[0m"
    exit 1
fi
