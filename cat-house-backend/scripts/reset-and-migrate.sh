#!/bin/bash
# Reset database and run fresh migrations
#
# This script:
# 1. Stops all services and removes volumes (full reset)
# 2. Starts services fresh
# 3. Generates new migrations for all services
# 4. Applies all migrations to the database
#
# WARNING: This will DELETE all local data!
#
# Usage: ./scripts/reset-and-migrate.sh

set -euo pipefail

echo -e "\033[0;31m========================================"
echo -e "  DATABASE RESET AND MIGRATION"
echo -e "========================================\033[0m"
echo ""
echo -e "\033[0;33mWARNING: This will DELETE all local data!\033[0m"
echo ""

read -p "Are you sure you want to continue? (yes/no): " confirmation
if [ "$confirmation" != "yes" ]; then
    echo -e "\033[0;33mOperation cancelled.\033[0m"
    exit 0
fi

echo ""
echo -e "\033[0;36mStep 1: Stopping services and removing volumes...\033[0m"
docker-compose down -v
echo -e "\033[0;32m✓ Services stopped and volumes removed\033[0m"
echo ""

echo -e "\033[0;36mStep 2: Rebuilding and starting services...\033[0m"
docker-compose up -d --build
sleep 10
echo -e "\033[0;32m✓ Services rebuilt and started\033[0m"
echo ""

echo -e "\033[0;36mStep 3: Generating migrations...\033[0m"
./scripts/generate-migrations.sh
echo -e "\033[0;32m✓ Migrations generated\033[0m"
echo ""

echo -e "\033[0;36mStep 4: Applying migrations...\033[0m"
./scripts/init-local-db.sh
echo -e "\033[0;32m✓ Migrations applied\033[0m"
echo ""

echo -e "\033[0;32m========================================"
echo -e "  RESET AND MIGRATION COMPLETE"
echo -e "========================================\033[0m"
echo ""
echo -e "\033[0;32mDatabase is ready for development!\033[0m"
