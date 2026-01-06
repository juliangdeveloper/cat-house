# Shared Database Architecture

## Overview

Cat House backend uses a **single shared Neon PostgreSQL database** (cathouse) accessed by all microservices. This simplifies deployment while maintaining logical service boundaries.

## Architecture Decision

### Single Database vs. Database per Service

**Chosen:** Single shared database

**Rationale:**
- **Consistency:** ACID transactions across all entities
- **Simplicity:** One connection string, one migration path
- **Foreign Keys:** Database-enforced referential integrity
- **Cost:** Single Neon project (free tier covers all services)
- **Development:** Easier local development and testing

**Trade-offs:**
- Services are coupled at database level
- Cannot independently scale database per service
- All services must coordinate on schema changes

## Service Boundaries

### Logical Ownership

| Service | Tables Owned | Access Pattern |
|---------|--------------|----------------|
| auth-service | users | Read/Write, Manages migrations |
| catalog-service | cats, permissions | Read/Write |
| installation-service | installations, installation_permissions | Read/Write |
| proxy-service | (none) | Read-only across all tables |

### Migration Management

**Multi-Service Architecture:** Each service manages its own schema migrations independently.

**Service-Specific Migrations:**

| Service | Schema | Alembic Config | Tables |
|---------|--------|----------------|--------|
| auth-service | auth | auth-service/alembic/ | users |
| catalog-service | catalog | catalog-service/alembic/ | cats, permissions |
| installation-service | installation | installation-service/alembic/ | installations, installation_permissions |

**Workflow:**
1. Developer creates/modifies models in appropriate service
2. Generate migration in that service: `cd <service> && alembic revision --autogenerate -m "description"`
3. Review and test migration
4. Apply migrations sequentially:
   - Local: Run `./scripts/init-local-db.ps1` or `./scripts/init-local-db.sh`
   - CI/CD: GitHub Actions runs all three migrations automatically
5. Each service sees its own schema immediately

**Migration Execution Order:** auth-service → catalog-service → installation-service

## Connection Configuration

### Neon Endpoints

**Pooler (Runtime):** For application connections
\\\
postgresql+asyncpg://user:pass@ep-xxx-pooler.region.aws.neon.tech/cathouse?sslmode=require
\\\

**Direct (Migrations):** For Alembic migrations only
\\\
postgresql://user:pass@ep-xxx.region.aws.neon.tech/cathouse?sslmode=require
\\\

### Connection Pooling

**Neon Free Tier Limit:** 10 concurrent connections

**Allocation:**
- auth-service: pool_size=2, max_overflow=1  max 3 connections
- catalog-service: pool_size=2, max_overflow=1  max 3 connections
- installation-service: pool_size=2, max_overflow=1  max 3 connections
- proxy-service: pool_size=1, max_overflow=0  max 1 connection
- **Total: 10 connections**

**Configuration in each service:**
\\\python
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine(
    settings.database_url,
    pool_size=2,              # Adjust per service
    max_overflow=1,           # Adjust per service
    pool_recycle=3600,        # Recycle before scale-to-zero
    pool_pre_ping=True,       # REQUIRED: Prevents SSL errors
    pool_timeout=30,
    echo=settings.debug,
    connect_args={
        \"server_settings\": {
            \"application_name\": \"cat-house-{service-name}\",
            \"jit\": \"off\",  # Faster cold starts
        },
        \"command_timeout\": 60,
    }
)
\\\

## Environment Variables

### Shared Configuration

All services use the **same DATABASE_URL** (pooler endpoint):

\\\.env
# Shared by all services
DATABASE_URL=postgresql+asyncpg://user:pass@ep-xxx-pooler.region.aws.neon.tech/cathouse?sslmode=require

# Auth service only (for migrations)
MIGRATION_DATABASE_URL=postgresql://user:pass@ep-xxx.region.aws.neon.tech/cathouse?sslmode=require
\\\

## Development Workflow

### Local Development

**No local PostgreSQL required.** All development uses Neon's development branch.

1. Set up .env with development branch connection string
2. Run migrations from auth-service
3. Start all services with Docker Compose
4. All services connect to Neon development branch

### Testing

**Use Neon branches for isolated testing:**
\\\python
# tests/conftest.py
@pytest.fixture(scope=\"session\")
async def test_db_url():
    # Create ephemeral test branch
    branch = create_branch(project_id, \"test-{uuid}\")
    yield branch.connection_url
    delete_branch(branch.id)
\\\

## Security

### Access Control

- All services use same database role with full access
- Application-level authorization enforces service boundaries
- Network security via Neon IP allowlist (if available)

### Credentials Management

- Development: .env files (gitignored)
- Production: AWS Secrets Manager or environment variables
- Never commit connection strings to git

## Monitoring

### Connection Tracking

Use Neon console to monitor:
- Active connections per service
- Query performance (pg_stat_statements)
- Connection pooling efficiency
- Scale-to-zero patterns

### Health Checks

Each service should implement:
\\\python
@router.get(\"/health/db\")
async def db_health(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text(\"SELECT 1\"))
        return {\"status\": \"healthy\"}
    except Exception as e:
        return {\"status\": \"unhealthy\", \"error\": str(e)}
\\\

## Troubleshooting

### Connection Issues

**\"SSL connection has been closed unexpectedly\"**
- Ensure pool_pre_ping=True in engine config
- Verify pool_recycle=3600 is set

**\"Too many connections\"**
- Check all services use allocated pool sizes
- Monitor Neon console for connection count
- Reduce pool_size if needed

**\"Password authentication failed\"**
- Verify DATABASE_URL in .env matches Neon credentials
- Check for special characters needing URL encoding

### Migration Issues

**\"Relation already exists\"**
- Ensure each service only manages its own schema
- Use `alembic stamp head` to mark current state in specific service
- Each service has its own Alembic version table in its schema

**"Migration failed in CI/CD"**
- Check GitHub Actions workflow logs for specific service failure
- Automatic rollback will execute if migration fails
- Slack notifications sent to #aws-alerts channel
- Verify all three services completed migrations successfully

## References

- [Neon Best Practices](.bmad-core/neon-rules/python-sqlalchemy-neon.md)
- [Database Schema](./docs/database-schema.md)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
