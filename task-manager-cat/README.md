# Task Manager API - My Cat Manager

Backend-only REST API service for task management with Cat House Platform integration using Command Pattern architecture.

## Overview

The Task Manager API is a stateless, serverless-ready backend service that provides:

- **Command Pattern Architecture:** Single `/execute` endpoint for all task operations
- **Service API Key Authentication:** X-Service-Key header validation (not JWT)
- **Cat House Platform Integration:** `/stats` endpoint for gamification data
- **Production-Ready:** Structured logging, type safety, comprehensive testing

## Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| **Runtime** | Python | 3.12 |
| **Framework** | FastAPI | 0.115.0 |
| **Database** | PostgreSQL (Neon serverless) | 16+ |
| **Database Client** | asyncpg | 0.29.0 |
| **Migrations** | Alembic | 1.13.1 |
| **Authentication** | Service API Keys | - |
| **Logging** | structlog | 24.4.0 |
| **Testing** | pytest + pytest-asyncio | 8.3.0 |
| **Code Quality** | ruff + mypy | 0.6.8 / 1.11.0 |
| **Server** | uvicorn (dev) + gunicorn (prod) | 0.31.0 / 23.0.0 |
| **Deployment** | AWS ECS Fargate | - |
| **IaC** | Terraform | - |

## Prerequisites

- **Docker Desktop** installed and running
- **Git** installed
- **Python 3.12** (optional, for local non-Docker development)

## Quick Start

```bash
# 1. Clone the repository
git clone <repository-url>
cd task-manager-api

# 2. Copy environment template
cp .env.example .env.dev

# 3. Start development environment
docker-compose -f docker-compose.dev.yml up --build

# 4. Access API documentation
open http://localhost:8888/docs
```

The API will be available at:
- **Swagger UI:** http://localhost:8888/docs
- **ReDoc:** http://localhost:8888/redoc
- **API Base:** http://localhost:8888

## Environment Configuration

### Configuration Variables

The application uses Pydantic Settings for type-safe configuration management. All required variables are validated on startup (fail-fast principle).

