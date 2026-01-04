# Cat House Backend Services

Microservices architecture for the Cat House platform - a marketplace for gamification integrations.

**CI/CD Status:** ? Consolidated pipeline configured (Dec 30, 2025)

## Architecture Overview

The Cat House backend consists of four containerized FastAPI microservices:

```
+
                    API Gateway                          
              https://chapi.gamificator.click            

                           
        
                                            
    
 Auth Service      Catalog        Installation  
  Port: 8005       Service          Service     
    Port: 8002     Port: 8003    
                     
                          
                   
                      Proxy     
                     Service    
                     Port: 8004 
                   
```

## Services

### Auth Service (Port 8005)
- User authentication and authorization
- JWT token generation and validation
- Role-based access control

### Catalog Service (Port 8002)
- Cat discovery and browsing
- Metadata and asset management
- Reviews and ratings
- Integration with S3 for assets

### Installation Service (Port 8003)
- Cat installation management
- Instance lifecycle
- Permission management
- Encrypted credential storage

### Proxy Service (Port 8004)
- Request mediation to external cat services
- Permission validation
- Audit logging
- Rate limiting

## Technology Stack

- **Language:** Python 3.11+
- **Framework:** FastAPI 0.104+
- **Database:** Neon PostgreSQL (Serverless)
- **ORM:** SQLAlchemy 2.0+ (Async)
- **Migrations:** Alembic 1.13+ (Auth Service Only)
- **Container:** Docker
- **Logging:** Loguru
- **Settings:** Pydantic Settings

## Database Architecture

**Shared Database Model:**
- All services connect to a **single Neon PostgreSQL database** (`neondb`)
- Simplified deployment with one connection string
- Database-enforced foreign key constraints
- ACID transactions across all entities

**Service Ownership (Logical):**
- **Auth Service:** Manages migrations, owns `users` table
- **Catalog Service:** Owns `cats` and `permissions` tables
- **Installation Service:** Owns `installations` and `installation_permissions` tables
- **Proxy Service:** Read-only access for validation

**Migration Management:**
- **ONLY auth-service manages migrations** (single source of truth)
- All models imported into `auth-service/alembic/env.py`
- See [auth-service/MIGRATIONS.md](auth-service/MIGRATIONS.md) for details
- See [docs/database-schema.md](docs/database-schema.md) for schema documentation

**Connection Pooling:**
```
Total: 10 connections (Neon Free Tier)
+-- Auth Service:         3 connections (pool_size=2, max_overflow=1)
+-- Catalog Service:      3 connections (pool_size=2, max_overflow=1)
+-- Installation Service: 3 connections (pool_size=2, max_overflow=1)
+-- Proxy Service:        1 connection  (pool_size=1, max_overflow=0)
```

## Database Migrations

**Centralized Migration Management:**
- **ONLY auth-service** manages database migrations
- All models from all services imported into `auth-service/alembic/env.py`
- Single source of truth for schema changes

### Quick Start

```bash
# Navigate to auth-service
cd auth-service

# Generate new migration after model changes
alembic revision --autogenerate -m "add user status field"

# Apply migrations
alembic upgrade head

# Check migration history
alembic history --verbose
```

### Production Migration Workflow (Using Neon MCP Tools)

**Safe Migration Process:**

1. **Generate Migration Locally:**
   ```bash
   cd auth-service
   alembic revision --autogenerate -m "description"
   ```

2. **Generate SQL Preview:**
   ```bash
   alembic upgrade head --sql > migration.sql
   ```

3. **Test in Temporary Branch (MCP):**
   ```typescript
   // Use Neon MCP tool to create temporary test branch
   mcp_neondatabase__prepare_database_migration({
     projectId: "old-dew-33552653",
     databaseName: "neondb",
     migrationSql: "<content-of-migration.sql>"
   })
   // Returns: migration_id and temporary branch details
   ```

4. **Verify Schema in Test Branch:**
   ```typescript
   // Check table structure
   mcp_neondatabase__describe_table_schema({
     projectId: "old-dew-33552653",
     tableName: "users",
     databaseName: "neondb",
     branchId: "<temp-branch-id>"
   })
   ```

5. **Apply to Production (if successful):**
   ```typescript
   // Apply changes to main branch
   mcp_neondatabase__complete_database_migration({
     migrationId: "<migration-id>"
   })
   ```

6. **Or Apply Directly (for development):**
   ```bash
   cd auth-service
   alembic upgrade head
   ```

**Rollback Procedure:**

```bash
# Preview rollback SQL first
alembic downgrade <current>:<target> --sql > rollback.sql

# Test in temporary branch using MCP tools (same process as above)

# Apply rollback if needed
alembic downgrade -1
```

**Key Points:**
- Never run migrations directly on production without testing
- Use Neon branches to test migrations safely
- Always have a rollback plan
- Document complex migrations

**Full Documentation:**
- [auth-service/MIGRATIONS.md](auth-service/MIGRATIONS.md) - Complete migration guide
- [docs/database-schema.md](docs/database-schema.md) - Schema documentation

## API Versioning

All services follow the `/api/v1/` URL pattern for API endpoints.

## Local Development

### Prerequisites

- Docker Desktop (or Docker Engine + Docker Compose)
- Python 3.11+ (for local development without Docker)
- Git

### Quick Start with Docker Compose

**NOTE:** This setup uses Neon PostgreSQL (serverless). No local PostgreSQL container is required.

1. **Clone the repository**
   ```bash
   cd cat-house-backend
   ```

