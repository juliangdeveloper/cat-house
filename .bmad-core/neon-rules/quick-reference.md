# Neon Best Practices - Quick Reference

## For: Cat House Backend Services

### Connection URLs

**Development (Local PostgreSQL):**
```bash
DATABASE_URL=postgresql+asyncpg://catuser:catpass@db:5432/cathouse?sslmode=disable
MIGRATION_DATABASE_URL=postgresql://catuser:catpass@db:5432/cathouse?sslmode=disable
```

**Production (Neon):**
```bash
DATABASE_URL=postgresql+asyncpg://user:pass@ep-xxx-pooler.neon.tech/cathouse?sslmode=require
MIGRATION_DATABASE_URL=postgresql://user:pass@ep-xxx.neon.tech/cathouse?sslmode=require
```

### Key Differences

| Aspect | Runtime (DATABASE_URL) | Migrations (MIGRATION_DATABASE_URL) |
|--------|----------------------|-------------------------------------|
| Driver | `postgresql+asyncpg://` | `postgresql://` |
| Endpoint | Pooler (`-pooler.neon.tech`) | Direct (no `-pooler`) |
| Purpose | Async application queries | Sync Alembic migrations |
| SSL | Required in prod | Required in prod |

### Connection Pool Settings

```python
# For 4 services sharing Neon Free (10 connections max)
pool_size=2              # Min connections per service
max_overflow=3           # Max total = 5 per service
pool_recycle=3600        # Recycle every hour
pool_pre_ping=True       # Health check before use
```

### Common Mistakes to Avoid

 Using asyncpg URL for Alembic  **Use sync postgresql://**
 Using direct endpoint for runtime  **Use pooler endpoint**  
 Missing sslmode=require in prod  **Always use SSL**
 Too many connections  **Monitor and tune pool_size**
 Committing .env files  **Add to .gitignore**

### Quick Commands

```bash
# Generate migration
alembic revision --autogenerate -m "add user table"

# Preview migration SQL
alembic upgrade head --sql

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Troubleshooting

**Error: "too many connections"**
 Reduce pool_size, use pooler endpoint

**Error: "SSL required"**
 Add `?sslmode=require` to URL

**Error: "asyncpg: invalid dsn"**
 Use `postgresql://` not `postgresql+asyncpg://` for Alembic

### Full Documentation

See complete guides:
- `.bmad-core/neon-rules/python-sqlalchemy-neon.md` (technical reference)
- `docs/cat-house/guides/database-setup.md` (setup guide)
- Story 1.2: `docs/cat-house/stories/1.2.database-schema-migrations.md`
