# Health Aggregator Service

This service aggregates health checks from all backend services in the Cat House platform.

## Purpose

- Provides a unified health check endpoint for monitoring
- Checks health of all microservices concurrently
- Returns aggregated status (healthy, degraded, or unhealthy)
- Used by the Nginx gateway and external monitoring tools

## Endpoints

### GET /health

Returns the aggregated health status of all services.

**Response (200 - All Healthy):**
```json
{
  "status": "healthy",
  "services": {
    "auth": {
      "status": "healthy",
      "timestamp": "2025-12-16T10:30:00Z",
      "response_time_ms": 45.3
    },
    "catalog": {
      "status": "healthy",
      "timestamp": "2025-12-16T10:30:00Z",
      "response_time_ms": 38.1
    },
    "installation": {
      "status": "healthy",
      "timestamp": "2025-12-16T10:30:00Z",
      "response_time_ms": 52.7
    },
    "proxy": {
      "status": "healthy",
      "timestamp": "2025-12-16T10:30:00Z",
      "response_time_ms": 41.2
    }
  },
  "summary": {
    "total": 4,
    "healthy": 4,
    "unhealthy": 0
  }
}
```

**Response (503 - Degraded/Unhealthy):**
```json
{
  "status": "degraded",
  "services": {
    "auth": {
      "status": "healthy",
      "timestamp": "2025-12-16T10:30:00Z",
      "response_time_ms": 45.3
    },
    "catalog": {
      "status": "unhealthy",
      "error": "Request timed out",
      "response_time_ms": null
    },
    "installation": {
      "status": "healthy",
      "timestamp": "2025-12-16T10:30:00Z",
      "response_time_ms": 52.7
    },
    "proxy": {
      "status": "healthy",
      "timestamp": "2025-12-16T10:30:00Z",
      "response_time_ms": 41.2
    }
  },
  "summary": {
    "total": 4,
    "healthy": 3,
    "unhealthy": 1
  }
}
```

### GET /

Root endpoint with service information.

## Configuration

The service checks the following backend services:
- Auth Service: `http://cathouse-auth:8005/health`
- Catalog Service: `http://cathouse-catalog:8002/health`
- Installation Service: `http://cathouse-installation:8003/health`
- Proxy Service: `http://cathouse-proxy:8004/health`

## Timeouts

- Connection timeout: 2 seconds
- Read timeout: 5 seconds

## Running Locally

```bash
cd health-aggregator
pip install -r requirements.txt
python -m app.main
```

Service will be available at http://localhost:8000

## Docker

```bash
docker build -t cathouse-health .
docker run -p 8000:8000 cathouse-health
```
