"""
Task command handlers for Task Manager API.

Implements action handlers for task CRUD operations:
- create-task: Create a new task for user
- list-tasks: List all tasks for user with optional status filter

All handlers follow universal handler signature:
    async def handler(user_id: str, payload: dict, db) -> dict

Architecture:
    - user_id: External user ID from Cat House (already authenticated)
    - payload: Action-specific parameters (validated by handler using Pydantic)
    - db: asyncpg database connection from pool
    - Returns: dict response (wrapped in CommandResponse by router)
    - Raises: HTTPException for validation/business logic errors
"""

from typing import Any, Optional
from uuid import UUID

import structlog
from fastapi import HTTPException
from pydantic import ValidationError

from app.models.task import TaskCreate, TaskResponse, TaskUpdate

logger = structlog.get_logger()


async def create_task_handler(user_id: str, payload: dict, db: Any) -> dict:
    """
    Create a new task for user.
    
    Handler for 'create-task' action. Validates payload using TaskCreate model,
    inserts task into database with user_id, and returns created task.
    
    Args:
        user_id: External user ID from Cat House (already authenticated)
        payload: Task creation data (title, description?, status?, priority?, due_date?)
        db: asyncpg database connection from pool
    
    Returns:
        dict: Created task object with all fields (id, created_at, etc.)
    
    Raises:
        HTTPException(400): Validation error (missing title, invalid status, etc.)
        HTTPException(500): Database error
    
    Example:
        Input payload: {"title": "Buy milk", "priority": "high"}
        Output: {
            "id": "uuid",
            "user_id": "user_123",
            "title": "Buy milk",
            "description": null,
            "status": "pending",
            "priority": "high",
            "created_at": "2025-11-12T10:00:00Z",
            "completed_at": null,
            "due_date": null
        }
    """
    # Validate payload using TaskCreate model
    try:
        task_data = TaskCreate(**payload)
    except ValidationError as e:
        logger.warning(
            "task_validation_error",
            user_id=user_id,
            error=str(e)
        )
        raise HTTPException(status_code=400, detail=str(e))

    # Prepare SQL INSERT with RETURNING
    sql = """
        INSERT INTO tasks (user_id, title, description, status, priority, due_date)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING *
    """

    try:
        # Execute INSERT and get created task
        row = await db.fetchrow(
            sql,
            user_id,
            task_data.title,
            task_data.description,
            task_data.status,
            task_data.priority,
            task_data.due_date
        )

        # Convert asyncpg Row to dict, then to TaskResponse
        row_dict = dict(row)
        task_response = TaskResponse.model_validate(row_dict)

        # Log successful creation
        logger.info(
            "task_created",
            task_id=str(task_response.id),
            user_id=user_id,
            title=task_data.title
        )

        # Return dict for CommandResponse wrapping
        return task_response.model_dump(mode='json')

    except Exception as e:
        logger.error(
            "database_error",
            action="create-task",
            user_id=user_id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Internal server error")


async def list_tasks_handler(user_id: str, payload: dict, db: Any) -> dict:
    """
    List all tasks for user with optional status filter.
    
    Handler for 'list-tasks' action. Queries tasks WHERE user_id = command.user_id,
    applies optional status filter from payload, and returns array of tasks.
    
    Args:
        user_id: External user ID from Cat House (already authenticated)
        payload: Optional filters (status?: string)
        db: asyncpg database connection from pool
    
    Returns:
        dict: Response with tasks array and count
            {"tasks": [...], "count": number}
    
    Raises:
        HTTPException(500): Database error
    
    Examples:
        Input payload (no filter): {}
        Output: {"tasks": [task1, task2, task3], "count": 3}
        
        Input payload (with filter): {"status": "pending"}
        Output: {"tasks": [task1, task2], "count": 2}
    """
    # Extract optional status filter
    status_filter: Optional[str] = payload.get('status')

    # Build SQL query based on filters
    if status_filter:
        sql = """
            SELECT * FROM tasks 
            WHERE user_id = $1 AND status = $2 
            ORDER BY created_at DESC
        """
        query_params = (user_id, status_filter)
    else:
        sql = """
            SELECT * FROM tasks 
            WHERE user_id = $1 
            ORDER BY created_at DESC
        """
        query_params = (user_id,)

    try:
        # Execute query
        rows = await db.fetch(sql, *query_params)

        # Convert rows to TaskResponse objects and then to dicts
        tasks = [
            TaskResponse.model_validate(dict(row)).model_dump(mode='json')
            for row in rows
        ]

        # Log successful query
        logger.info(
            "tasks_listed",
            user_id=user_id,
            status_filter=status_filter,
            count=len(tasks)
        )

        # Return dict with tasks array and count
        return {"tasks": tasks, "count": len(tasks)}

    except Exception as e:
        logger.error(
            "database_error",
            action="list-tasks",
            user_id=user_id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Internal server error")


async def get_task_handler(user_id: str, payload: dict, db: Any) -> dict:
    """
    Retrieve a single task by ID.
    
    Handler for 'get-task' action. Queries task by ID without user ownership
    check (trusts Cat House authorization). Returns complete task object or
    404 error if task not found.
    
    Args:
        user_id: External user ID from Cat House (for logging only)
        payload: Task identifier (task_id: uuid)
        db: asyncpg database connection from pool
    
    Returns:
        dict: Complete task object with all fields
    
    Raises:
        HTTPException(400): Missing or invalid task_id format
        HTTPException(404): Task not found
        HTTPException(500): Database error
    
    Example:
        Input payload: {"task_id": "550e8400-e29b-41d4-a716-446655440000"}
        Output: {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "user_id": "user_123",
            "title": "Buy milk",
            "status": "pending",
            ...
        }
    """
    # Extract task_id from payload
    task_id = payload.get('task_id')

    # Check if task_id is provided
    if not task_id:
        logger.warning(
            "validation_error",
            user_id=user_id,
            error="Missing required field: task_id"
        )
        raise HTTPException(status_code=400, detail="Missing required field: task_id")

    # Validate UUID format
    try:
        task_id_uuid = UUID(task_id)
    except (ValueError, TypeError):
        logger.warning(
            "validation_error",
            user_id=user_id,
            task_id=task_id,
            error="Invalid UUID format"
        )
        raise HTTPException(status_code=400, detail="Invalid UUID format for task_id")

    # Query task by ID (no user ownership check - trusts Cat House)
    sql = "SELECT * FROM tasks WHERE id = $1"

    try:
        row = await db.fetchrow(sql, task_id_uuid)

        # Handle not found
        if row is None:
            logger.warning(
                "task_not_found",
                task_id=str(task_id_uuid),
                user_id=user_id
            )
            raise HTTPException(status_code=404, detail=f"Task not found: {task_id_uuid}")

        # Convert asyncpg Row to dict and validate with TaskResponse
        row_dict = dict(row)
        task_response = TaskResponse.model_validate(row_dict)

        # Log successful retrieval
        logger.info(
            "task_retrieved",
            task_id=str(task_id_uuid),
            user_id=user_id
        )

        # Return dict for CommandResponse wrapping
        return task_response.model_dump(mode='json')

    except HTTPException:
        # Re-raise HTTPException (404) without wrapping
        raise
    except Exception as e:
        logger.error(
            "database_error",
            action="get-task",
            user_id=user_id,
            task_id=str(task_id_uuid),
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Internal server error")


async def update_task_handler(user_id: str, payload: dict, db: Any) -> dict:
    """
    Update task fields with partial update support.
    
    Handler for 'update-task' action. Supports partial updates (only provided
    fields are updated). Automatically manages completed_at timestamp:
    - Status = "completed" → sets completed_at = NOW()
    - Status = any other value → sets completed_at = NULL
    - Status not in payload → leaves completed_at unchanged
    
    Args:
        user_id: External user ID from Cat House (for logging only)
        payload: Task ID + optional update fields
            {task_id: uuid, title?, description?, status?, priority?, due_date?}
        db: asyncpg database connection from pool
    
    Returns:
        dict: Updated task object with all fields
    
    Raises:
        HTTPException(400): Missing/invalid task_id, no fields to update, or validation error
        HTTPException(404): Task not found
        HTTPException(500): Database error
    
    Example:
        Input payload: {"task_id": "uuid", "status": "completed", "priority": "high"}
        Output: {updated task with completed_at timestamp set}
    """
    # Extract and validate task_id
    task_id = payload.get('task_id')

    if not task_id:
        logger.warning(
            "validation_error",
            user_id=user_id,
            error="Missing required field: task_id"
        )
        raise HTTPException(status_code=400, detail="Missing required field: task_id")

    try:
        task_id_uuid = UUID(task_id)
    except (ValueError, TypeError):
        logger.warning(
            "validation_error",
            user_id=user_id,
            task_id=task_id,
            error="Invalid UUID format"
        )
        raise HTTPException(status_code=400, detail="Invalid UUID format for task_id")

    # Extract update fields (exclude task_id)
    update_fields_dict = {k: v for k, v in payload.items() if k != 'task_id'}

    # Validate update fields using TaskUpdate
    try:
        update_data = TaskUpdate(**update_fields_dict)
    except ValidationError as e:
        logger.warning(
            "validation_error",
            user_id=user_id,
            task_id=str(task_id_uuid),
            error=str(e)
        )
        raise HTTPException(status_code=400, detail=str(e))

    # Get only non-None fields for partial update
    update_dict = update_data.model_dump(exclude_none=True)

    if not update_dict:
        logger.warning(
            "validation_error",
            user_id=user_id,
            task_id=str(task_id_uuid),
            error="No fields provided for update"
        )
        raise HTTPException(status_code=400, detail="No fields provided for update")

    # Build dynamic UPDATE query
    set_clauses = []
    values = []
    param_index = 2  # $1 is task_id

    for field, value in update_dict.items():
        set_clauses.append(f"{field} = ${param_index}")
        values.append(value)
        param_index += 1

    # Handle completed_at based on status field
    if 'status' in update_dict:
        if update_dict['status'] == "completed":
            set_clauses.append("completed_at = NOW()")
        else:
            set_clauses.append("completed_at = NULL")

    # Build SQL with dynamic SET clause
    set_clause = ", ".join(set_clauses)
    sql = f"UPDATE tasks SET {set_clause} WHERE id = $1 RETURNING *"

    try:
        row = await db.fetchrow(sql, task_id_uuid, *values)

        # Handle not found
        if row is None:
            logger.warning(
                "task_not_found",
                task_id=str(task_id_uuid),
                user_id=user_id
            )
            raise HTTPException(status_code=404, detail=f"Task not found: {task_id_uuid}")

        # Convert asyncpg Row to dict and validate with TaskResponse
        row_dict = dict(row)
        task_response = TaskResponse.model_validate(row_dict)

        # Log successful update with fields changed
        logger.info(
            "task_updated",
            task_id=str(task_id_uuid),
            user_id=user_id,
            updated_fields=list(update_dict.keys())
        )

        # Return dict for CommandResponse wrapping
        return task_response.model_dump(mode='json')

    except HTTPException:
        # Re-raise HTTPException (404) without wrapping
        raise
    except Exception as e:
        logger.error(
            "database_error",
            action="update-task",
            user_id=user_id,
            task_id=str(task_id_uuid),
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Internal server error")


async def delete_task_handler(user_id: str, payload: dict, db: Any) -> dict:
    """
    Delete a task by ID.
    
    Handler for 'delete-task' action. Permanently deletes task from database
    without user ownership check (trusts Cat House authorization). Returns
    success confirmation with deleted task ID.
    
    Args:
        user_id: External user ID from Cat House (for logging only)
        payload: Task identifier (task_id: uuid)
        db: asyncpg database connection from pool
    
    Returns:
        dict: Success confirmation with deleted_id
            {"success": True, "deleted_id": "uuid"}
    
    Raises:
        HTTPException(400): Missing or invalid task_id format
        HTTPException(404): Task not found
        HTTPException(500): Database error
    
    Example:
        Input payload: {"task_id": "550e8400-e29b-41d4-a716-446655440000"}
        Output: {"success": true, "deleted_id": "550e8400-e29b-41d4-a716-446655440000"}
    """
    # Extract task_id from payload
    task_id = payload.get('task_id')

    # Check if task_id is provided
    if not task_id:
        logger.warning(
            "validation_error",
            user_id=user_id,
            error="Missing required field: task_id"
        )
        raise HTTPException(status_code=400, detail="Missing required field: task_id")

    # Validate UUID format
    try:
        task_id_uuid = UUID(task_id)
    except (ValueError, TypeError):
        logger.warning(
            "validation_error",
            user_id=user_id,
            task_id=task_id,
            error="Invalid UUID format"
        )
        raise HTTPException(status_code=400, detail="Invalid UUID format for task_id")

    # Delete task and return ID to confirm deletion
    sql = "DELETE FROM tasks WHERE id = $1 RETURNING id"

    try:
        row = await db.fetchrow(sql, task_id_uuid)

        # Handle not found
        if row is None:
            logger.warning(
                "task_not_found",
                task_id=str(task_id_uuid),
                user_id=user_id
            )
            raise HTTPException(status_code=404, detail=f"Task not found: {task_id_uuid}")

        # Log successful deletion
        logger.info(
            "task_deleted",
            task_id=str(task_id_uuid),
            user_id=user_id
        )

        # Return success response
        return {
            "success": True,
            "deleted_id": str(task_id_uuid)
        }

    except HTTPException:
        # Re-raise HTTPException (404) without wrapping
        raise
    except Exception as e:
        logger.error(
            "database_error",
            action="delete-task",
            user_id=user_id,
            task_id=str(task_id_uuid),
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Internal server error")
