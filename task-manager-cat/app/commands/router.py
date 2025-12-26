"""
Command Router implementing Universal Command Pattern.

Routes standardized command requests to appropriate action handlers.
Single endpoint (POST /execute) dispatches to multiple handlers based on action name.

Architecture:
    - ACTION_HANDLERS: Registry mapping action names to handler functions
    - execute_command: POST /execute endpoint with authentication and routing
    - Handlers added in Epic 3.3/3.4 (create-task, list-tasks, etc.)
"""

from collections.abc import Awaitable
from typing import Any, Callable

import structlog
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import validate_service_key
from app.commands.handlers.stats import get_stats_handler
from app.commands.handlers.tasks import (
    create_task_handler,
    delete_task_handler,
    get_task_handler,
    list_tasks_handler,
    update_task_handler,
)
from app.commands.models import CommandRequest, CommandResponse
from app.database import get_db

# Type alias for command handler functions
CommandHandler = Callable[[str, dict, Any], Awaitable[dict]]

logger = structlog.get_logger()

# Create FastAPI router (no prefix - endpoint becomes /execute)
router = APIRouter(tags=["Commands"])

# Handler registry - maps action names to handler functions
# Handlers added in Epic 3.3/3.4 (task CRUD) and Epic 4.2 (statistics)
# Handler signature: async def handler(user_id: str, payload: dict, db: Any) -> dict
ACTION_HANDLERS: dict[str, CommandHandler] = {
    "create-task": create_task_handler,
    "list-tasks": list_tasks_handler,
    "get-task": get_task_handler,
    "update-task": update_task_handler,
    "delete-task": delete_task_handler,
    "get-stats": get_stats_handler,
}