| Variable | Required | Default | Description | Example |
|----------|----------|---------|-------------|---------|
| `DATABASE_URL` | ✅ Yes | None | PostgreSQL connection string (asyncpg driver) | `postgresql+asyncpg://user:pass@host:5432/db?sslmode=require` |
| `MIGRATION_DATABASE_URL` | No | Uses `DATABASE_URL` | Direct connection for Alembic migrations (psycopg2) | `postgresql://user:pass@host:5432/db?sslmode=require` |
| `ENVIRONMENT` | No | `development` | Runtime environment identifier | `development`, `staging`, `production` |
| `LOG_LEVEL` | No | `INFO` | Logging verbosity level | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `PORT` | No | `8000` | Internal container port (mapped to 8888 on host) | `8000` |
| `CORS_ORIGINS` | No | `http://localhost:3000` | Comma-separated list of allowed cross-origin request sources. **Security:** Production should ONLY include Cat House domain (https://cathouse.gamificator.click). Development includes localhost:3000 (Cat House dev) and localhost:8888 (API docs access). Clients must send X-Service-Key header for authentication. | `http://localhost:3000,http://localhost:8888` (dev), `https://cathouse.gamificator.click` (prod) |
| `API_KEY_SECRET` | No* | None | Secret for generating service API keys (*required in Epic 2) | 32+ character random string |
| `ADMIN_API_KEY` | No* | None | Admin endpoint authentication (*required in Epic 2) | Secure random string |

**Note:** Variables marked with * are optional until Epic 2 (Authentication & Security) but will become required.

### Configuration Files

- **`.env.example`** - Template with all variables documented (committed to version control)
- **`.env.dev`** - Development configuration with local values (git-ignored, create from template)
- **`.env.prod`** - Production configuration (stored in AWS Secrets Manager, NOT in repository)

### Setup Instructions

1. **Copy environment template:**
   ```powershell
   Copy-Item .env.example .env.dev
   ```

2. **Edit `.env.dev` with your local database credentials:**
   ```bash
   DATABASE_URL=postgresql+asyncpg://taskuser:taskpass@postgres:5432/taskmanager_dev?sslmode=disable
   ```

3. **Start containers (configuration is automatically loaded):**
   ```powershell
   docker-compose -f docker-compose.dev.yml up
   ```

4. **Verify configuration loaded successfully:**
   Check logs for `configuration_loaded` event with your environment and log level.

### CORS Configuration Details

Task Manager API implements Cross-Origin Resource Sharing (CORS) to allow Cat House Platform (frontend web application) to make cross-origin requests from the browser. CORS is a browser security mechanism that restricts web pages from making requests to domains different from the serving domain.

**Allowed HTTP Methods:**
- `GET` - Retrieve resources (health check, stats, query tasks)
- `POST` - Create resources and execute commands
- `PATCH` - Update existing resources
- `DELETE` - Remove resources
- `OPTIONS` - Preflight requests (automatically handled by browser)

**Allowed Headers:**
- `X-Service-Key` - Service authentication (custom header, triggers CORS preflight)
- `Content-Type` - JSON payloads (application/json triggers preflight)

**CORS Preflight Behavior:**

Browsers automatically send a preflight OPTIONS request before actual requests that:
1. Use custom headers (like X-Service-Key)
2. Use Content-Type: application/json
3. Use methods other than GET/HEAD/POST with simple content types

**Preflight Example:**
```bash
curl -X OPTIONS http://localhost:8888/health \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: X-Service-Key, Content-Type" \
  -v
```

**Expected Preflight Response Headers:**
```http
HTTP/1.1 200 OK
Access-Control-Allow-Origin: http://localhost:3000
Access-Control-Allow-Methods: GET, POST, PATCH, DELETE, OPTIONS
Access-Control-Allow-Headers: X-Service-Key, Content-Type
Access-Control-Allow-Credentials: true
```

**Production Security:**

⚠️ **NEVER use wildcards (*) in production** - always specify explicit origins, methods, and headers.

```bash
# ❌ INSECURE - DO NOT USE
CORS_ORIGINS=*  # ANY website can call API from victim's browser

# ✅ SECURE - Production Configuration
CORS_ORIGINS=https://cathouse.gamificator.click  # ONLY Cat House domain
```

**CORS vs Authentication:**

CORS is NOT authentication - it only protects users from malicious websites. Service key (X-Service-Key) provides actual API authentication. Both layers are required:

1. **CORS (Browser Protection):** Prevents malicious websites from using victim's browser to call API
2. **Service Key (API Protection):** Prevents unauthorized clients (browser or non-browser) from accessing API
3. **HTTPS (Transport Protection):** Encrypts service key in transit

### Environment Variable Precedence

Configuration values are loaded in this order (highest to lowest priority):

1. **Actual environment variables** - Set in shell or `docker-compose.yml` `environment:` section
2. **Docker Compose env_file** - Loaded from `env_file: .env.dev` directive
3. **.env file** - Automatically loaded by Pydantic Settings (`model_config.env_file`)
4. **Default values** - Defined in `app/config.py` Settings class

### Overriding Configuration

You can override any setting using environment variables in `docker-compose.dev.yml`:

```yaml
services:
  api:
    env_file: .env.dev      # Load base configuration
    environment:
      LOG_LEVEL: DEBUG       # Override specific setting
      ENVIRONMENT: staging
```

### Troubleshooting Configuration Errors

**Error: "Field required" for DATABASE_URL**

Your `.env.dev` file is missing or doesn't contain `DATABASE_URL`. Solution:

```powershell
# Copy template and edit with your database connection
Copy-Item .env.example .env.dev
# Edit .env.dev and set DATABASE_URL
```

**Error: "DATABASE_URL must start with postgresql://"**

Your database URL has an invalid format. Ensure it uses PostgreSQL protocol:

- **For application runtime:** Use `postgresql+asyncpg://...` (asyncpg driver)
- **For Alembic migrations:** Use `postgresql://...` (standard psycopg2 driver)

**Error: Application starts but configuration seems wrong**

Check environment variable precedence. Docker environment variables override `.env.dev` file. Use:

```bash
docker exec taskmanager-api-dev python -c "from app.config import settings; print(f'Environment: {settings.environment}, Log Level: {settings.log_level}')"
```

**Configuration validation passes but application fails to connect**

Verify PostgreSQL container is running and accessible:

```bash
docker ps | grep postgres
docker exec -it taskmanager-postgres-dev psql -U taskuser -d taskmanager_dev
```



## Project Structure

```
task-manager-api/
├── app/                        # Application source code
│   ├── __init__.py             # Package marker
│   ├── main.py                 # FastAPI entry point
│   ├── config.py               # Environment configuration (Story 1.5)
│   ├── database.py             # Database connection (Story 3.1)
│   ├── auth.py                 # Service Key validation (Epic 2)
│   ├── commands/               # Command Pattern implementation
│   │   ├── __init__.py
│   │   ├── models.py           # Command request/response models (Story 3.3)
│   │   ├── router.py           # /execute endpoint (Story 3.3)
│   │   └── handlers/           # Command handlers (Stories 3.4-3.5)
│   │       └── __init__.py
│   ├── models/                 # Database models
│   │   ├── __init__.py
│   │   └── task.py             # Task SQLAlchemy model (Story 3.2)
│   └── services/               # Business logic layer
│       ├── __init__.py
│       └── task_service.py     # Task CRUD operations (Story 3.4)
├── tests/                      # Test suite
│   ├── unit/                   # Unit tests (Story 5.1)
│   └── integration/            # API integration tests (Story 5.2)
├── alembic/                    # Database migrations
│   └── versions/               # Migration scripts (Story 3.2)
├── terraform/                  # Infrastructure as Code (Story 5.4)
├── .github/                    # CI/CD pipelines
│   └── workflows/              # GitHub Actions (Story 5.5)
├── .env.dev                    # Development environment variables (local)
├── .env.example                # Environment template (version controlled)
├── .gitignore                  # Git ignore rules
├── Dockerfile.dev              # Development Docker image
├── docker-compose.dev.yml      # Development orchestration
├── requirements.txt            # Production dependencies
├── requirements-dev.txt        # Development dependencies
├── pyproject.toml              # Tool configuration (ruff, mypy)
└── README.md                   # This file
```

## Development Workflow

### Starting the Environment

```bash
# Start all services (API + PostgreSQL)
docker-compose -f docker-compose.dev.yml up

# Start with rebuild (after dependency changes)
docker-compose -f docker-compose.dev.yml up --build

# Start in detached mode (background)
docker-compose -f docker-compose.dev.yml up -d
```

### Stopping the Environment

```bash
# Stop services (preserves database data)
docker-compose -f docker-compose.dev.yml down

# Stop and remove volumes (clean slate)
docker-compose -f docker-compose.dev.yml down -v
```

### Viewing Logs

```bash
# API logs only
docker-compose -f docker-compose.dev.yml logs -f api

# All service logs
docker-compose -f docker-compose.dev.yml logs -f

# Last 100 lines
docker-compose -f docker-compose.dev.yml logs --tail=100
```

### Hot-Reload Development

The development environment automatically reloads on code changes:

- **Application code:** Changes in `./app` trigger uvicorn restart (1-2 seconds)
- **Test code:** Changes in `./tests` are immediately available
- **No manual restart needed:** Just save your file in VS Code

Watch the logs for reload confirmation:
```
INFO: Detected file change in 'app/main.py'. Reloading...
```

### Running Tests

```bash
# All tests
docker-compose exec api pytest tests/

# Specific test level
docker-compose exec api pytest tests/unit/
docker-compose exec api pytest tests/integration/

# With coverage
docker-compose exec api pytest --cov=app --cov-report=html tests/
```

### Code Quality Checks

```bash
# Lint and format with ruff
docker-compose exec api ruff check app/ tests/
docker-compose exec api ruff format app/ tests/

# Type check with mypy
docker-compose exec api mypy app/
```

### Database Access

**From Host Machine (DBeaver, psql):**
```
Host: localhost | Port: 5435
Database: taskmanager_dev
Username: taskuser | Password: taskpass
```

**From Terminal:**
```bash
docker exec -it taskmanager-postgres-dev psql -U taskuser -d taskmanager_dev
```

**Port Mapping:**
- API: 8888 (host) → 8000 (container)
- PostgreSQL: 5435 (host) → 5432 (container)

### Database Migrations (Alembic)

Task Manager uses Alembic for database schema migrations. Migrations are version-controlled SQL changes applied incrementally.

**Run Migrations:**
```bash
# Apply all pending migrations to latest version
docker exec taskmanager-api-dev alembic upgrade head

# Apply one migration forward
docker exec taskmanager-api-dev alembic upgrade +1

# Apply to specific revision
docker exec taskmanager-api-dev alembic upgrade <revision_id>
```

**Rollback Migrations:**
```bash
# Rollback last migration
docker exec taskmanager-api-dev alembic downgrade -1

# Rollback to base (all migrations)
docker exec taskmanager-api-dev alembic downgrade base

# Rollback to specific revision
docker exec taskmanager-api-dev alembic downgrade <revision_id>
```

**Migration Information:**
```bash
# Show current migration version
docker exec taskmanager-api-dev alembic current

# View migration history
docker exec taskmanager-api-dev alembic history

# View history with details
docker exec taskmanager-api-dev alembic history --verbose
```

**Create New Migration:**
```bash
# Auto-generate migration from model changes
docker exec taskmanager-api-dev alembic revision --autogenerate -m "description"

# Create empty migration template
docker exec taskmanager-api-dev alembic revision -m "description"
```

**Migration Files:**
- Location: `alembic/versions/`
- Naming: `<revision>_<description>.py` (e.g., `3d76e0c7a711_create_service_api_keys_table.py`)
- Content: `upgrade()` and `downgrade()` functions with SQL operations

### Database Schema

#### service_api_keys Table (Story 2.1)

Stores Service API Keys for client authentication:

```sql
CREATE TABLE service_api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key_name VARCHAR(100) UNIQUE NOT NULL,  -- Client identifier
    api_key VARCHAR(255) UNIQUE NOT NULL,   -- Service key value
    active BOOLEAN DEFAULT true NOT NULL,   -- Enable/disable flag
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    expires_at TIMESTAMPTZ  -- NULL for non-expiring keys
);

-- Partial index for active key lookups (performance optimization)
CREATE INDEX idx_service_api_keys_active ON service_api_keys(api_key) WHERE active = true;
```

**Migration:**
```bash
docker exec taskmanager-api-dev alembic revision -m "create_service_api_keys_table"
docker exec taskmanager-api-dev alembic upgrade head
```

#### tasks Table (Story 3.1)

Core data model for task management with user-scoped access:

```sql
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,           -- External user ID from Cat House
    title VARCHAR(500) NOT NULL,
    description TEXT,                         -- Optional long-form description
    status VARCHAR(50) NOT NULL DEFAULT 'pending',  -- pending|in_progress|completed
    priority VARCHAR(50),                     -- low|medium|high|urgent (optional)
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,                 -- Set when status changes to completed
    due_date TIMESTAMPTZ                      -- Optional task deadline
);

-- Single-column index for user-scoped queries
CREATE INDEX idx_tasks_user_id ON tasks(user_id);

-- Composite index for filtered queries (e.g., list pending tasks for user)
CREATE INDEX idx_tasks_user_status ON tasks(user_id, status);
```

**Design Notes:**
- `user_id` is NOT a foreign key - Task Manager is decoupled from Cat House user database
- VARCHAR for enums instead of PostgreSQL ENUM type for flexibility
- TIMESTAMPTZ (timestamp with timezone) for all datetime columns (stores UTC internally)
- Composite index `(user_id, status)` optimizes most common query pattern
- `gen_random_uuid()` is PostgreSQL 13+ built-in (no extension required)

**Migration Workflow:**
```bash
# Create migration
docker exec taskmanager-api-dev alembic revision -m "create_tasks_table"

# Review generated SQL in alembic/versions/<revision>_create_tasks_table.py

# Test rollback capability
docker exec taskmanager-api-dev alembic upgrade head
docker exec taskmanager-api-dev alembic downgrade -1  # Verify table drops cleanly
docker exec taskmanager-api-dev alembic upgrade head  # Re-apply

# Commit migration to version control
git add alembic/versions/<revision>_create_tasks_table.py
git commit -m "feat: add tasks table migration"
```

**Query Performance:**
- `SELECT * FROM tasks WHERE user_id = 'user_123'` - Uses `idx_tasks_user_id`
- `SELECT * FROM tasks WHERE user_id = 'user_123' AND status = 'pending'` - Uses `idx_tasks_user_status` (optimal)
- Composite index `(user_id, status)` supports both queries efficiently via leftmost prefix rule

### Authentication Headers

Task Manager uses **Service API Key authentication** (not JWT). Client applications authenticate by providing a service key in the `X-Service-Key` header.

**Authentication Model:**
- **Task Manager:** Validates service key from `service_api_keys` table
- **Cat House:** Validates user JWT and provides `user_id` in command payload
- **Flow:** User → Cat House (JWT) → Task Manager (Service Key + user_id)

**Header Format:**
```http
X-Service-Key: sk_dev_test_key_12345678901234567890123456789012
```

**Example API Request:**
```bash
curl -X POST http://localhost:8888/execute \
  -H "Content-Type: application/json" \
  -H "X-Service-Key: sk_dev_test_key_12345678901234567890123456789012" \
  -d '{
    "action": "create-task",
    "user_id": "user_123",
    "payload": {
      "title": "Buy cat food",
      "description": "Get salmon flavor"
    }
  }'
```

**Development Test Key:**
```
Key Name: cat-house-dev
X-Service-Key: sk_dev_test_key_12345678901234567890123456789012
```
This key is seeded in development database (Story 2.1) for testing.

**Service Key Management:**
- **Create Keys:** `/admin/service-keys` endpoint (Story 2.2, requires ADMIN_API_KEY)
- **Stored:** `service_api_keys` table in PostgreSQL
- **Validated:** `app/auth.py` - `validate_service_key()` dependency
- **Usage:** Apply to endpoints via FastAPI `Depends(validate_service_key)`

### Admin Endpoints

Task Manager provides admin endpoints for service API key management. These endpoints are protected by the `X-Admin-Key` header and should only be accessed by authorized administrators.

**Security Notes:**
- Admin endpoints should NEVER be exposed to public internet in production
- Use VPN, AWS Security Groups, or IP whitelisting
- Rotate ADMIN_API_KEY regularly
- Store production ADMIN_API_KEY in AWS Secrets Manager

#### Create Service Key

**POST /admin/service-keys**

Creates a new service API key for client application authentication.

**Headers:**
```http
X-Admin-Key: your-admin-key
Content-Type: application/json
```

**Request Body:**
```json
{
  "key_name": "cat-house-prod",
  "environment": "prod"
}
```

**Response (201 Created):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "key_name": "cat-house-prod",
  "service_key": "sk_prod_a1b2c3d4e5f67890123456789abcdef01234567890123456789abcdef012345",
  "created_at": "2025-11-12T10:30:00Z"
}
```

**Important:** The `service_key` is only returned in the creation response. Store it securely immediately - it cannot be retrieved later.

**Example (curl):**
```bash
curl -X POST http://localhost:8888/admin/service-keys \
  -H "X-Admin-Key: dev-admin-key-replace-in-production" \
  -H "Content-Type: application/json" \
  -d '{
    "key_name": "mobile-app-ios",
    "environment": "prod"
  }'
