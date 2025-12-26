"""Models for auth-service.

This module exports all models owned by auth-service.
All models use the shared database defined in base.py.
"""
from .base import Base, BaseModel
from .user import User

__all__ = ["Base", "BaseModel", "User"]
