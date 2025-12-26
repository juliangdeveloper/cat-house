# Neon PostgreSQL Best Practices for Python/SQLAlchemy

## Connection Management

### Database URLs for Different Purposes

**Runtime Connection (asyncpg/psycopg3):**
```
postgresql+asyncpg://user:pass@project-pooler.neon.tech/dbname?sslmode=require
```

**Alembic Migrations (psycopg2):**
```
postgresql://user:pass@project.neon.tech/dbname?sslmode=require
```

Key differences:
- Runtime uses **pooler endpoint** (-pooler suffix) for connection pooling
- Migrations use **direct endpoint** to avoid pooler conflicts
- Runtime uses async driver (asyncpg), migrations use sync driver (psycopg2)

### Connection Pooling Best Practices

For SQLAlchemy with Neon:

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

engine = create_async_engine(
    settings.database_url,
    pool_size=5,              # Min connections (Neon Free: 10 total)
    max_overflow=5,           # Additional connections when needed
    pool_timeout=30,          # Wait time for connection
    pool_recycle=3600,        # Recycle connections every hour
    pool_pre_ping=True,       # Verify connection health
    echo=settings.debug       # Log SQL in debug mode
)

AsyncSessionLocal = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)
```

**Neon Free Tier Limits:**
- 10 concurrent connections max
- Keep pool_size + max_overflow  10
- Use pooler endpoint to share connections across services

## Migration Patterns

### Alembic Configuration for Neon

**alembic/env.py:**
```python
from app.config import settings
from app.models import Base

# Use migration URL or fall back to main URL
database_url = settings.migration_database_url or settings.database_url

# Convert asyncpg URL to sync for Alembic
if database_url.startswith('postgresql+asyncpg://'):
    database_url = database_url.replace('postgresql+asyncpg://', 'postgresql://')

config.set_main_option('sqlalchemy.url', database_url)
target_metadata = Base.metadata
```

### Migration Commands

```bash
# Generate migration from model changes
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one version
alembic downgrade -1

# View history
alembic history --verbose
```

### Safe Migration Patterns

**Adding nullable columns (safe):**
```python
op.add_column('users', sa.Column('phone', sa.String(20), nullable=True))
```

**Adding NOT NULL columns (requires data migration):**
```python
# Step 1: Add as nullable
op.add_column('users', sa.Column('status', sa.String(20), nullable=True))

# Step 2: Populate data
op.execute(\"UPDATE users SET status = 'active' WHERE status IS NULL\")

# Step 3: Make NOT NULL
op.alter_column('users', 'status', nullable=False)
```

**Creating indexes concurrently (no table lock):**
```python
from alembic import op
op.create_index(
    'ix_users_email', 
    'users', 
    ['email'], 
    unique=True,
    postgresql_concurrently=True
)
```

## Environment Configuration

### Settings Class Pattern

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )
    
    # Database (required)
    database_url: str
    migration_database_url: str | None = None
    
    # App config
    environment: str = 'development'
    debug: bool = False
    
    @field_validator('database_url')
    @classmethod
    def validate_db_url(cls, v: str) -> str:
        if not v.startswith(('postgresql://', 'postgresql+asyncpg://')):
            raise ValueError('Invalid PostgreSQL URL')
        return v

settings = Settings()
```

### .env.example Template

```bash
# Development (local PostgreSQL)
DATABASE_URL=postgresql+asyncpg://catuser:catpass@localhost:5432/cathouse_dev?sslmode=disable
MIGRATION_DATABASE_URL=postgresql://catuser:catpass@localhost:5432/cathouse_dev?sslmode=disable

# Production (Neon)
# DATABASE_URL=postgresql+asyncpg://user:pass@project-pooler.neon.tech/cathouse?sslmode=require
# MIGRATION_DATABASE_URL=postgresql://user:pass@project.neon.tech/cathouse?sslmode=require
```

## Testing with Ephemeral Databases

### Using Neon Branches for Testing

Neon allows creating database branches for isolated testing:

```python
# tests/conftest.py
import pytest
import asyncpg
import os

@pytest.fixture(scope='session')
async def test_database_url():
    \"\"\"Create ephemeral test database using Neon branch\"\"\"
    # In CI/CD, use Neon API to create branch
    # Or use local PostgreSQL for faster tests
    base_url = os.getenv('TEST_DATABASE_URL')
    return base_url

@pytest.fixture
async def db_connection(test_database_url):
    \"\"\"Provide clean database connection for each test\"\"\"
    conn = await asyncpg.connect(test_database_url)
    
    # Run migrations
    # alembic upgrade head
    
    yield conn
    
    # Cleanup
    await conn.close()
```

## Security Best Practices

### Never Commit Credentials

```gitignore
# .gitignore
.env
.env.dev
.env.local
.env.production
*.pem
*.key
```

### Use Environment-Specific Configs

**Development:**
- Local PostgreSQL or Neon Free tier
- sslmode=disable OK for localhost
- Debug logging enabled

**Production:**
- Neon pooler endpoint
- sslmode=require MANDATORY
- INFO level logging
- Secrets in AWS Secrets Manager / HashiCorp Vault

## Performance Optimization

### Indexes

```python
# In SQLAlchemy models
class User(Base):
    __tablename__ = 'users'
    
    email = Column(String(255), unique=True, index=True)  # Single column index
    
    __table_args__ = (
        Index('ix_user_role_active', 'role', 'is_active'),  # Composite index
    )
```

### Query Optimization

```python
# Use select() instead of Query for SQLAlchemy 2.0
from sqlalchemy import select

async def get_active_users(session: AsyncSession):
    stmt = select(User).where(
        User.is_active == True
    ).options(
        selectinload(User.installations)  # Eager load relationships
    )
    result = await session.execute(stmt)
    return result.scalars().all()
```

## Troubleshooting

### Common Connection Errors

**Error: \"too many connections\"**
- Reduce pool_size + max_overflow
- Use pooler endpoint (-pooler)
- Check for connection leaks

**Error: \"SSL connection required\"**
- Add ?sslmode=require to URL
- Neon requires SSL in production

**Error: \"password authentication failed\"**
- Verify credentials in Neon Console
- Check URL encoding of special characters

### Migration Conflicts

**Error: \"relation already exists\"**
```bash
# Mark current state without running migrations
alembic stamp head

# Or start fresh (DANGER: drops all tables)
alembic downgrade base
alembic upgrade head
```

## References

- [Neon Documentation](https://neon.tech/docs)
- [SQLAlchemy 2.0 Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [asyncpg Performance](https://github.com/MagicStack/asyncpg)
