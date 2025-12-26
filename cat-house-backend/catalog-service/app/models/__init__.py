"""Models for catalog-service.

This module exports all models owned by catalog-service.
All models use the shared database defined in base.py.
"""
from .base import Base, BaseModel
from .cat import Cat
from .permission import Permission

__all__ = ["Base", "BaseModel", "Cat", "Permission"]
