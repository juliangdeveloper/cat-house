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

# Run Alembic migrations from auth-service
docker-compose exec -T auth-service alembic upgrade head

if [ $? -eq 0 ]; then
  echo "✅ Database migrations completed successfully!"
  echo ""
  echo "🎉 Local database is ready for development!"
  echo ""
  echo "Connection details:"
  echo "  Host: localhost"
  echo "  Port: 5432"
  echo "  Database: cathouse"
  echo "  User: catuser"
  echo "  Password: catpass"
  echo ""
  echo "DATABASE_URL for services:"
  echo "  postgresql+asyncpg://catuser:catpass@postgres:5432/cathouse"
else
  echo "❌ Migration failed. Check logs with: docker-compose logs auth-service"
  exit 1
fi
