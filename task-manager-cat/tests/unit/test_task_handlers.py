"""
Unit tests for task command handlers.

Tests handler business logic in isolation from HTTP layer.
Uses mocks for database operations (asyncpg).

Test Categories:
    - Payload validation (TaskCreate model)
    - Database operations (INSERT, SELECT)
    - Response format (dict with all fields)
    - Error handling (validation errors, database errors)
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from fastapi import HTTPException

from app.commands.handlers.tasks import (
    create_task_handler,
    delete_task_handler,
    get_task_handler,
    list_tasks_handler,
    update_task_handler,
)


@pytest.fixture
def mock_db():
    """Mock asyncpg database connection."""
    return AsyncMock()


@pytest.fixture
def sample_task_row():
    """Sample task row returned by asyncpg."""
    return {
        'id': UUID('550e8400-e29b-41d4-a716-446655440000'),
        'user_id': 'test-user-123',
        'title': 'Test Task',
        'description': None,
        'status': 'pending',
        'priority': None,
        'created_at': datetime(2025, 11, 12, 10, 0, 0, tzinfo=timezone.utc),
        'completed_at': None,
        'due_date': None
    }


# ============================================================================
# create_task_handler Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_task_handler_success(mock_db, sample_task_row):
    """Test successful task creation with valid payload."""
    # Arrange
    mock_db.fetchrow.return_value = sample_task_row
    payload = {"title": "Test Task"}

    # Act
    result = await create_task_handler("test-user-123", payload, mock_db)

    # Assert
    assert result["title"] == "Test Task"
    assert result["user_id"] == "test-user-123"
    assert result["status"] == "pending"
    assert result["id"] == "550e8400-e29b-41d4-a716-446655440000"
    assert "created_at" in result
    mock_db.fetchrow.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_task_handler_with_all_fields(mock_db):
    """Test task creation with all optional fields."""
    # Arrange
    task_row = {
        'id': UUID('550e8400-e29b-41d4-a716-446655440000'),
        'user_id': 'test-user-123',
        'title': 'Complete Task',
        'description': 'Full description',
        'status': 'in_progress',
        'priority': 'high',
        'created_at': datetime(2025, 11, 12, 10, 0, 0, tzinfo=timezone.utc),
        'completed_at': None,
        'due_date': datetime(2025, 11, 20, 10, 0, 0, tzinfo=timezone.utc)
    }
    mock_db.fetchrow.return_value = task_row
    payload = {
        "title": "Complete Task",
        "description": "Full description",
        "status": "in_progress",
        "priority": "high",
        "due_date": "2025-11-20T10:00:00Z"
    }

    # Act
    result = await create_task_handler("test-user-123", payload, mock_db)

    # Assert
    assert result["title"] == "Complete Task"
    assert result["description"] == "Full description"
    assert result["status"] == "in_progress"
    assert result["priority"] == "high"
    assert result["due_date"] == "2025-11-20T10:00:00Z"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_task_handler_missing_title(mock_db):
    """Test validation error with missing title."""
    # Arrange
    payload = {"description": "No title"}

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await create_task_handler("test-user-123", payload, mock_db)

    assert exc_info.value.status_code == 400
    assert "title" in str(exc_info.value.detail).lower()
    mock_db.fetchrow.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_task_handler_invalid_status(mock_db):
    """Test validation error with invalid status."""
    # Arrange
    payload = {"title": "Test", "status": "invalid_status"}

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await create_task_handler("test-user-123", payload, mock_db)

    assert exc_info.value.status_code == 400
    assert "status" in str(exc_info.value.detail).lower()
    mock_db.fetchrow.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_task_handler_invalid_priority(mock_db):
    """Test validation error with invalid priority."""
    # Arrange
    payload = {"title": "Test", "priority": "super_urgent"}

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await create_task_handler("test-user-123", payload, mock_db)

    assert exc_info.value.status_code == 400
    assert "priority" in str(exc_info.value.detail).lower()
    mock_db.fetchrow.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_task_handler_database_error(mock_db):
    """Test database error handling."""
    # Arrange
    mock_db.fetchrow.side_effect = Exception("Database connection failed")
    payload = {"title": "Test Task"}

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await create_task_handler("test-user-123", payload, mock_db)

    assert exc_info.value.status_code == 500
    assert "Internal server error" in exc_info.value.detail


# ============================================================================
# list_tasks_handler Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_tasks_handler_no_filter(mock_db):
    """Test list all tasks without status filter."""
    # Arrange
    task_rows = [
        {
            'id': UUID('550e8400-e29b-41d4-a716-446655440000'),
            'user_id': 'test-user-123',
            'title': 'Task 1',
            'description': None,
            'status': 'pending',
            'priority': None,
            'created_at': datetime(2025, 11, 12, 10, 0, 0, tzinfo=timezone.utc),
            'completed_at': None,
            'due_date': None
        },
        {
            'id': UUID('660e8400-e29b-41d4-a716-446655440001'),
            'user_id': 'test-user-123',
            'title': 'Task 2',
            'description': None,
            'status': 'in_progress',
            'priority': 'high',
            'created_at': datetime(2025, 11, 12, 11, 0, 0, tzinfo=timezone.utc),
            'completed_at': None,
            'due_date': None
        }
    ]
    mock_db.fetch.return_value = task_rows
    payload = {}

    # Act
    result = await list_tasks_handler("test-user-123", payload, mock_db)

    # Assert
    assert result["count"] == 2
    assert len(result["tasks"]) == 2
    assert result["tasks"][0]["title"] == "Task 1"
    assert result["tasks"][1]["title"] == "Task 2"
    mock_db.fetch.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_tasks_handler_with_status_filter(mock_db):
    """Test list tasks with status filter."""
    # Arrange
    task_rows = [
        {
            'id': UUID('550e8400-e29b-41d4-a716-446655440000'),
            'user_id': 'test-user-123',
            'title': 'Pending Task',
            'description': None,
            'status': 'pending',
            'priority': None,
            'created_at': datetime(2025, 11, 12, 10, 0, 0, tzinfo=timezone.utc),
            'completed_at': None,
            'due_date': None
        }
    ]
    mock_db.fetch.return_value = task_rows
    payload = {"status": "pending"}

    # Act
    result = await list_tasks_handler("test-user-123", payload, mock_db)

    # Assert
    assert result["count"] == 1
    assert len(result["tasks"]) == 1
    assert result["tasks"][0]["status"] == "pending"
    mock_db.fetch.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_tasks_handler_empty_result(mock_db):
    """Test list tasks when user has no tasks."""
    # Arrange
    mock_db.fetch.return_value = []
    payload = {}

    # Act
    result = await list_tasks_handler("test-user-123", payload, mock_db)

    # Assert
    assert result["count"] == 0
    assert result["tasks"] == []
    mock_db.fetch.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_tasks_handler_database_error(mock_db):
    """Test database error handling in list operation."""
    # Arrange
    mock_db.fetch.side_effect = Exception("Database connection failed")
    payload = {}

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await list_tasks_handler("test-user-123", payload, mock_db)

    assert exc_info.value.status_code == 500
    assert "Internal server error" in exc_info.value.detail


# ============================================================================
# get_task_handler Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_task_handler_success(mock_db, sample_task_row):
    """Test successful task retrieval with valid task_id."""
    # Arrange
    mock_db.fetchrow.return_value = sample_task_row
    payload = {"task_id": "550e8400-e29b-41d4-a716-446655440000"}

    # Act
    result = await get_task_handler("test-user-123", payload, mock_db)

    # Assert
    assert result["id"] == "550e8400-e29b-41d4-a716-446655440000"
    assert result["title"] == "Test Task"
    assert result["user_id"] == "test-user-123"
    assert "created_at" in result
    mock_db.fetchrow.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_task_handler_missing_task_id(mock_db):
    """Test missing task_id in payload returns 400."""
    # Arrange
    payload = {}

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await get_task_handler("test-user-123", payload, mock_db)

    assert exc_info.value.status_code == 400
    assert "Missing required field: task_id" in exc_info.value.detail
    mock_db.fetchrow.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_task_handler_invalid_uuid_format(mock_db):
    """Test invalid UUID format returns 400."""
    # Arrange
    payload = {"task_id": "not-a-valid-uuid"}

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await get_task_handler("test-user-123", payload, mock_db)

    assert exc_info.value.status_code == 400
    assert "Invalid UUID format for task_id" in exc_info.value.detail
    mock_db.fetchrow.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_task_handler_task_not_found(mock_db):
    """Test task not found returns 404."""
    # Arrange
    mock_db.fetchrow.return_value = None
    payload = {"task_id": "550e8400-e29b-41d4-a716-446655440000"}

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await get_task_handler("test-user-123", payload, mock_db)

    assert exc_info.value.status_code == 404
    assert "Task not found" in exc_info.value.detail
    mock_db.fetchrow.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_task_handler_database_error(mock_db):
    """Test database error handling returns 500."""
    # Arrange
    mock_db.fetchrow.side_effect = Exception("Database connection failed")
    payload = {"task_id": "550e8400-e29b-41d4-a716-446655440000"}

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await get_task_handler("test-user-123", payload, mock_db)

    assert exc_info.value.status_code == 500
    assert "Internal server error" in exc_info.value.detail


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_task_handler_returns_all_fields(mock_db):
    """Test that all task fields are returned."""
    # Arrange
    complete_task_row = {
        'id': UUID('550e8400-e29b-41d4-a716-446655440000'),
        'user_id': 'test-user-123',
        'title': 'Complete Task',
        'description': 'Full description',
        'status': 'completed',
        'priority': 'high',
        'created_at': datetime(2025, 11, 12, 10, 0, 0, tzinfo=timezone.utc),
        'completed_at': datetime(2025, 11, 12, 15, 0, 0, tzinfo=timezone.utc),
        'due_date': datetime(2025, 11, 20, 10, 0, 0, tzinfo=timezone.utc)
    }
    mock_db.fetchrow.return_value = complete_task_row
    payload = {"task_id": "550e8400-e29b-41d4-a716-446655440000"}

    # Act
    result = await get_task_handler("test-user-123", payload, mock_db)

    # Assert
    assert result["id"] == "550e8400-e29b-41d4-a716-446655440000"
    assert result["user_id"] == "test-user-123"
    assert result["title"] == "Complete Task"
    assert result["description"] == "Full description"
    assert result["status"] == "completed"
    assert result["priority"] == "high"
    assert result["completed_at"] is not None
    assert result["due_date"] is not None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_task_handler_with_null_fields(mock_db):
    """Test task retrieval with null optional fields."""
    # Arrange
    minimal_task_row = {
        'id': UUID('550e8400-e29b-41d4-a716-446655440000'),
        'user_id': 'test-user-123',
        'title': 'Minimal Task',
        'description': None,
        'status': 'pending',
        'priority': None,
        'created_at': datetime(2025, 11, 12, 10, 0, 0, tzinfo=timezone.utc),
        'completed_at': None,
        'due_date': None
    }
    mock_db.fetchrow.return_value = minimal_task_row
    payload = {"task_id": "550e8400-e29b-41d4-a716-446655440000"}

    # Act
    result = await get_task_handler("test-user-123", payload, mock_db)

    # Assert
    assert result["description"] is None
    assert result["priority"] is None
    assert result["completed_at"] is None
    assert result["due_date"] is None


# ============================================================================
# update_task_handler Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_task_handler_partial_update_title_only(mock_db):
    """Test successful partial update with only title."""
    # Arrange
    updated_task_row = {
        'id': UUID('550e8400-e29b-41d4-a716-446655440000'),
        'user_id': 'test-user-123',
        'title': 'Updated Title',
        'description': None,
        'status': 'pending',
        'priority': None,
        'created_at': datetime(2025, 11, 12, 10, 0, 0, tzinfo=timezone.utc),
        'completed_at': None,
        'due_date': None
    }
    mock_db.fetchrow.return_value = updated_task_row
    payload = {
        "task_id": "550e8400-e29b-41d4-a716-446655440000",
        "title": "Updated Title"
    }

    # Act
    result = await update_task_handler("test-user-123", payload, mock_db)

    # Assert
    assert result["title"] == "Updated Title"
    assert result["status"] == "pending"  # Unchanged
    mock_db.fetchrow.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_task_handler_multiple_fields(mock_db):
    """Test successful update with multiple fields."""
    # Arrange
    updated_task_row = {
        'id': UUID('550e8400-e29b-41d4-a716-446655440000'),
        'user_id': 'test-user-123',
        'title': 'Updated Title',
        'description': 'Updated description',
        'status': 'in_progress',
        'priority': 'high',
        'created_at': datetime(2025, 11, 12, 10, 0, 0, tzinfo=timezone.utc),
        'completed_at': None,
        'due_date': datetime(2025, 11, 20, 10, 0, 0, tzinfo=timezone.utc)
    }
    mock_db.fetchrow.return_value = updated_task_row
    payload = {
        "task_id": "550e8400-e29b-41d4-a716-446655440000",
        "title": "Updated Title",
        "description": "Updated description",
        "status": "in_progress",
        "priority": "high",
        "due_date": "2025-11-20T10:00:00Z"
    }

    # Act
    result = await update_task_handler("test-user-123", payload, mock_db)

    # Assert
    assert result["title"] == "Updated Title"
    assert result["description"] == "Updated description"
    assert result["status"] == "in_progress"
    assert result["priority"] == "high"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_task_handler_status_to_completed_sets_completed_at(mock_db):
    """Test status change to 'completed' sets completed_at timestamp."""
    # Arrange
    updated_task_row = {
        'id': UUID('550e8400-e29b-41d4-a716-446655440000'),
        'user_id': 'test-user-123',
        'title': 'Test Task',
        'description': None,
        'status': 'completed',
        'priority': None,
        'created_at': datetime(2025, 11, 12, 10, 0, 0, tzinfo=timezone.utc),
        'completed_at': datetime(2025, 11, 12, 15, 30, 0, tzinfo=timezone.utc),
        'due_date': None
    }
    mock_db.fetchrow.return_value = updated_task_row
    payload = {
        "task_id": "550e8400-e29b-41d4-a716-446655440000",
        "status": "completed"
    }

    # Act
    result = await update_task_handler("test-user-123", payload, mock_db)

    # Assert
    assert result["status"] == "completed"
    assert result["completed_at"] is not None
    # Verify SQL includes completed_at = NOW()
    call_args = mock_db.fetchrow.call_args
    assert "completed_at = NOW()" in call_args[0][0]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_task_handler_status_to_pending_clears_completed_at(mock_db):
    """Test status change to non-completed clears completed_at."""
    # Arrange
    updated_task_row = {
        'id': UUID('550e8400-e29b-41d4-a716-446655440000'),
        'user_id': 'test-user-123',
        'title': 'Test Task',
        'description': None,
        'status': 'pending',
        'priority': None,
        'created_at': datetime(2025, 11, 12, 10, 0, 0, tzinfo=timezone.utc),
        'completed_at': None,
        'due_date': None
    }
    mock_db.fetchrow.return_value = updated_task_row
    payload = {
        "task_id": "550e8400-e29b-41d4-a716-446655440000",
        "status": "pending"
    }

    # Act
    result = await update_task_handler("test-user-123", payload, mock_db)

    # Assert
    assert result["status"] == "pending"
    assert result["completed_at"] is None
    # Verify SQL includes completed_at = NULL
    call_args = mock_db.fetchrow.call_args
    assert "completed_at = NULL" in call_args[0][0]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_task_handler_without_status_leaves_completed_at_unchanged(mock_db):
    """Test update without status field leaves completed_at unchanged."""
    # Arrange
    updated_task_row = {
        'id': UUID('550e8400-e29b-41d4-a716-446655440000'),
        'user_id': 'test-user-123',
        'title': 'Updated Title',
        'description': None,
        'status': 'in_progress',
        'priority': 'high',
        'created_at': datetime(2025, 11, 12, 10, 0, 0, tzinfo=timezone.utc),
        'completed_at': None,
        'due_date': None
    }
    mock_db.fetchrow.return_value = updated_task_row
    payload = {
        "task_id": "550e8400-e29b-41d4-a716-446655440000",
        "title": "Updated Title",
        "priority": "high"
    }

    # Act
    result = await update_task_handler("test-user-123", payload, mock_db)

    # Assert - completed_at should remain unchanged (not in SQL)
    call_args = mock_db.fetchrow.call_args
    assert "completed_at" not in call_args[0][0]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_task_handler_missing_task_id(mock_db):
    """Test missing task_id returns 400."""
    # Arrange
    payload = {"title": "New Title"}

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await update_task_handler("test-user-123", payload, mock_db)

    assert exc_info.value.status_code == 400
    assert "Missing required field: task_id" in exc_info.value.detail
    mock_db.fetchrow.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_task_handler_invalid_task_id_format(mock_db):
    """Test invalid task_id format returns 400."""
    # Arrange
    payload = {"task_id": "invalid-uuid", "title": "New Title"}

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await update_task_handler("test-user-123", payload, mock_db)

    assert exc_info.value.status_code == 400
    assert "Invalid UUID format for task_id" in exc_info.value.detail
    mock_db.fetchrow.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_task_handler_no_fields_provided(mock_db):
    """Test no update fields provided returns 400."""
    # Arrange
    payload = {"task_id": "550e8400-e29b-41d4-a716-446655440000"}

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await update_task_handler("test-user-123", payload, mock_db)

    assert exc_info.value.status_code == 400
    assert "No fields provided for update" in exc_info.value.detail
    mock_db.fetchrow.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_task_handler_invalid_field_values(mock_db):
    """Test invalid field values return 400 with ValidationError."""
    # Arrange
    payload = {
        "task_id": "550e8400-e29b-41d4-a716-446655440000",
        "status": "invalid_status"
    }

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await update_task_handler("test-user-123", payload, mock_db)

    assert exc_info.value.status_code == 400
    assert "status" in str(exc_info.value.detail).lower()
    mock_db.fetchrow.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_task_handler_task_not_found(mock_db):
    """Test task not found returns 404."""
    # Arrange
    mock_db.fetchrow.return_value = None
    payload = {
        "task_id": "550e8400-e29b-41d4-a716-446655440000",
        "title": "Updated Title"
    }

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await update_task_handler("test-user-123", payload, mock_db)

    assert exc_info.value.status_code == 404
    assert "Task not found" in exc_info.value.detail


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_task_handler_database_error(mock_db):
    """Test database error handling returns 500."""
    # Arrange
    mock_db.fetchrow.side_effect = Exception("Database connection failed")
    payload = {
        "task_id": "550e8400-e29b-41d4-a716-446655440000",
        "title": "Updated Title"
    }

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await update_task_handler("test-user-123", payload, mock_db)

    assert exc_info.value.status_code == 500
    assert "Internal server error" in exc_info.value.detail


# ============================================================================
# delete_task_handler Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_task_handler_success(mock_db):
    """Test successful task deletion."""
    # Arrange
    mock_db.fetchrow.return_value = {'id': UUID('550e8400-e29b-41d4-a716-446655440000')}
    payload = {"task_id": "550e8400-e29b-41d4-a716-446655440000"}

    # Act
    result = await delete_task_handler("test-user-123", payload, mock_db)

    # Assert
    assert result["success"] is True
    assert result["deleted_id"] == "550e8400-e29b-41d4-a716-446655440000"
    mock_db.fetchrow.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_task_handler_missing_task_id(mock_db):
    """Test missing task_id returns 400."""
    # Arrange
    payload = {}

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await delete_task_handler("test-user-123", payload, mock_db)

    assert exc_info.value.status_code == 400
    assert "Missing required field: task_id" in exc_info.value.detail
    mock_db.fetchrow.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_task_handler_invalid_task_id_format(mock_db):
    """Test invalid task_id format returns 400."""
    # Arrange
    payload = {"task_id": "not-a-valid-uuid"}

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await delete_task_handler("test-user-123", payload, mock_db)

    assert exc_info.value.status_code == 400
    assert "Invalid UUID format for task_id" in exc_info.value.detail
    mock_db.fetchrow.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_task_handler_task_not_found(mock_db):
    """Test task not found returns 404."""
    # Arrange
    mock_db.fetchrow.return_value = None
    payload = {"task_id": "550e8400-e29b-41d4-a716-446655440000"}

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await delete_task_handler("test-user-123", payload, mock_db)

    assert exc_info.value.status_code == 404
    assert "Task not found" in exc_info.value.detail
    mock_db.fetchrow.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_task_handler_database_error(mock_db):
    """Test database error handling returns 500."""
    # Arrange
    mock_db.fetchrow.side_effect = Exception("Database connection failed")
    payload = {"task_id": "550e8400-e29b-41d4-a716-446655440000"}

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await delete_task_handler("test-user-123", payload, mock_db)

    assert exc_info.value.status_code == 500
    assert "Internal server error" in exc_info.value.detail


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_task_handler_response_format(mock_db):
    """Test delete response has correct format with success and deleted_id."""
    # Arrange
    task_id = "550e8400-e29b-41d4-a716-446655440000"
    mock_db.fetchrow.return_value = {'id': UUID(task_id)}
    payload = {"task_id": task_id}

    # Act
    result = await delete_task_handler("test-user-123", payload, mock_db)

    # Assert
    assert isinstance(result, dict)
    assert "success" in result
    assert "deleted_id" in result
    assert result["success"] is True
    assert result["deleted_id"] == task_id