```

**Error Responses:**
- `400 Bad Request` - Key name already exists
- `401 Unauthorized` - Missing or invalid X-Admin-Key
- `422 Unprocessable Entity` - Invalid request body (validation error)

#### Rotate Service Key

**POST /admin/rotate-key**

Rotates an existing service API key with zero-downtime grace period. The old key continues working for 7 days to allow client migration.

**Headers:**
```http
X-Admin-Key: your-admin-key
Content-Type: application/json
```

**Request Body:**
```json
{
  "key_name": "cat-house-prod"
}
```

**Response (200 OK):**
```json
{
  "new_key": "sk_prod_f1e2d3c4b5a67890123456789fedcba09876543210fedcba0987654321fedcb",
  "old_key_expires_at": "2025-11-19T10:30:00Z"
}
```

**Rotation Workflow:**
1. Call `/admin/rotate-key` endpoint
2. Receive `new_key` and `old_key_expires_at` in response
3. Update client application configuration with `new_key`
4. Deploy updated client application
5. Old key continues working until `old_key_expires_at` (7 day grace period)
6. After grace period, old key automatically expires

**Example (curl):**
```bash
curl -X POST http://localhost:8888/admin/rotate-key \
  -H "X-Admin-Key: dev-admin-key-replace-in-production" \
  -H "Content-Type: application/json" \
  -d '{
    "key_name": "mobile-app-ios"
  }'
