# Auth Service

Authentication and authorization service for Cat House platform.

## Features

- JWT-based authentication
- User registration and login
- Role-based access control
- Token refresh mechanism

## API Endpoints

### Health Check
- `GET /api/v1/auth/health` - Service health status

### Authentication (To be implemented)
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh JWT token
- `GET /api/v1/auth/me` - Get current user info

## Local Development

### Prerequisites
- Python 3.11+
- Docker (optional)

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env

# Edit .env with your configuration

# Run the service
python -m uvicorn app.main:app --reload --port 8005
```

### Using Docker
```bash
# Build the image
docker build -t auth-service .

# Run the container
docker run -p 8005:8005 --env-file .env auth-service
```

## Database Migrations

**IMPORTANT:** This service is the **ONLY** service that manages database migrations for the entire Cat House backend.

### Quick Reference

```bash
# Generate new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history --verbose

# Check current revision
alembic current
```

### Safe Production Workflow

```bash
# 1. Generate SQL preview
alembic upgrade head --sql > migration.sql

# 2. Test in temporary Neon branch using MCP tools
#    (See MIGRATIONS.md for detailed workflow)

# 3. Apply to production after successful testing
alembic upgrade head
```

**Full documentation:** [MIGRATIONS.md](./MIGRATIONS.md)

## Testing
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

## Environment Variables

See `.env.example` for all available configuration options.

## API Documentation

When running in debug mode, Swagger docs available at:
- http://localhost:8005/api/v1/docs
- http://localhost:8005/api/v1/redoc

## Port

Default: **8005**
