"""
Task Manager API - Authentication

Service API Key validation for client application authentication.
Implements dependency injection pattern for FastAPI endpoints.
"""

import secrets

import asyncpg
from fastapi import Depends, Header, HTTPException, status

from app.config import settings
from app.database import get_db


def generate_service_key(environment: str) -> str:
    """
    Generate cryptographically secure service API key.
    
    Uses Python's secrets module to generate 32 random bytes (256 bits entropy)
    suitable for security tokens. Keys are prefixed with environment identifier
    to distinguish production from development keys.
    
    Args:
        environment: Key environment ('prod' or 'dev')
    
    Returns:
        str: Service key in format 'sk_{environment}_{64_hex_chars}'
        
    Raises:
        ValueError: If environment is not 'prod' or 'dev'
    
    Examples:
        >>> key = generate_service_key('prod')
        >>> key.startswith('sk_prod_')
        True
        >>> len(key)
        72
        >>> key = generate_service_key('dev')
        >>> key.startswith('sk_dev_')
        True
        >>> generate_service_key('staging')  # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        ValueError: Invalid environment: staging. Must be 'prod' or 'dev'
    
    Security Notes:
        - 32 bytes = 256 bits entropy (AES-256 equivalent strength)
        - secrets.token_bytes() uses OS's cryptographically strong random source
        - Keys are industry-standard length (GitHub PAT, AWS Access Keys, Stripe)
    """
    if environment not in ('prod', 'dev'):
        raise ValueError(f"Invalid environment: {environment}. Must be 'prod' or 'dev'")

    random_bytes = secrets.token_bytes(32)
    hex_string = random_bytes.hex()
    return f"sk_{environment}_{hex_string}"


async def validate_admin_key(
    x_admin_key: str = Header(..., alias="X-Admin-Key")
) -> None:
    """
    Validate admin API key from X-Admin-Key header.
    
    Uses constant-time comparison to prevent timing attacks where attackers
    measure response time to guess keys character-by-character.
    
    Args:
        x_admin_key: Admin API key from X-Admin-Key header (extracted by FastAPI)
    
    Returns:
        None: Dependency used for authentication only (no return value needed)
    
    Raises:
        HTTPException(401): If admin key is missing or invalid
    
    Usage in endpoint:
        >>> from fastapi import Depends
        >>> from app.auth import validate_admin_key
        >>> 
        >>> @router.post("/admin/service-keys", dependencies=[Depends(validate_admin_key)])
        >>> async def create_service_key(...):
        ...     # Only executes if admin key is valid
        ...     pass
    
    Security Notes:
        - secrets.compare_digest() provides constant-time comparison
        - Prevents timing attacks (standard == comparison is vulnerable)
        - Admin key stored in environment variable (ADMIN_API_KEY)
        - Must be rotated periodically (manual process in MVP)
    """
    if not secrets.compare_digest(x_admin_key, settings.admin_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin key"
        )



async def validate_service_key(
    x_service_key: str = Header(..., alias="X-Service-Key"),
    db: asyncpg.Connection = Depends(get_db)
) -> str:
    """
    Validate Service API Key from X-Service-Key header.
    
    Checks that:
    - Service key exists in database
    - Service key is active (active = true)
    - Service key has not expired (expires_at IS NULL OR expires_at > NOW())
    
    Args:
        x_service_key: Service API key from X-Service-Key header (extracted by FastAPI)
        db: Database connection from pool (provided by get_db dependency)
    
    Returns:
        str: key_name of validated service key (for logging/monitoring)
    
    Raises:
        HTTPException(401): If service key is missing, invalid, inactive, or expired
    
    Usage in endpoint:
        >>> from fastapi import Depends
        >>> from app.auth import validate_service_key
        >>> 
        >>> @app.post("/execute")
        >>> async def execute_command(
        ...     command: CommandRequest,
        ...     key_name: str = Depends(validate_service_key)
        ... ):
        ...     # key_name is available if request has valid service key
        ...     logger.info("command_received", key_name=key_name, action=command.action)
        ...     # ... rest of endpoint logic
    
    Example valid header:
        X-Service-Key: sk_dev_test_key_12345678901234567890123456789012
    """
    result = await db.fetchrow("""
        SELECT key_name FROM service_api_keys 
        WHERE api_key = $1 
        AND active = true 
        AND (expires_at IS NULL OR expires_at > NOW())
    """, x_service_key)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired service key"
        )

    return result['key_name']
