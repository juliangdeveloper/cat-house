"""Models for installation-service.

This module exports all models owned by installation-service.
All models use the shared database defined in base.py.
"""

from .base import Base, BaseModel
from .installation import Installation
from .installation_permission import InstallationPermission

__all__ = ["Base", "BaseModel", "Installation", "InstallationPermission"]
