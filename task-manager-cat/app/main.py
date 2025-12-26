"""
Task Manager API - Main Application Entry Point

FastAPI application with structured logging, CORS middleware, and health check endpoint.
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app import __version__
from app.commands.router import router as command_router
from app.config import settings
from app.database import close_db_pool
from app.routers import admin

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    
    Handles startup and shutdown events:
    - Startup: Log configuration
    - Shutdown: Close database connection pool
    """
    # Startup
    logger.info(
        "application_startup",
        version="1.0.0",
        environment=settings.environment,
        log_level=settings.log_level,
    )

    yield

    # Shutdown
    logger.info("application_shutdown", message="Closing database connections")
    await close_db_pool()


# Create FastAPI application instance with lifespan handler
app = FastAPI(
    title="Task Manager API",
    description="""
## Task Manager API for Cat House Platform

A specialized backend service providing task management functionality for the Cat House Platform ecosystem.

### Universal Command Pattern Architecture

This API implements a **Universal Command Pattern** where all task operations flow through a single endpoint (`POST /execute`). 
Cat House Platform validates user authentication (JWT) and authorization before sending commands to this service.

**Benefits:**
- Single integration point for Cat House
- Consistent request/response format
- Easy to extend with new actions
- Service-to-service authentication via API keys

### Available Command Actions

1. **create-task** - Create a new task for a user
2. **list-tasks** - Retrieve all tasks for a user (with optional filtering)
3. **get-task** - Get a specific task by ID
4. **update-task** - Update an existing task (partial updates supported)
5. **delete-task** - Delete a task by ID
6. **get-stats** - Get task statistics (counts, completion rate, overdue tasks)

### Authentication

All protected endpoints require a **Service API Key** passed via the `X-Service-Key` header. 
Keys are managed through admin endpoints and must be kept secure on Cat House's backend (never exposed to frontend).

Public endpoints:
- `GET /health` - Health check for load balancers

Admin endpoints (require `X-Admin-Key` header):
- `POST /admin/service-keys` - Create new service key
- `GET /admin/service-keys` - List all service keys
- `DELETE /admin/service-keys/{key_id}` - Revoke a service key

### Cat House Integration

Cat House Platform acts as the API consumer:
1. User authenticates with Cat House (JWT token)
2. Cat House validates user permissions
3. Cat House sends command to Task Manager API with user_id
4. Task Manager executes action and returns result
5. Cat House displays result to user

All commands include `user_id` for data isolation - users only see their own tasks.
    """,
    version=__version__,
    contact={
        "name": "Cat House Platform Team",
        "email": "support@cathouse.example.com"
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    },
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Include routers
app.include_router(admin.router)
# Command router implements Universal Command Pattern (POST /execute)
app.include_router(command_router)

# CORS configuration from settings
# Purpose: Restrict cross-origin requests to Cat House Platform origins only
# Security: Wildcards (*) replaced with explicit values for production security
# Authentication: X-Service-Key header required (per Authentication Strategy - Service API Keys)
# Headers:
#   - X-Service-Key: Service authentication (custom header, triggers CORS preflight)
#   - Content-Type: JSON payloads (application/json triggers preflight)
# Methods: Limited to specific HTTP methods only (no TRACE, CONNECT, etc.)
# Credentials: Required for authentication headers (allow_credentials=True)
# Note: Cat House must keep service key secure on backend (never expose to frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["X-Service-Key", "Content-Type"],
)


@app.get("/health", status_code=200, tags=["Health"])
async def health_check():
    """Health check endpoint for load balancer verification"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def custom_openapi():
    """
    Custom OpenAPI schema generator with enhanced security documentation.
    
    Adds security schemes for service-to-service and admin authentication:
    - ServiceKey: X-Service-Key header for Cat House integration
    - AdminKey: X-Admin-Key header for key management operations
    """
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        contact=app.contact,
        license_info=app.license_info,
    )

    # Add security schemes for API documentation
    openapi_schema["components"]["securitySchemes"] = {
        "ServiceKey": {
            "type": "apiKey",
            "in": "header",
            "name": "X-Service-Key",
            "description": "Service API key for Cat House Platform integration. Required for all /execute commands."
        },
        "AdminKey": {
            "type": "apiKey",
            "in": "header",
            "name": "X-Admin-Key",
            "description": "Admin key for service key management endpoints. Required for all /admin/* endpoints."
        }
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