```

**Error Responses:**
- `404 Not Found` - Key name not found or no active key
- `401 Unauthorized` - Missing or invalid X-Admin-Key
- `422 Unprocessable Entity` - Invalid request body (validation error)

**Grace Period Details:**
- Duration: 7 days from rotation timestamp
- Both keys work: Old and new keys both authenticate successfully
- Zero downtime: Client can migrate without service interruption
- Automatic expiration: Old key stops working after `old_key_expires_at`


## Testing

**Test Structure:**
- `tests/unit/` - Business logic in isolation
- `tests/integration/` - API endpoints with database

**Coverage Goals:**
- Overall: ≥80%
- Critical paths: ≥95% (authentication, command handlers)

**Running Tests:**
See [Running Tests](#running-tests) section for commands.

## Code Quality Standards

**Configuration:** `pyproject.toml`
- **Ruff:** Line length 100, Python 3.12, comprehensive rules
- **Mypy:** Strict mode, type hints required

**Running Checks:**
See [Code Quality Checks](#code-quality-checks) section for commands.

## API Documentation

**Interactive Documentation:**
- **Swagger UI:** http://localhost:8888/docs - Interactive testing
- **ReDoc:** http://localhost:8888/redoc - Clean documentation
- **OpenAPI JSON:** http://localhost:8888/openapi.json - Raw specification
- **Usage Guide:** `docs/api-usage-guide.md` - Integration examples

### Command Pattern Architecture

Task Manager implements the **Universal Command Pattern** with a single endpoint (`POST /execute`) for all task operations. This design provides consistency, extensibility, and simplified integration with Cat House Platform.

#### POST /execute Endpoint

**URL:** `POST /execute`

**Authentication:** `X-Service-Key` header (required)

**Request Body:** `CommandRequest` schema

```json
{
  "action": "create-task",
  "user_id": "user_123",
  "payload": {
    "title": "Buy milk",
    "priority": "high"
  }
}
```

**Response Body:** `CommandResponse` schema

```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "user_123",
    "title": "Buy milk",
    "status": "pending",
    "priority": "high",
    "created_at": "2025-11-12T10:30:00Z"
  },
  "error": null,
  "timestamp": "2025-11-12T10:30:15Z"
}
```

#### Available Actions

##### create-task

**Purpose:** Create a new task for user

**Payload Schema:**
```json
{
  "title": "string (required, max 500 chars)",
  "description": "string (optional)",
  "status": "pending|in_progress|completed (optional, default: pending)",
  "priority": "low|medium|high|urgent (optional)",
  "due_date": "ISO 8601 datetime (optional)"
}
```

**Response:** Created task object with generated `id`, `created_at`, and user_id

**Example:**
```bash
curl -X POST http://localhost:8888/execute \
  -H "X-Service-Key: sk_dev_test_key_..." \
  -H "Content-Type: application/json" \
  -d '{
    "action": "create-task",
    "user_id": "user_123",
    "payload": {
      "title": "Buy cat food",
      "description": "Salmon flavor, 2kg bag",
      "priority": "high",
      "due_date": "2025-11-20T10:00:00Z"
    }
  }'
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "user_123",
    "title": "Buy cat food",
    "description": "Salmon flavor, 2kg bag",
    "status": "pending",
    "priority": "high",
    "created_at": "2025-11-12T10:30:00Z",
    "completed_at": null,
    "due_date": "2025-11-20T10:00:00Z"
  },
  "error": null,
  "timestamp": "2025-11-12T10:30:15Z"
}
```

**Validation Rules:**
- `title` is required (cannot be empty)
- `status` must match regex: `^(pending|in_progress|completed)$`
- `priority` must match regex: `^(low|medium|high|urgent)$`
- Invalid values return 400 with Pydantic validation error details

##### list-tasks

**Purpose:** List all tasks for user with optional status filter

**Payload Schema:**
```json
{
  "status": "pending|in_progress|completed (optional filter)"
}
```

**Response:** Array of task objects with count

**Example (no filter):**
```bash
curl -X POST http://localhost:8888/execute \
  -H "X-Service-Key: sk_dev_test_key_..." \
  -H "Content-Type: application/json" \
  -d '{
    "action": "list-tasks",
    "user_id": "user_123",
    "payload": {}
  }'
