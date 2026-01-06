"""Import all models for auth-service Alembic migrations.

Each service manages its own migrations independently:
- auth-service: users table in auth schema
- catalog-service: cats, permissions tables in catalog schema
- installation-service: installations, installation_permissions tables in installation schema

This follows true microservice architecture where each service owns its database schema.
"""

# Import base classes
from .base import Base, BaseModel

# Import auth-service models
from .user import User

# Export all models
__all__ = [
    "Base",
    "BaseModel",
    "User",
]
