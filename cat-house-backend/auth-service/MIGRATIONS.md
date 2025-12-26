# Auth Service - Database Migrations

This service is the **ONLY** service that manages database migrations for the entire Cat House backend.

## Migration Responsibilities

**Centralized Migration Management:**
- Auth service contains the Alembic configuration
- All models from all services are imported into `alembic/env.py`
- Migrations are generated and applied only from this service
- Other services simply connect to the shared database

## Prerequisites

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with your Neon connection strings
   ```

## Migration Commands

### Generate New Migration

```bash
# Navigate to auth-service directory
cd auth-service

# Generate migration from model changes
alembic revision --autogenerate -m "description of changes"

# Review the generated migration in alembic/versions/
```

### Apply Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Apply up to a specific revision
alembic upgrade <revision_id>

# Apply one migration at a time
alembic upgrade +1
```

### Rollback Migrations

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to a specific revision
alembic downgrade <revision_id>

# Rollback all migrations
alembic downgrade base

# Preview rollback SQL (test before applying)
alembic downgrade <current>:<target> --sql
# Example: alembic downgrade cd0f2927ee5e:base --sql
```

**Testing Rollback Procedure:**

1. **Generate rollback SQL:**
   ```bash
   # From current revision to base
   alembic downgrade cd0f2927ee5e:base --sql > rollback.sql
   
   # Or rollback one step
   alembic current  # Get current revision
   alembic downgrade <current>:<previous> --sql > rollback.sql
   ```

2. **Test in temporary branch using MCP:**
   ```typescript
   // Create test branch
   mcp_neondatabase__create_branch({
     projectId: "<project-id>",
     branchName: "test-rollback"
   })
   
   // Apply rollback SQL
   mcp_neondatabase__run_sql({
     projectId: "<project-id>",
     branchId: "<test-branch-id>",
     sql: "<rollback-sql-content>"
   })
   
   // Verify schema
   mcp_neondatabase__get_database_tables({
     projectId: "<project-id>",
     branchId: "<test-branch-id>"
   })
   
   // Delete test branch after verification
   mcp_neondatabase__delete_branch({
     projectId: "<project-id>",
     branchId: "<test-branch-id>"
   })
   ```

3. **Apply rollback to main (if needed):**
   ```bash
   # Only after successful testing
   alembic downgrade -1
   ```

### View Migration History

```bash
# Show all migrations
alembic history --verbose

# Show current revision
alembic current

# Show pending migrations
alembic heads
```

## Safe Migration Workflow (Production)

**IMPORTANT:** Never run migrations directly on production. Use this workflow:

1. **Generate migration locally:**
   ```bash
   alembic revision --autogenerate -m "add user status field"
   ```

2. **Review the generated migration:**
   - Check `alembic/versions/<timestamp>_<slug>.py`
   - Ensure upgrade() and downgrade() are correct
   - Verify no data loss will occur

3. **Generate SQL preview:**
   ```bash
   alembic upgrade head --sql > migration.sql
   ```

4. **Test in development branch:**
   - Use Neon MCP tool `mcp_neondatabase__prepare_database_migration`
   - Creates temporary branch
   - Applies migration to test branch
   - Verify schema changes

5. **Apply to production:**
   - After successful testing
   - Use Neon MCP tool `mcp_neondatabase__complete_database_migration`
   - Applies changes to main branch

## Model Changes from Other Services

When models in other services change (catalog, installation, proxy):

1. **Developer updates model** in their service
2. **Navigate to auth-service:**
   ```bash
   cd auth-service
   ```

3. **Generate migration:**
   ```bash
   alembic revision --autogenerate -m "update cat model"
   ```
   
   Alembic will detect changes because `alembic/env.py` imports all models.

4. **Follow safe migration workflow** above

## Troubleshooting

### "Can't locate revision identified by..."

```bash
# Stamp the database with current state
alembic stamp head
```

### "Target database is not up to date"

```bash
# Check current revision
alembic current

# Apply pending migrations
alembic upgrade head
```

### "Multiple heads detected"

```bash
# Show all heads
alembic heads

# Merge heads
alembic merge -m "merge heads" <head1> <head2>
```

### Import Errors

If Alembic can't find models from other services:

1. Verify path setup in `alembic/env.py`
2. Ensure all services have models/__init__.py
3. Check Python path includes backend root

## Connection Strings

Auth service requires TWO database URLs:

**DATABASE_URL** (runtime, async, pooler):
```
postgresql+asyncpg://user:pass@ep-xxx-pooler.neon.tech/neondb?sslmode=require
```

**MIGRATION_DATABASE_URL** (migrations, sync, direct):
```
postgresql://user:pass@ep-xxx.neon.tech/neondb?sslmode=require
```

Key differences:
- Runtime uses `-pooler` endpoint
- Migrations use direct endpoint
- Runtime uses async driver (asyncpg)
- Migrations use sync driver (psycopg2)

## Best Practices

1. **Always review generated migrations** before applying
2. **Test migrations in development branch** first
3. **Write reversible migrations** (proper downgrade())
4. **Keep migrations atomic** (one logical change per migration)
5. **Document complex migrations** with comments
6. **Never edit applied migrations** (create new one instead)
7. **Backup before production migrations** (use Neon branching)

## Resources

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Neon Best Practices](../.bmad-core/neon-rules/python-sqlalchemy-neon.md)
- [Database Schema](../docs/database-schema.md)
- [Shared Database Architecture](../docs/shared-database-architecture.md)