```

**Example (with status filter):**
```bash
curl -X POST http://localhost:8888/execute \
  -H "X-Service-Key: sk_dev_test_key_..." \
  -H "Content-Type: application/json" \
  -d '{
    "action": "list-tasks",
    "user_id": "user_123",
    "payload": {
      "status": "pending"
    }
  }'
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "tasks": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "user_id": "user_123",
        "title": "Buy cat food",
        "description": "Salmon flavor, 2kg bag",
        "status": "pending",
        "priority": "high",
        "created_at": "2025-11-12T10:30:00Z",
        "completed_at": null,
        "due_date": "2025-11-20T10:00:00Z"
      },
      {
        "id": "660e8400-e29b-41d4-a716-446655440001",
        "user_id": "user_123",
        "title": "Clean litter box",
        "description": null,
        "status": "pending",
        "priority": "medium",
        "created_at": "2025-11-12T09:00:00Z",
        "completed_at": null,
        "due_date": null
      }
    ],
    "count": 2
  },
  "error": null,
  "timestamp": "2025-11-12T10:30:15Z"
}
```

**Query Behavior:**
- Results ordered by `created_at DESC` (most recent first)
- Tasks scoped to `user_id` (users can only see their own tasks)
- Empty result: `{"tasks": [], "count": 0}`
- Status filter uses composite index `(user_id, status)` for optimal performance

##### get-task

**Purpose:** Retrieve a single task by ID

**Payload Schema:**
```json
{
  "task_id": "UUID (required)"
}
```

**Response:** Complete task object or 404 error

**Example:**
```bash
curl -X POST http://localhost:8888/execute \
  -H "X-Service-Key: sk_dev_test_key_..." \
  -H "Content-Type: application/json" \
  -d '{
    "action": "get-task",
    "user_id": "user_123",
    "payload": {
      "task_id": "550e8400-e29b-41d4-a716-446655440000"
    }
  }'
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "user_123",
    "title": "Buy cat food",
    "description": "Salmon flavor, 2kg bag",
    "status": "pending",
    "priority": "high",
    "created_at": "2025-11-12T10:30:00Z",
    "completed_at": null,
    "due_date": "2025-11-20T10:00:00Z"
  },
  "error": null,
  "timestamp": "2025-11-12T10:30:15Z"
}
```

**Error Responses:**
- `400`: Missing or invalid UUID format for task_id
- `404`: Task not found

**Security Note:** No user ownership check (trusts Cat House Platform authorization)

##### update-task

**Purpose:** Update task fields (partial update supported)

**Payload Schema:**
```json
{
  "task_id": "UUID (required)",
  "title": "string (optional, max 500 chars)",
  "description": "string (optional)",
  "status": "pending|in_progress|completed (optional)",
  "priority": "low|medium|high|urgent (optional)",
  "due_date": "ISO 8601 datetime (optional)"
}
```

**Special Behavior:**
- **Partial Updates:** Only provided fields are updated, others remain unchanged
- **Automatic completed_at Management:**
  - Status = `"completed"` → Sets `completed_at = NOW()`
  - Status = any other value → Sets `completed_at = NULL`
  - Status not in payload → Leaves `completed_at` unchanged

**Response:** Updated task object

**Example (partial update - title only):**
```bash
curl -X POST http://localhost:8888/execute \
  -H "X-Service-Key: sk_dev_test_key_..." \
  -H "Content-Type: application/json" \
  -d '{
    "action": "update-task",
    "user_id": "user_123",
    "payload": {
      "task_id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Buy cat food - Updated"
    }
  }'
