"""
Task Manager API - Admin Router

Admin endpoints for service API key management.
Protected by X-Admin-Key header authentication.
"""

from datetime import datetime, timedelta, timezone

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import generate_service_key, validate_admin_key
from app.database import get_db
from app.models.admin import (
    ServiceKeyCreateRequest,
    ServiceKeyCreateResponse,
    ServiceKeyRotateRequest,
    ServiceKeyRotateResponse,
)

router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)


@router.post(
    "/service-keys",
    response_model=ServiceKeyCreateResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(validate_admin_key)]
)
async def create_service_key(
    request: ServiceKeyCreateRequest,
    db: asyncpg.Connection = Depends(get_db)
):
    """
    Create new service API key for client application.
    
    Generates cryptographically secure service key with environment-specific prefix.
    Service keys authenticate client applications (Cat House, mobile apps) for data operations.
    
    Args:
        request: Service key creation parameters (key_name, environment)
        db: Database connection from pool
    
    Returns:
        ServiceKeyCreateResponse with generated key details
    
    Raises:
        HTTPException(400): If key_name already exists
        HTTPException(401): If X-Admin-Key header missing or invalid
    
    Security:
        - Requires valid X-Admin-Key header (validated by dependency)
        - Service key returned ONLY in creation response (store securely)
        - key_name must be unique (enforced by database constraint)
    
    Example:
        POST /admin/service-keys
        Headers: X-Admin-Key: your-admin-key
        Body: {"key_name": "cat-house-prod", "environment": "prod"}
        
        Response: {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "key_name": "cat-house-prod",
            "service_key": "sk_prod_a1b2c3...",
            "created_at": "2025-11-12T10:30:00Z"
        }
    """
    # Check if key_name already exists
    existing = await db.fetchrow(
        "SELECT id FROM service_api_keys WHERE key_name = $1",
        request.key_name
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Service key with name '{request.key_name}' already exists"
        )

    # Generate service key
    service_key = generate_service_key(request.environment)

    # Insert into database
    result = await db.fetchrow("""
        INSERT INTO service_api_keys (key_name, api_key, active, created_at)
        VALUES ($1, $2, true, NOW())
        RETURNING id, key_name, api_key, created_at
    """, request.key_name, service_key)

    return ServiceKeyCreateResponse(
        id=result['id'],
        key_name=result['key_name'],
        service_key=result['api_key'],
        created_at=result['created_at']
    )


@router.post(
    "/rotate-key",
    response_model=ServiceKeyRotateResponse,
    dependencies=[Depends(validate_admin_key)]
)
async def rotate_service_key(
    request: ServiceKeyRotateRequest,
    db: asyncpg.Connection = Depends(get_db)
):
    """
    Rotate existing service API key with zero-downtime grace period.
    
    Implements rotation workflow:
    1. Generate new key with same environment as old key
    2. Mark old key with expires_at = NOW() + 7 days (grace period)
    3. Insert new key (no expiration)
    4. Both keys validate during grace period (zero downtime)
    5. After 7 days, old key stops working
    
    Args:
        request: Service key rotation parameters (key_name)
        db: Database connection from pool
    
    Returns:
        ServiceKeyRotateResponse with new key and old key expiration
    
    Raises:
        HTTPException(404): If key_name not found or no active key
        HTTPException(401): If X-Admin-Key header missing or invalid
    
    Security:
        - Requires valid X-Admin-Key header (validated by dependency)
        - 7 day grace period allows client migration without downtime
        - Old key automatically expires after grace period
    
    Example:
        POST /admin/rotate-key
        Headers: X-Admin-Key: your-admin-key
        Body: {"key_name": "cat-house-prod"}
        
        Response: {
            "new_key": "sk_prod_new123...",
            "old_key_expires_at": "2025-11-19T10:30:00Z"
        }
    
    Workflow:
        1. Client receives new_key in response
        2. Client updates configuration with new_key
        3. Old key continues working for 7 days
        4. After 7 days, old key expires (expires_at < NOW())
    """
    # Fetch current active key
    result = await db.fetchrow("""
        SELECT api_key FROM service_api_keys
        WHERE key_name = $1 AND active = true
        ORDER BY created_at DESC LIMIT 1
    """, request.key_name)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Active service key '{request.key_name}' not found"
        )

    old_key = result['api_key']

    # Extract environment from old key (sk_prod_xxx or sk_dev_xxx)
    environment = old_key.split('_')[1]

    # Generate new key
    new_key = generate_service_key(environment)

    # Calculate grace period expiration (UTC timezone-aware)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    # Mark old key for expiration
    await db.execute("""
        UPDATE service_api_keys
        SET expires_at = $1
        WHERE api_key = $2
    """, expires_at, old_key)

    # Insert new key (no expiration)
    await db.execute("""
        INSERT INTO service_api_keys (key_name, api_key, active, created_at)
        VALUES ($1, $2, true, NOW())
    """, request.key_name, new_key)

    return ServiceKeyRotateResponse(
        new_key=new_key,
        old_key_expires_at=expires_at
    )
