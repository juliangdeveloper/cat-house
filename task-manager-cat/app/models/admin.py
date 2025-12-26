"""
Task Manager API - Admin Models

Pydantic request/response models for admin endpoints.
Provides type safety and validation for service key management operations.
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ServiceKeyCreateRequest(BaseModel):
    """
    Request model for creating a new service API key.
    
    Attributes:
        key_name: Unique identifier for the service key (alphanumeric + hyphens)
        environment: Key environment (affects prefix: sk_prod_ or sk_dev_)
    """

    key_name: str = Field(
        min_length=3,
        max_length=100,
        pattern=r"^[a-z0-9-]+$",
        description="Unique identifier for the service key (alphanumeric + hyphens)",
        examples=["cat-house-prod", "mobile-app-ios", "web-app-staging"]
    )
    environment: Literal["prod", "dev"] = Field(
        description="Key environment (affects prefix)"
    )


class ServiceKeyCreateResponse(BaseModel):
    """
    Response model for service key creation.
    
    Attributes:
        id: Database UUID for the service key record
        key_name: Unique identifier for the service key
        service_key: Generated service API key (store securely, only shown once)
        created_at: Timestamp when key was created
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    key_name: str
    service_key: str = Field(
        description="Generated service API key (store securely, only shown once)"
    )
    created_at: datetime


class ServiceKeyRotateRequest(BaseModel):
    """
    Request model for rotating an existing service API key.
    
    Attributes:
        key_name: Identifier of the service key to rotate
    """

    key_name: str = Field(
        min_length=3,
        max_length=100,
        pattern=r"^[a-z0-9-]+$",
        description="Unique identifier for the service key to rotate",
        examples=["cat-house-prod", "mobile-app-ios"]
    )


class ServiceKeyRotateResponse(BaseModel):
    """
    Response model for service key rotation.
    
    Attributes:
        new_key: Newly generated service API key
        old_key_expires_at: Timestamp when old key will expire (7 day grace period)
    """

    new_key: str = Field(
        description="Newly generated service API key (replaces old key)"
    )
    old_key_expires_at: datetime = Field(
        description="Timestamp when old key expires (7 day grace period for migration)"
    )
