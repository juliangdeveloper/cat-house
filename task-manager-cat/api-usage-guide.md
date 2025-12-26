# Task Manager API - Usage Guide

**Version:** 1.0.0  
**Last Updated:** November 13, 2025

---

## Table of Contents

1. [Overview](#overview)
2. [Universal Command Pattern](#universal-command-pattern)
3. [Authentication Setup](#authentication-setup)
4. [Available Actions](#available-actions)
5. [Example Requests](#example-requests)
6. [Error Handling](#error-handling)
7. [Best Practices for Cat House Integration](#best-practices-for-cat-house-integration)

---

## Overview

The Task Manager API provides task management functionality for the Cat House Platform ecosystem. It implements a **Universal Command Pattern** where all operations flow through a single endpoint (`POST /execute`), making integration simple and consistent.

**Base URL (Development):** `http://localhost:8888`  
**Base URL (Production):** `https://api.task-manager.cathouse.example.com`

---

## Universal Command Pattern

All task operations use the same request structure:

```json
{
  "action": "action-name",
  "user_id": "user_identifier",
  "payload": { /* action-specific parameters */ }
}
```

**Benefits:**
- Single integration endpoint to maintain
- Consistent request/response format
- Easy to extend with new actions
- Simplified error handling

**Response Format:**

```json
{
  "success": true,
  "data": { /* action-specific response */ },
  "error": null,
  "timestamp": "2025-11-13T10:00:00Z"
}
```

---

## Authentication Setup

### Getting a Service API Key

Service API keys are created by Cat House administrators via the admin endpoints:

```bash
# Create new service key (requires X-Admin-Key header)
curl -X POST http://localhost:8888/admin/service-keys \
  -H "X-Admin-Key: your-admin-key" \
  -H "Content-Type: application/json" \
  -d '{
    "key_name": "cat-house-prod",
    "environment": "prod"
  }'
```

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "key_name": "cat-house-prod",
  "service_key": "sk_prod_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
  "created_at": "2025-11-13T10:00:00Z"
}
```

**⚠️ Security Warning:** Store the `service_key` securely. It will only be shown once during creation.

### Using the Service Key

Include the service key in the `X-Service-Key` header for all requests to `/execute`:

```bash
curl -X POST http://localhost:8888/execute \
  -H "X-Service-Key: sk_prod_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6" \
  -H "Content-Type: application/json" \
  -d '{ "action": "list-tasks", "user_id": "user_123", "payload": {} }'
```

### Key Rotation

Rotate keys without downtime using the admin rotation endpoint:

```bash
curl -X POST http://localhost:8888/admin/rotate-key \
  -H "X-Admin-Key: your-admin-key" \
  -H "Content-Type: application/json" \
  -d '{"key_name": "cat-house-prod"}'
```

**Response:**
```json
{
  "new_key": "sk_prod_new123...",
  "old_key_expires_at": "2025-11-20T10:00:00Z"
}
```

Both keys work during the 7-day grace period, allowing zero-downtime migration.

---

## Available Actions

### 1. create-task

Create a new task for a user.

**Payload:**
- `title` (string, required): Task title (max 500 characters)
- `description` (string, optional): Task description
- `status` (string, optional): `pending` | `in_progress` | `completed` (default: `pending`)
- `priority` (string, optional): `low` | `medium` | `high` | `urgent`
- `due_date` (datetime, optional): ISO 8601 format (UTC)

**Response:** TaskResponse object with generated `id`, `created_at`, etc.

### 2. list-tasks

Retrieve all tasks for a user with optional filtering.

**Payload:**
- `status` (string, optional): Filter by status
- `priority` (string, optional): Filter by priority

**Response:** Array of TaskResponse objects

### 3. get-task

Retrieve a specific task by ID.

**Payload:**
- `task_id` (string, required): UUID of the task

**Response:** TaskResponse object

### 4. update-task

Update an existing task (partial updates supported).

**Payload:**
- `task_id` (string, required): UUID of the task
- `title` (string, optional): New title
- `description` (string, optional): New description
- `status` (string, optional): New status
- `priority` (string, optional): New priority
- `due_date` (datetime, optional): New due date

**Response:** Updated TaskResponse object

### 5. delete-task

Delete a task by ID.

**Payload:**
- `task_id` (string, required): UUID of the task

**Response:** Confirmation message

### 6. get-stats

Retrieve task statistics for a user.

**Payload:** Empty object `{}`

**Response:**
- `total_tasks` (int): Total task count
- `pending_tasks` (int): Pending tasks
- `in_progress_tasks` (int): In-progress tasks
- `completed_tasks` (int): Completed tasks
- `completion_rate` (float): Percentage (0.0 to 100.0)
- `overdue_tasks` (int): Overdue tasks

---

## Example Requests

### Create Task (curl)

```bash
curl -X POST http://localhost:8888/execute \
  -H "X-Service-Key: sk_dev_test_key_..." \
  -H "Content-Type: application/json" \
  -d '{
    "action": "create-task",
    "user_id": "user_123",
    "payload": {
      "title": "Buy cat food",
      "description": "Whiskers needs more treats",
      "status": "pending",
      "priority": "high",
      "due_date": "2025-11-15T10:00:00Z"
    }
  }'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "user_123",
    "title": "Buy cat food",
    "description": "Whiskers needs more treats",
    "status": "pending",
    "priority": "high",
    "created_at": "2025-11-13T10:00:00Z",
    "completed_at": null,
    "due_date": "2025-11-15T10:00:00Z"
  },
  "error": null,
  "timestamp": "2025-11-13T10:00:05Z"
}
```

### Create Task (Python)

```python
import requests
from datetime import datetime, timedelta

API_URL = "http://localhost:8888/execute"
SERVICE_KEY = "sk_dev_test_key_..."

def create_task(user_id: str, title: str, priority: str = "medium", due_date: datetime = None):
    """Create a new task via Task Manager API"""
    payload = {
        "action": "create-task",
        "user_id": user_id,
        "payload": {
            "title": title,
            "priority": priority,
            "due_date": due_date.isoformat() if due_date else None
        }
    }
    
    headers = {
        "X-Service-Key": SERVICE_KEY,
        "Content-Type": "application/json"
    }
    
    response = requests.post(API_URL, json=payload, headers=headers)
    response.raise_for_status()
    
    return response.json()

# Example usage
result = create_task(
    user_id="user_123",
    title="Buy cat food",
    priority="high",
    due_date=datetime.now() + timedelta(days=2)
)

print(f"Created task: {result['data']['id']}")
```

### List Tasks (curl)

```bash
curl -X POST http://localhost:8888/execute \
  -H "X-Service-Key: sk_dev_test_key_..." \
  -H "Content-Type: application/json" \
  -d '{
    "action": "list-tasks",
    "user_id": "user_123",
    "payload": {"status": "pending"}
  }'
```

### Update Task (Python)

```python
def update_task(user_id: str, task_id: str, **updates):
    """Update task fields (partial update supported)"""
    payload = {
        "action": "update-task",
        "user_id": user_id,
        "payload": {
            "task_id": task_id,
            **updates
        }
    }
    
    headers = {
        "X-Service-Key": SERVICE_KEY,
        "Content-Type": "application/json"
    }
    
    response = requests.post(API_URL, json=payload, headers=headers)
    response.raise_for_status()
    
    return response.json()

# Mark task as completed
result = update_task(
    user_id="user_123",
    task_id="550e8400-e29b-41d4-a716-446655440000",
    status="completed"
)
```

### Get Statistics (curl)

```bash
curl -X POST http://localhost:8888/execute \
  -H "X-Service-Key: sk_dev_test_key_..." \
  -H "Content-Type: application/json" \
  -d '{
    "action": "get-stats",
    "user_id": "user_123",
    "payload": {}
  }'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "total_tasks": 10,
    "pending_tasks": 3,
    "in_progress_tasks": 2,
    "completed_tasks": 5,
    "completion_rate": 50.0,
    "overdue_tasks": 2
  },
  "error": null,
  "timestamp": "2025-11-13T12:00:00Z"
}
```

---

## Error Handling

### Error Response Format

```json
{
  "success": false,
  "data": null,
  "error": "Error message here",
  "timestamp": "2025-11-13T10:30:15Z"
}
```

### Common HTTP Status Codes

| Status | Meaning | Example |
|--------|---------|---------|
| 200 | Success | Command executed successfully |
| 400 | Bad Request | Unknown action or invalid payload |
| 401 | Unauthorized | Invalid or missing service key |
| 404 | Not Found | Task not found or belongs to different user |
| 422 | Validation Error | Request body failed validation |

### Validation Errors (422)

FastAPI returns detailed validation errors:

```json
{
  "detail": [
    {
      "loc": ["body", "action"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### Python Error Handling

```python
def safe_api_call(payload: dict):
    """Make API call with proper error handling"""
    try:
        response = requests.post(API_URL, json=payload, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        if not result['success']:
            print(f"Command failed: {result['error']}")
            return None
        
        return result['data']
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print("Authentication failed - check service key")
        elif e.response.status_code == 404:
            print("Resource not found")
        elif e.response.status_code == 422:
            print(f"Validation error: {e.response.json()}")
        else:
            print(f"HTTP error: {e}")
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None
```

---

## Best Practices for Cat House Integration

### 1. User Isolation

Always include the correct `user_id` from Cat House's JWT token:

```python
# Extract user_id from JWT token
user_id = jwt_token['sub']  # or jwt_token['user_id']

# Pass to Task Manager API
payload = {
    "action": "list-tasks",
    "user_id": user_id,  # Ensures data isolation
    "payload": {}
}
```

### 2. Service Key Security

**✅ Do:**
- Store service key in environment variables
- Keep key on backend only (never expose to frontend)
- Rotate keys periodically (use 7-day grace period)
- Use different keys for dev/staging/prod

**❌ Don't:**
- Hardcode keys in source code
- Commit keys to version control
- Send keys to frontend/mobile apps
- Share keys between environments

```python
# Good: Load from environment
SERVICE_KEY = os.environ.get('TASK_MANAGER_API_KEY')

# Bad: Hardcoded
SERVICE_KEY = "sk_prod_abc123..."  # ❌ Never do this
```

### 3. Error Handling

Always check the `success` flag in responses:

```python
result = api_call(payload)

if not result['success']:
    # Handle error
    log_error(result['error'])
    return error_response_to_user()

# Process data
data = result['data']
```

### 4. Payload Validation

Validate user input before sending to API:

```python
def create_task_for_user(user_id: str, title: str, **kwargs):
    # Validate inputs
    if not title or len(title) > 500:
        raise ValueError("Title must be 1-500 characters")
    
    if 'status' in kwargs and kwargs['status'] not in ['pending', 'in_progress', 'completed']:
        raise ValueError("Invalid status")
    
    # Send to API
    return create_task(user_id, title, **kwargs)
```

### 5. Rate Limiting (Future)

Currently no rate limits, but plan for implementation:

```python
import time
from functools import wraps

def rate_limit(calls_per_second=10):
    """Decorator to rate limit API calls"""
    min_interval = 1.0 / calls_per_second
    last_called = [0.0]
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)
            
            last_called[0] = time.time()
            return func(*args, **kwargs)
        
        return wrapper
    return decorator

@rate_limit(calls_per_second=10)
def api_call(payload):
    return requests.post(API_URL, json=payload, headers=headers)
```

### 6. Logging and Monitoring

Log all API interactions for debugging:

```python
import logging

logger = logging.getLogger(__name__)

def api_call_with_logging(payload):
    logger.info(f"API call: action={payload['action']}, user_id={payload['user_id']}")
    
    try:
        result = api_call(payload)
        logger.info(f"API success: {result['data']}")
        return result
    except Exception as e:
        logger.error(f"API error: {e}", exc_info=True)
        raise
```

### 7. Testing

Mock API responses in Cat House tests:

```python
from unittest.mock import patch

@patch('requests.post')
def test_create_task(mock_post):
    # Mock successful response
    mock_post.return_value.json.return_value = {
        "success": True,
        "data": {"id": "task-123", "title": "Test task"},
        "error": None,
        "timestamp": "2025-11-13T10:00:00Z"
    }
    
    result = create_task("user_123", "Test task")
    assert result['success'] is True
    assert result['data']['title'] == "Test task"
```

---

## Additional Resources

- **Interactive API Docs:** http://localhost:8888/docs (Swagger UI)
- **Alternative Docs:** http://localhost:8888/redoc (ReDoc)
- **OpenAPI Spec:** http://localhost:8888/openapi.json
- **Health Check:** http://localhost:8888/health

---
