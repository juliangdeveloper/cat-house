# Database Setup Guide - Cat House Backend

## Overview

Cat House uses Neon PostgreSQL as the serverless database backend. This guide covers setup for all environments.

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

1. **Create Neon Project:**
   - Sign up at https://neon.tech
   - Create project: "cat-house-prod"
   - Region: Select closest to your users
   - Note both connection strings (pooler + direct)

2. **Get Connection Strings:**
   
   **Pooler (for application runtime, async):**
   ```
   postgresql+asyncpg://user:pass@ep-xxx-pooler.region.aws.neon.tech/cathouse?sslmode=require
   ```
   
   **Direct (for migrations, sync):**
   ```
   postgresql://user:pass@ep-xxx.region.aws.neon.tech/cathouse?sslmode=require
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
