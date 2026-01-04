"""Auth Service - Main application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.logging_config import logger, setup_logging
from app.middleware import correlation_id_middleware, metrics_middleware
from app.routers import health, metrics
from app.metrics import set_service_health

# Setup logging on startup
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting {settings.service_display_name}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Service port: {settings.port}")

    # Set service health to healthy
    set_service_health(True)

    yield

    # Shutdown
    logger.info(f"Shutting down {settings.service_display_name}")
    set_service_health(False)


app = FastAPI(
    title=settings.service_display_name,
    version="1.0.0",
    debug=settings.debug,
    docs_url="/api/v1/docs" if settings.debug else None,
    redoc_url="/api/v1/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# Add middlewares (order matters - metrics should be outermost)
app.middleware("http")(metrics_middleware)
app.middleware("http")(correlation_id_middleware)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api/v1/auth", tags=["health"])
app.include_router(metrics.router, prefix="/api/v1/auth", tags=["metrics"])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app", host="0.0.0.0", port=settings.port, reload=settings.debug
    )