```

**Example (status completion):**
```bash
curl -X POST http://localhost:8888/execute \
  -H "X-Service-Key: sk_dev_test_key_..." \
  -H "Content-Type: application/json" \
  -d '{
    "action": "update-task",
    "user_id": "user_123",
    "payload": {
      "task_id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "completed"
    }
  }'
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "user_123",
    "title": "Buy cat food",
    "description": "Salmon flavor, 2kg bag",
    "status": "completed",
    "priority": "high",
    "created_at": "2025-11-12T10:30:00Z",
    "completed_at": "2025-11-12T15:45:00Z",
    "due_date": "2025-11-20T10:00:00Z"
  },
  "error": null,
  "timestamp": "2025-11-12T15:45:30Z"
}
```

**Error Responses:**
- `400`: Missing/invalid task_id, no fields provided, or invalid field values
- `404`: Task not found

**Validation:** Uses TaskUpdate model with all optional fields for partial updates

##### delete-task

**Purpose:** Permanently delete a task

**Payload Schema:**
```json
{
  "task_id": "UUID (required)"
}
```

**Response:** Success confirmation with deleted task ID

**Example:**
```bash
curl -X POST http://localhost:8888/execute \
  -H "X-Service-Key: sk_dev_test_key_..." \
  -H "Content-Type: application/json" \
  -d '{
    "action": "delete-task",
    "user_id": "user_123",
    "payload": {
      "task_id": "550e8400-e29b-41d4-a716-446655440000"
    }
  }'
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "success": true,
    "deleted_id": "550e8400-e29b-41d4-a716-446655440000"
  },
  "error": null,
  "timestamp": "2025-11-12T15:50:00Z"
}
```

**Error Responses:**
- `400`: Missing or invalid UUID format for task_id
- `404`: Task not found (already deleted or never existed)

**Operation:** Permanent deletion from database (not soft delete)

##### get-stats

**Purpose:** Retrieve task statistics for user (for Cat House Whiskers integration)

**Payload Schema:**
```json
{}
```
*Note: Empty payload - statistics are user-scoped (user_id is sufficient)*

**Response:** Statistics object with 6 metrics

**Example:**
```bash
curl -X POST http://localhost:8888/execute \
  -H "X-Service-Key: sk_dev_test_key_..." \
  -H "Content-Type: application/json" \
  -d '{
    "action": "get-stats",
    "user_id": "user_123",
    "payload": {}
  }'
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "total_tasks": 10,
    "pending_tasks": 3,
    "in_progress_tasks": 2,
    "completed_tasks": 5,
    "completion_rate": 50.0,
    "overdue_tasks": 2
  },
  "error": null,
  "timestamp": "2025-11-12T15:55:00Z"
}
```

**Response Fields:**
- `total_tasks`: Total task count for user
- `pending_tasks`: Count where status = 'pending'
- `in_progress_tasks`: Count where status = 'in_progress'
- `completed_tasks`: Count where status = 'completed'
- `completion_rate`: Percentage (0.0 to 100.0), rounded to 2 decimals
- `overdue_tasks`: Count where due_date < NOW() AND status != 'completed'

**Performance:** < 200ms for users with up to 1000 tasks

**Zero Tasks Edge Case:** User with no tasks returns all zeros:
```json
{
  "total_tasks": 0,
  "pending_tasks": 0,
  "in_progress_tasks": 0,
  "completed_tasks": 0,
  "completion_rate": 0.0,
  "overdue_tasks": 0
}
```

**Integration Note:** Statistics calculated in real-time (not cached) for MVP

**Error Responses:**
- `500`: Unexpected error during statistics calculation

#### Handler Registration

Handlers are registered in the `ACTION_HANDLERS` dictionary in `app/commands/router.py`:

```python
from app.commands.handlers.tasks import create_task_handler

