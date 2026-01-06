#!/bin/bash
# init-local-db.sh
# Initialize local PostgreSQL database for Cat House development

set -e

echo "🐱 Initializing Cat House Local Database..."

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
until docker-compose exec -T postgres pg_isready -U catuser -d cathouse > /dev/null 2>&1; do
  echo "   Waiting for database connection..."
  sleep 2
done

echo "✅ PostgreSQL is ready!"

# Check if migrations have already been run
TABLES_EXIST=$(docker-compose exec -T postgres psql -U catuser -d cathouse -tAc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'auth' AND table_name = 'users';")

if [ "$TABLES_EXIST" -gt "0" ]; then
  echo "⚠️  Database already initialized. Skipping migration."
  echo "   To reset the database, run: docker-compose down -v && docker-compose up -d"
  exit 0
fi

echo "📊 Running database migrations..."

# Run Alembic migrations from all services
echo "  [1/3] Running auth schema migrations..."
docker-compose exec -T auth-service alembic upgrade head
if [ $? -ne 0 ]; then
  echo "❌ Auth migration failed. Check logs with: docker-compose logs auth-service"
  exit 1
fi

echo "  [2/3] Running catalog schema migrations..."
docker-compose exec -T catalog-service alembic upgrade head
if [ $? -ne 0 ]; then
  echo "❌ Catalog migration failed. Check logs with: docker-compose logs catalog-service"
  exit 1
fi

echo "  [3/3] Running installation schema migrations..."
docker-compose exec -T installation-service alembic upgrade head
if [ $? -ne 0 ]; then
  echo "❌ Installation migration failed. Check logs with: docker-compose logs installation-service"
  exit 1
fi

# Verify migrations succeeded
echo "🔍 Verifying schema integrity..."
SCHEMA_CHECK=$(docker-compose exec -T postgres psql -U catuser -d cathouse -tAc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema IN ('auth', 'catalog', 'installation') AND table_name IN ('users', 'cats', 'installations');")

if [ "$SCHEMA_CHECK" -ge "3" ]; then
  echo "✅ Database migrations completed successfully!"
  echo "✅ Schema verification passed: All core tables exist"
  echo ""
  echo "🎉 Local database is ready for development!"
  echo ""
  echo "Connection details:"
  echo "  Host: localhost"
  echo "  Port: 5435"
  echo "  Database: cathouse"
  echo "  User: catuser"
  echo "  Password: catpass"
  echo ""
  echo "DATABASE_URL for services:"
  echo "  postgresql+asyncpg://catuser:catpass@postgres:5432/cathouse"
else
  echo "❌ Schema verification failed: Expected 3+ core tables, found $SCHEMA_CHECK"
  echo "Run: docker-compose logs auth-service catalog-service installation-service"
  exit 1
fi
