"""
Middleware for correlation IDs and metrics tracking.
"""

import time
from uuid import uuid4

from fastapi import Request

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
        },
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
        },
    )

    return response


async def metrics_middleware(request: Request, call_next):
    """Track metrics for all requests."""
    from app.metrics import (
        track_request_metrics,
        http_requests_in_progress,
    )
    from app.config import settings

    # Track in-progress requests
    http_requests_in_progress.labels(
        method=request.method, service=settings.service_name
    ).inc()

    start_time = time.time()

    try:
        response = await call_next(request)
        duration = time.time() - start_time

        # Track request metrics
        track_request_metrics(
            method=request.method,
            endpoint=request.url.path,
            status_code=response.status_code,
            duration=duration,
        )

        return response

    finally:
        # Decrement in-progress counter
        http_requests_in_progress.labels(
            method=request.method, service=settings.service_name
        ).dec()
