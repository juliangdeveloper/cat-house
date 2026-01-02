"""
Prometheus metrics module for tracking HTTP requests, database operations, and business events.
"""

from prometheus_client import Counter, Histogram, Gauge, REGISTRY
from app.config import settings

# HTTP Request metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status", "service"],
    registry=REGISTRY,
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint", "service"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
    registry=REGISTRY,
)

http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently being processed",
    ["method", "service"],
    registry=REGISTRY,
)

# Database metrics
db_connections_active = Gauge(
    "db_connections_active",
    "Number of active database connections",
    ["service"],
    registry=REGISTRY,
)

db_query_duration_seconds = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    ["service", "operation"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0],
    registry=REGISTRY,
)

# Business metrics
business_events_total = Counter(
    "business_events_total",
    "Total business events",
    ["service", "event_type"],
    registry=REGISTRY,
)

# Service health
service_health_status = Gauge(
    "service_health_status",
    "Service health status (1=healthy, 0=unhealthy)",
    ["service"],
    registry=REGISTRY,
)


def track_request_metrics(
    method: str, endpoint: str, status_code: int, duration: float
):
    """Track HTTP request metrics."""
    http_requests_total.labels(
        method=method,
        endpoint=endpoint,
        status=status_code,
        service=settings.service_name,
    ).inc()

    http_request_duration_seconds.labels(
        method=method, endpoint=endpoint, service=settings.service_name
    ).observe(duration)


def track_business_event(event_type: str):
    """Track business events (user registration, cat installation, etc.)."""
    business_events_total.labels(
        service=settings.service_name, event_type=event_type
    ).inc()


def track_db_query(operation: str, duration: float):
    """Track database query duration."""
    db_query_duration_seconds.labels(
        service=settings.service_name, operation=operation
    ).observe(duration)


def set_service_health(healthy: bool):
    """Set service health status."""
    service_health_status.labels(service=settings.service_name).set(1 if healthy else 0)