2. **Configure environment variables**
   ```bash
   # Copy .env.example to .env for each service
   cp auth-service/.env.example auth-service/.env
   cp catalog-service/.env.example catalog-service/.env
   cp installation-service/.env.example installation-service/.env
   cp proxy-service/.env.example proxy-service/.env
   ```
   
   Edit each `.env` file with your Neon connection strings.
   
   **Neon Project Details:**
   - Project: cat-house
   - Database: neondb
   - Connection strings provided in `.env.example`

3. **Run database migrations**
   ```bash
   cd auth-service
   pip install -r requirements.txt
   alembic upgrade head
   cd ..
   ```

4. **Start all services**
   ```bash
   docker-compose up -d
   ```

5. **Check service health**
   ```bash
   # Auth Service
   curl http://localhost:8005/api/v1/health
   
   # Catalog Service
   curl http://localhost:8002/api/v1/health
   
   # Installation Service
   curl http://localhost:8003/api/v1/health
   
   # Proxy Service
   curl http://localhost:8004/api/v1/health
   ```

4. **View logs**
   ```bash
   docker-compose logs -f [service-name]
   ```

5. **Stop all services**
   ```bash
   docker-compose down
   ```

### Development with Hot Reload

The docker-compose configuration mounts service code as volumes, enabling hot reload:

```bash
# Make changes to any service's code in ./[service-name]/app/
# The service will automatically reload
```

### Individual Service Development

Each service can be run independently. See individual service README files:

- [Auth Service README](./auth-service/README.md)
- [Catalog Service README](./catalog-service/README.md)
- [Installation Service README](./installation-service/README.md)
- [Proxy Service README](./proxy-service/README.md)

## Port Assignments

| Service      | Port | URL                              |
|--------------|------|----------------------------------|
| Auth         | 8005 | http://localhost:8005/api/v1/    |
| Catalog      | 8002 | http://localhost:8002/api/v1/    |
| Installation | 8003 | http://localhost:8003/api/v1/    |
| Proxy        | 8004 | http://localhost:8004/api/v1/    |
| PostgreSQL   | 5432 | postgresql://catuser:catpass@localhost:5432/cathouse |

## Inter-Service Communication

Services communicate via the internal Docker network `cathouse-network`. In production, this will be replaced by the API Gateway routing.

### Service Discovery

Services reference each other using container names:
- `http://auth-service:8005`
- `http://catalog-service:8002`
- `http://installation-service:8003`
- `http://proxy-service:8004`

## Database

All services share a single PostgreSQL database with separate schemas:

- `auth` schema - Auth Service tables
- `catalog` schema - Catalog Service tables
- `installation` schema - Installation Service tables
- `proxy` schema - Proxy Service tables

## API Documentation

When running in debug mode, each service exposes Swagger UI:

- Auth: http://localhost:8005/api/v1/docs
- Catalog: http://localhost:8002/api/v1/docs
- Installation: http://localhost:8003/api/v1/docs
- Proxy: http://localhost:8004/api/v1/docs

## Testing

### Unit Tests

Each service includes unit tests using pytest:

```bash
# Test a specific service
cd [service-name]
pip install -r requirements.txt
pytest tests/ -v

# Or using Docker
docker-compose run auth-service pytest tests/ -v
```

### Integration Tests

Docker Compose integration tests verify multi-service deployment:

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run integration tests (will start/stop Docker services)
pytest tests/test_docker_integration.py -v

# Note: Integration tests automatically start and stop Docker Compose
```

### Environment Variable Tests

Configuration loading is tested to ensure settings can be properly overridden:

```bash
# Auth service includes config tests
cd auth-service
pytest tests/test_config.py -v
```

## Project Structure

```
cat-house-backend/
 docker-compose.yml          # Orchestration for all services
 init-db.sql                 # Database initialization
 README.md                   # This file
 auth-service/
    app/
       main.py            # FastAPI app
       config.py          # Settings
       routers/           # API endpoints
       services/          # Business logic
       models/            # Data models
    tests/
    Dockerfile
    requirements.txt
    README.md
 catalog-service/           # Same structure
 installation-service/      # Same structure
 proxy-service/             # Same structure
```

## Environment Variables

Each service has an `.env.example` file. For local development, docker-compose.yml provides default values.

For production deployment, ensure all secrets are properly configured.

## Troubleshooting

### Services won't start
```bash
# Check Docker is running
docker info

# Rebuild containers
docker-compose up --build

# Check logs
docker-compose logs
```

### Database connection errors
```bash
# Ensure database is healthy
docker-compose ps

# Check database logs
docker-compose logs db
```

### Port already in use
```bash
# Find process using port (example for 8005)
netstat -ano | findstr :8005

# Stop conflicting service or change port in docker-compose.yml
```

## Production Deployment

These services are designed to be deployed on AWS ECS Fargate with:
- API Gateway for routing
- Neon Serverless PostgreSQL
- AWS S3 for assets
- CloudWatch for logging and monitoring
- AWS Chatbot for Slack notifications
- Secrets Manager for credentials

See [docs/monitoring/](docs/monitoring/) for monitoring and alerting setup.

## Contributing

1. Each service follows the same structure
2. Use structured logging with Loguru
3. All endpoints under `/api/v1/`
4. Include tests for new features
5. Update service README when adding endpoints

## License

Proprietary - Cat House Platform

---

**Maintained by:** Platform Engineering Team  
**Last Updated:** December 2025
#   D o c k e r   i m a g e s   b u i l d   t r i g g e r 
 
 