ACTION_HANDLERS = {
    "create-task": create_task_handler,
    # More handlers added in Stories 3.3/3.4
}
```

**Handler Function Signature:**

```python
async def handler(user_id: str, payload: dict, db) -> dict:
    """
    Args:
        user_id: External user ID from Cat House (already authenticated)
        payload: Action-specific parameters (validated by handler)
        db: Database connection from pool (dependency injection)
    
    Returns:
        dict: Response data (will be wrapped in CommandResponse)
    
    Raises:
        HTTPException: For validation errors, not found, etc.
    """
    pass
```

#### Error Responses

| Status Code | Error | Description |
|-------------|-------|-------------|
| 401 | Invalid service key | Missing or invalid X-Service-Key header |
| 404 | Unknown action | Action not registered in ACTION_HANDLERS |
| 422 | Invalid request body | CommandRequest validation failed |
| 500 | Handler execution error | Wrapped in CommandResponse with error field |

#### Example Usage

**Create Task:**

```bash
curl -X POST http://localhost:8888/execute \
  -H "X-Service-Key: sk_dev_test_key_..." \
  -H "Content-Type: application/json" \
  -d '{
    "action": "create-task",
    "user_id": "user_123",
    "payload": {
      "title": "Buy milk",
      "priority": "high"
    }
  }'
