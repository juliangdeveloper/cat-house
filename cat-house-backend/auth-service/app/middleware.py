"""
Correlation ID middleware for distributed tracing across microservices.
"""
from fastapi import Request
from uuid import uuid4
import time
from app.logging_config import logger, trace_id_var

async def correlation_id_middleware(request: Request, call_next):
    """Add correlation ID to all requests for distributed tracing."""
    # Get or generate trace ID
    trace_id = request.headers.get("X-Trace-ID", str(uuid4()))
    trace_id_var.set(trace_id)
    
    # Log request
    start_time = time.time()
    logger.info(
        f"Request started: {request.method} {request.url.path}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown"),
        }
    )
    
    # Process request
    response = await call_next(request)
    
    # Add trace ID to response headers
    response.headers["X-Trace-ID"] = trace_id
    
    # Log response
    duration = time.time() - start_time
    logger.info(
        f"Request completed: {response.status_code}",
        extra={
            "status_code": response.status_code,
            "duration_ms": round(duration * 1000, 2),
        }
    )
    
    return response
