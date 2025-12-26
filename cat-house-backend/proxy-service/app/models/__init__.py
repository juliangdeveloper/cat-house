"""Models for proxy-service.

Proxy service has read-only access to all models.
It doesn't own any tables but imports all models for validation.
"""
from .base import Base, BaseModel

__all__ = ["Base", "BaseModel"]
