# Database Setup Guide - Cat House Backend

## Overview

Cat House uses Neon PostgreSQL as the serverless database backend. This guide covers setup for all environments.

**Project Details:**
- **Project Name:** cat-house
- **Project ID:** royal-king-27503715
- **Region:** AWS São Paulo (sa-east-1)
- **Postgres Version:** 17

**Branches:**
- `production` - Main production database
- `staging` - Staging environment for testing
- `development` - Development branch for local testing
- `test` - CI/CD testing branch

## Quick Start

### Development (Neon by default)

1. **Note about local DB:**
   The `cat-house-backend/docker-compose.yml` does not include a local `db` service. Development connects to Neon by default. If you prefer local PostgreSQL, run your own container and adjust the URLs accordingly.

2. **Configure environment:**
   ```bash
   # From cat-house-backend
   cp auth-service/.env.example auth-service/.env
   cp catalog-service/.env.example catalog-service/.env
   cp installation-service/.env.example installation-service/.env
   cp proxy-service/.env.example proxy-service/.env
   ```

3. **Update .env files with Neon credentials:**
   - Runtime (pooler, async driver):
     ```
     DATABASE_URL=postgresql+asyncpg://user:pass@ep-xxx-pooler.region.aws.neon.tech/cathouse?sslmode=require
     ```
   - Migrations (direct, sync driver) — only `auth-service`:
     ```
     MIGRATION_DATABASE_URL=postgresql://user:pass@ep-xxx.region.aws.neon.tech/cathouse?sslmode=require
     ```
   Note: Services set `ssl="require"` via SQLAlchemy `connect_args`; including `?sslmode=require` in the URL is optional for runtime.

### Production (Neon PostgreSQL)

**Connection Strings for cat-house project:**

**Test Branch (for CI/CD):**
```
# Pooled (runtime with asyncpg)
postgresql+asyncpg://neondb_owner:npg_YkeJrUi0tf7E@ep-long-poetry-ach6uuxn-pooler.sa-east-1.aws.neon.tech/neondb?sslmode=require

# Direct (migrations with psycopg2)
postgresql://neondb_owner:npg_YkeJrUi0tf7E@ep-long-poetry-ach6uuxn.sa-east-1.aws.neon.tech/neondb?sslmode=require
```

**Staging Branch:**
```
# Pooled (runtime with asyncpg)
postgresql+asyncpg://neondb_owner:npg_YkeJrUi0tf7E@ep-withered-river-aci39v6t-pooler.sa-east-1.aws.neon.tech/neondb?sslmode=require

# Direct (migrations with psycopg2)
postgresql://neondb_owner:npg_YkeJrUi0tf7E@ep-withered-river-aci39v6t.sa-east-1.aws.neon.tech/neondb?sslmode=require
```

**Production Branch:**
```
# Pooled (runtime with asyncpg)
postgresql+asyncpg://neondb_owner:npg_YkeJrUi0tf7E@ep-jolly-art-accpsvnx-pooler.sa-east-1.aws.neon.tech/neondb?sslmode=require

# Direct (migrations with psycopg2)
postgresql://neondb_owner:npg_YkeJrUi0tf7E@ep-jolly-art-accpsvnx.sa-east-1.aws.neon.tech/neondb?sslmode=require
```

## Database Schema Setup

### Initialize Schema with Alembic

Migrations are centralized in `auth-service` and manage the schema for all services. Other services do not run Alembic.

Refer to `cat-house-backend/auth-service/MIGRATIONS.md` for commands and workflow, and see detailed configuration in `.bmad-core/neon-rules/python-sqlalchemy-neon.md`.

## Connection Pooling

Neon Free Tier: 10 connections max. Recommended allocation (implemented):
- Auth: pool_size=2, max_overflow=1 (max 3)
- Catalog: pool_size=2, max_overflow=1 (max 3)
- Installation: pool_size=2, max_overflow=1 (max 3)
- Proxy: pool_size=1, max_overflow=0 (max 1)

This totals 10 connections. See complete pooling guidance in the Neon best practices guide.

## Security Checklist

- [ ] Never commit .env files to git
- [ ] Use ?sslmode=require in production
- [ ] Store credentials in secrets manager
- [ ] Rotate passwords regularly
- [ ] Enable Neon IP allowlist (if available)

## Resources

- [Neon Documentation](https://neon.tech/docs)
- [Neon Best Practices Guide](.bmad-core/neon-rules/python-sqlalchemy-neon.md)
- [SQLAlchemy 2.0 Tutorial](https://docs.sqlalchemy.org/en/20/tutorial/index.html)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
