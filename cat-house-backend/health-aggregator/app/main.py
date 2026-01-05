from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import httpx
import asyncio
from typing import Dict, Any
from contextlib import asynccontextmanager

from app.logging_config import logger, setup_logging
from app.middleware import correlation_id_middleware

# Setup logging on startup
setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Health Aggregator Service")
    logger.info("Environment: development")
    logger.info("Service port: 8006")
    yield
    # Shutdown
    logger.info("Shutting down Health Aggregator Service")

app = FastAPI(
    title="Health Aggregator Service", 
    version="1.0.0",
    lifespan=lifespan
)

# Add correlation ID middleware (must be first)
app.middleware("http")(correlation_id_middleware)

# Service endpoints to check
SERVICES = {
    "auth": "http://cathouse-auth:8005/api/v1/auth/health",
    "catalog": "http://cathouse-catalog:8002/api/v1/catalog/health",
    "installation": "http://cathouse-installation:8003/api/v1/installation/health",
    "proxy": "http://cathouse-proxy:8004/api/v1/proxy/health"
}

async def check_service(client: httpx.AsyncClient, name: str, url: str) -> Dict[str, Any]:
    """
    Check the health of a single service.
    
    Args:
        client: HTTP client to use for the request
        name: Name of the service
        url: Health endpoint URL
        
    Returns:
        Dictionary with service health status
    """
    try:
        response = await client.get(url)
        response.raise_for_status()
        data = response.json()
        
        return {
            "status": data.get("status", "unknown"),
            "timestamp": data.get("timestamp"),
            "response_time_ms": response.elapsed.total_seconds() * 1000
        }
    except httpx.TimeoutException:
        logger.error(f"Service {name} timed out")
        return {
            "status": "unhealthy",
            "error": "Request timed out",
            "response_time_ms": None
        }
    except httpx.HTTPStatusError as e:
        logger.error(f"Service {name} returned status {e.response.status_code}")
        return {
            "status": "unhealthy",
            "error": f"HTTP {e.response.status_code}",
            "response_time_ms": e.response.elapsed.total_seconds() * 1000
        }
    except Exception as e:
        logger.error(f"Service {name} check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "response_time_ms": None
        }

@app.get("/api/v1/health")
async def health_check():
    """
    Aggregate health check endpoint.
    
    Checks all backend services and returns an aggregated health status.
    Returns:
        - 200 if all services are healthy
        - 503 if any service is unhealthy or degraded
    """
    timeout = httpx.Timeout(5.0, connect=2.0)
    
    async with httpx.AsyncClient(timeout=timeout) as client:
        # Create tasks for all service health checks
        tasks = [
            check_service(client, name, url) 
            for name, url in SERVICES.items()
        ]
        
        # Execute all health checks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Build services status dictionary
    services = {}
    overall_healthy = True
    healthy_count = 0
    total_count = len(SERVICES)
    
    for (name, _), result in zip(SERVICES.items(), results):
        if isinstance(result, Exception):
            services[name] = {
                "status": "unhealthy",
                "error": str(result),
                "response_time_ms": None
            }
            overall_healthy = False
        else:
            services[name] = result
            if result.get("status") == "healthy":
                healthy_count += 1
            else:
                overall_healthy = False
    
    # Determine overall status
    if overall_healthy:
        overall_status = "healthy"
        status_code = 200
    elif healthy_count > 0:
        overall_status = "degraded"
        status_code = 503
    else:
        overall_status = "unhealthy"
        status_code = 503
    
    response_data = {
        "status": overall_status,
        "services": services,
        "summary": {
            "total": total_count,
            "healthy": healthy_count,
            "unhealthy": total_count - healthy_count
        }
    }
    
    return JSONResponse(
        status_code=status_code,
        content=response_data
    )

@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "Health Aggregator",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)