```

**List Tasks:**

```bash
curl -X POST http://localhost:8888/execute \
  -H "X-Service-Key: sk_dev_test_key_..." \
  -H "Content-Type: application/json" \
  -d '{
    "action": "list-tasks",
    "user_id": "user_123",
    "payload": {
      "status": "pending"
    }
  }'
```

**Error Response (Unknown Action):**

```json
{
  "detail": "Unknown action: nonexistent-action"
}
```

### Key Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/execute` | POST | Command Pattern endpoint (all operations) |
| `/health` | GET | Health check |
| `/` | GET | API information |
| `/admin/service-keys` | POST | Create service API key (admin only) |
| `/admin/rotate-key` | POST | Rotate service API key (admin only) |

## Deployment

Production uses AWS ECS Fargate with Terraform. See Epic 5 stories for detailed guides.

## Contributing

### Code Style Guidelines

1. Type hints required on all functions
2. Pass ruff and mypy checks before committing
3. Write tests for new features and bug fixes

### Git Workflow & Commits

Follow [Conventional Commits](https://www.conventionalcommits.org/): `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`

```bash
git checkout -b feature/story-X.Y
# ... make changes and test ...
docker-compose exec api ruff check app/ tests/
docker-compose exec api mypy app/
docker-compose exec api pytest tests/
git commit -m "feat: add new feature"
git push origin feature/story-X.Y
```

## License

MIT License - See LICENSE file for details

## Support

For questions or issues:
- **GitHub Issues:** [Repository issues page]
- **Documentation:** See `docs/` directory for architecture and PRD
- **Epic Documentation:** See `docs/prd/epic-*.md` for feature roadmap