@router.post("/execute", response_model=CommandResponse, responses={
    200: {
        "description": "Command executed successfully",
        "content": {
            "application/json": {
                "example": {
                    "success": True,
                    "data": {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "user_id": "user_123",
                        "title": "Buy cat food",
                        "description": "Whiskers needs more treats",
                        "status": "pending",
                        "priority": "high",
                        "created_at": "2025-11-13T10:00:00Z",
                        "completed_at": None,
                        "due_date": "2025-11-15T10:00:00Z"
                    },
                    "error": None,
                    "timestamp": "2025-11-13T10:00:05Z"
                }
            }
        }
    },
    400: {
        "description": "Unknown action or invalid payload",
        "content": {
            "application/json": {
                "example": {"detail": "Unknown action: invalid-action"}
            }
        }
    },
    401: {
        "description": "Invalid or missing service key",
        "content": {
            "application/json": {
                "example": {"detail": "Invalid service key"}
            }
        }
    },
    422: {
        "description": "Validation error in request body",
        "content": {
            "application/json": {
                "example": {
                    "detail": [
                        {
                            "loc": ["body", "action"],
                            "msg": "field required",
                            "type": "value_error.missing"
                        }
                    ]
                }
            }
        }
    }
})
async def execute_command(
    command: CommandRequest,
    key_name: str = Depends(validate_service_key),
    db: Any = Depends(get_db)
) -> CommandResponse:
    """
    Universal command router implementing Command Pattern for all task operations.
    
    This endpoint serves as the single integration point for Cat House Platform, routing
    all task-related commands to their appropriate handlers based on the action name.
    
    ## Universal Command Pattern
    
    All operations use the same request structure:
    - **action**: The command to execute (e.g., "create-task", "get-stats")
    - **user_id**: User identifier from Cat House JWT token
    - **payload**: Action-specific parameters (varies by action)
    
    ## Available Command Actions
    
    ### create-task
    Create a new task for the specified user.
    
    **Payload Fields:**
    - `title` (string, required): Task title (max 500 characters)
    - `description` (string, optional): Task description
    - `status` (string, optional): pending | in_progress | completed (default: pending)
    - `priority` (string, optional): low | medium | high | urgent
    - `due_date` (datetime, optional): Task due date in ISO 8601 format (UTC)
    
    **Response Data:** TaskResponse object with generated id, created_at, etc.
    
    **Example:**
    ```json
    {
        "action": "create-task",
        "user_id": "user_123",
        "payload": {
            "title": "Buy cat food",
            "description": "Whiskers needs more treats",
            "status": "pending",
            "priority": "high",
            "due_date": "2025-11-15T10:00:00Z"
        }
    }
    ```
    
    ### list-tasks
    Retrieve all tasks for the specified user with optional filtering.
    
    **Payload Fields:**
    - `status` (string, optional): Filter by status (pending | in_progress | completed)
    - `priority` (string, optional): Filter by priority (low | medium | high | urgent)
    
    **Response Data:** Array of TaskResponse objects
    
    **Example:**
    ```json
    {
        "action": "list-tasks",
        "user_id": "user_456",
        "payload": {"status": "pending"}
    }
    ```
    
    ### get-task
    Retrieve a specific task by ID.
    
    **Payload Fields:**
    - `task_id` (string, required): UUID of the task to retrieve
    
    **Response Data:** TaskResponse object
    
    **Example:**
    ```json
    {
        "action": "get-task",
        "user_id": "user_123",
        "payload": {"task_id": "550e8400-e29b-41d4-a716-446655440000"}
    }
    ```
    
    ### update-task
    Update an existing task (partial updates supported).
    
    **Payload Fields:**
    - `task_id` (string, required): UUID of the task to update
    - `title` (string, optional): New task title
    - `description` (string, optional): New task description
    - `status` (string, optional): New status (pending | in_progress | completed)
    - `priority` (string, optional): New priority (low | medium | high | urgent)
    - `due_date` (datetime, optional): New due date in ISO 8601 format
    
    **Response Data:** Updated TaskResponse object
    
    **Example:**
    ```json
    {
        "action": "update-task",
        "user_id": "user_123",
        "payload": {
            "task_id": "550e8400-e29b-41d4-a716-446655440000",
            "status": "completed"
        }
    }
    ```
    
    ### delete-task
    Delete a task by ID.
    
    **Payload Fields:**
    - `task_id` (string, required): UUID of the task to delete
    
    **Response Data:** Confirmation message
    
    **Example:**
    ```json
    {
        "action": "delete-task",
        "user_id": "user_123",
        "payload": {"task_id": "550e8400-e29b-41d4-a716-446655440000"}
    }
    ```
    
    ### get-stats
    Retrieve task statistics for the specified user.
    
    **Payload Fields:** Empty object `{}`
    
    **Response Data:**
    - `total_tasks` (int): Total number of tasks
    - `pending_tasks` (int): Tasks with status = pending
    - `in_progress_tasks` (int): Tasks with status = in_progress
    - `completed_tasks` (int): Tasks with status = completed
    - `completion_rate` (float): Percentage of completed tasks (0.0 to 100.0)
    - `overdue_tasks` (int): Tasks past due_date and not completed
    
    **Example:**
    ```json
    {
        "action": "get-stats",
        "user_id": "user_789",
        "payload": {}
    }
    ```
    
    ## Authentication
    
    All requests require a valid service API key in the `X-Service-Key` header.
    Keys are issued by Cat House administrators via `/admin/service-keys` endpoint.
    
    ## Response Format
    
    All responses follow the CommandResponse structure:
    - `success` (bool): Whether the command succeeded
    - `data` (dict): Action-specific response data (null on error)
    - `error` (string): Error message if success=false (null on success)
    - `timestamp` (datetime): UTC timestamp of response generation
    
    ## Error Handling
    
    - **400 Bad Request**: Unknown action or invalid payload structure
    - **401 Unauthorized**: Missing or invalid X-Service-Key header
    - **404 Not Found**: Resource not found (task doesn't exist or belongs to different user)
    - **422 Unprocessable Entity**: Validation errors in request body
    
    Args:
        command: CommandRequest with action, user_id, and payload
        key_name: Validated service key name (from validate_service_key dependency)
        db: Database connection pool (from get_db dependency)
    
    Returns:
        CommandResponse with success flag, data, and timestamp
    
    Raises:
        HTTPException(401): Invalid service key (raised by validate_service_key)
        HTTPException(404): Unknown action (not in ACTION_HANDLERS)
        HTTPException(500): Handler execution error (wrapped in CommandResponse)
    """
    # Log command received
    logger.info(
        "command_received",
        action=command.action,
        user_id=command.user_id,
        key_name=key_name
    )

    # Check if action exists
    if command.action not in ACTION_HANDLERS:
        logger.warning(
            "unknown_action",
            action=command.action,
            user_id=command.user_id,
            key_name=key_name
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown action: {command.action}"
        )

    # Route to handler
    try:
        handler = ACTION_HANDLERS[command.action]
        result = await handler(command.user_id, command.payload, db)

        logger.info(
            "command_success",
            action=command.action,
            user_id=command.user_id,
            key_name=key_name
        )

        return CommandResponse(success=True, data=result, error=None)

    except HTTPException:
        # Re-raise HTTP exceptions (handler validation errors)
        raise

    except Exception as e:
        logger.error(
            "command_failed",
            action=command.action,
            user_id=command.user_id,
            key_name=key_name,
            error=str(e)
        )
        return CommandResponse(success=False, data=None, error=str(e))
