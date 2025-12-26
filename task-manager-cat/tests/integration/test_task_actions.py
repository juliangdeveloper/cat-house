"""
Integration tests for task command actions.

Tests end-to-end task operations through POST /execute endpoint:
- create-task action with validation
- list-tasks action with filtering
- CommandResponse wrapping
- Database persistence

Uses real database and HTTP client from conftest.py fixtures.
"""

import pytest
from httpx import AsyncClient

# ============================================================================
# create-task Action Tests
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_task_success(client: AsyncClient, test_service_key: str, test_db):
    """Test successful task creation via create-task action."""
    # Arrange
    payload = {
        "action": "create-task",
        "user_id": "test-user-123",
        "payload": {
            "title": "Buy milk",
            "priority": "high"
        }
    }

    # Act
    response = await client.post(
        "/execute",
        headers={"X-Service-Key": test_service_key},
        json=payload
    )

    # Assert - Response structure
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["error"] is None
    assert "timestamp" in data

    # Assert - Task data
    task = data["data"]
    assert task["title"] == "Buy milk"
    assert task["priority"] == "high"
    assert task["user_id"] == "test-user-123"
    assert task["status"] == "pending"
    assert "id" in task
    assert "created_at" in task

    # Assert - Database persistence
    row = await test_db.fetchrow(
        "SELECT * FROM tasks WHERE user_id = 'test-user-123'"
    )
    assert row is not None
    assert row["title"] == "Buy milk"
    assert row["priority"] == "high"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_task_with_all_fields(client: AsyncClient, test_service_key: str, test_db):
    """Test task creation with all optional fields."""
    # Arrange
    payload = {
        "action": "create-task",
        "user_id": "test-user-456",
        "payload": {
            "title": "Complete project",
            "description": "Finish the MVP implementation",
            "status": "in_progress",
            "priority": "urgent",
            "due_date": "2025-11-20T10:00:00Z"
        }
    }

    # Act
    response = await client.post(
        "/execute",
        headers={"X-Service-Key": test_service_key},
        json=payload
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

    task = data["data"]
    assert task["title"] == "Complete project"
    assert task["description"] == "Finish the MVP implementation"
    assert task["status"] == "in_progress"
    assert task["priority"] == "urgent"
    assert task["due_date"] == "2025-11-20T10:00:00Z"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_task_missing_title(client: AsyncClient, test_service_key: str, test_db):
    """Test validation error when title is missing."""
    # Arrange
    payload = {
        "action": "create-task",
        "user_id": "test-user-789",
        "payload": {
            "description": "No title provided"
        }
    }

    # Act
    response = await client.post(
        "/execute",
        headers={"X-Service-Key": test_service_key},
        json=payload
    )

    # Assert
    assert response.status_code == 400
    data = response.json()
    assert "title" in data["detail"].lower()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_task_invalid_status(client: AsyncClient, test_service_key: str, test_db):
    """Test validation error with invalid status."""
    # Arrange
    payload = {
        "action": "create-task",
        "user_id": "test-user-999",
        "payload": {
            "title": "Test task",
            "status": "invalid_status"
        }
    }

    # Act
    response = await client.post(
        "/execute",
        headers={"X-Service-Key": test_service_key},
        json=payload
    )

    # Assert
    assert response.status_code == 400
    data = response.json()
    assert "status" in data["detail"].lower()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_task_invalid_priority(client: AsyncClient, test_service_key: str, test_db):
    """Test validation error with invalid priority."""
    # Arrange
    payload = {
        "action": "create-task",
        "user_id": "test-user-888",
        "payload": {
            "title": "Test task",
            "priority": "super_urgent"
        }
    }

    # Act
    response = await client.post(
        "/execute",
        headers={"X-Service-Key": test_service_key},
        json=payload
    )

    # Assert
    assert response.status_code == 400
    data = response.json()
    assert "priority" in data["detail"].lower()


# ============================================================================
# list-tasks Action Tests
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_tasks_no_filter(client: AsyncClient, test_service_key: str, test_db):
    """Test listing all tasks without status filter."""
    # Arrange - Create test tasks
    await test_db.execute(
        """
        INSERT INTO tasks (user_id, title, status, priority)
        VALUES 
            ('test-user-list-1', 'Task 1', 'pending', 'low'),
            ('test-user-list-1', 'Task 2', 'in_progress', 'high'),
            ('test-user-list-1', 'Task 3', 'completed', 'medium')
        """
    )

    payload = {
        "action": "list-tasks",
        "user_id": "test-user-list-1",
        "payload": {}
    }

    # Act
    response = await client.post(
        "/execute",
        headers={"X-Service-Key": test_service_key},
        json=payload
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

    result = data["data"]
    assert result["count"] == 3
    assert len(result["tasks"]) == 3

    # Verify all tasks belong to user
    for task in result["tasks"]:
        assert task["user_id"] == "test-user-list-1"

    # Verify all task titles are present (order may vary with same timestamp)
    task_titles = {task["title"] for task in result["tasks"]}
    assert task_titles == {"Task 1", "Task 2", "Task 3"}


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_tasks_with_status_filter(client: AsyncClient, test_service_key: str, test_db):
    """Test listing tasks with status filter."""
    # Arrange - Create test tasks
    await test_db.execute(
        """
        INSERT INTO tasks (user_id, title, status, priority)
        VALUES 
            ('test-user-list-2', 'Pending 1', 'pending', 'low'),
            ('test-user-list-2', 'In Progress', 'in_progress', 'high'),
            ('test-user-list-2', 'Pending 2', 'pending', 'medium')
        """
    )

    payload = {
        "action": "list-tasks",
        "user_id": "test-user-list-2",
        "payload": {"status": "pending"}
    }

    # Act
    response = await client.post(
        "/execute",
        headers={"X-Service-Key": test_service_key},
        json=payload
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

    result = data["data"]
    assert result["count"] == 2
    assert len(result["tasks"]) == 2

    # Verify only pending tasks returned
    for task in result["tasks"]:
        assert task["status"] == "pending"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_tasks_empty_result(client: AsyncClient, test_service_key: str, test_db):
    """Test listing tasks when user has no tasks."""
    # Arrange
    payload = {
        "action": "list-tasks",
        "user_id": "test-user-empty",
        "payload": {}
    }

    # Act
    response = await client.post(
        "/execute",
        headers={"X-Service-Key": test_service_key},
        json=payload
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

    result = data["data"]
    assert result["count"] == 0
    assert result["tasks"] == []


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_tasks_user_scoping(client: AsyncClient, test_service_key: str, test_db):
    """Test that users can only see their own tasks."""
    # Arrange - Create tasks for two different users
    await test_db.execute(
        """
        INSERT INTO tasks (user_id, title, status)
        VALUES 
            ('test-user-alice', 'Alice Task 1', 'pending'),
            ('test-user-alice', 'Alice Task 2', 'in_progress'),
            ('test-user-bob', 'Bob Task 1', 'pending')
        """
    )

    payload = {
        "action": "list-tasks",
        "user_id": "test-user-alice",
        "payload": {}
    }

    # Act
    response = await client.post(
        "/execute",
        headers={"X-Service-Key": test_service_key},
        json=payload
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

    result = data["data"]
    assert result["count"] == 2  # Only Alice's tasks

    # Verify all tasks belong to Alice
    for task in result["tasks"]:
        assert task["user_id"] == "test-user-alice"
        assert "Alice" in task["title"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_tasks_with_completed_status(client: AsyncClient, test_service_key: str, test_db):
    """Test listing only completed tasks."""
    # Arrange - Create tasks with different statuses
    await test_db.execute(
        """
        INSERT INTO tasks (user_id, title, status)
        VALUES 
            ('test-user-filter', 'Pending Task', 'pending'),
            ('test-user-filter', 'Completed Task 1', 'completed'),
            ('test-user-filter', 'In Progress Task', 'in_progress'),
            ('test-user-filter', 'Completed Task 2', 'completed')
        """
    )

    payload = {
        "action": "list-tasks",
        "user_id": "test-user-filter",
        "payload": {"status": "completed"}
    }

    # Act
    response = await client.post(
        "/execute",
        headers={"X-Service-Key": test_service_key},
        json=payload
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

    result = data["data"]
    assert result["count"] == 2

    # Verify only completed tasks returned
    for task in result["tasks"]:
        assert task["status"] == "completed"
        assert "Completed" in task["title"]


# ============================================================================
# get-task Action Tests
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_task_success(client: AsyncClient, test_service_key: str, test_db):
    """Test successful task retrieval via get-task action."""
    # Arrange - Create a test task
    row = await test_db.fetchrow(
        """
        INSERT INTO tasks (user_id, title, description, status, priority)
        VALUES ('test-user-get', 'Get Task Test', 'Test description', 'in_progress', 'high')
        RETURNING id
        """
    )
    task_id = str(row["id"])

    payload = {
        "action": "get-task",
        "user_id": "test-user-get",
        "payload": {"task_id": task_id}
    }

    # Act
    response = await client.post(
        "/execute",
        headers={"X-Service-Key": test_service_key},
        json=payload
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

    task = data["data"]
    assert task["id"] == task_id
    assert task["title"] == "Get Task Test"
    assert task["description"] == "Test description"
    assert task["status"] == "in_progress"
    assert task["priority"] == "high"
    assert task["user_id"] == "test-user-get"
    assert "created_at" in task
    assert task["completed_at"] is None


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_task_nonexistent(client: AsyncClient, test_service_key: str, test_db):
    """Test get-task with non-existent task ID returns 404."""
    # Arrange
    payload = {
        "action": "get-task",
        "user_id": "test-user-get",
        "payload": {"task_id": "550e8400-e29b-41d4-a716-446655440000"}
    }

    # Act
    response = await client.post(
        "/execute",
        headers={"X-Service-Key": test_service_key},
        json=payload
    )

    # Assert
    assert response.status_code == 404
    data = response.json()
    assert "Task not found" in data["detail"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_task_invalid_uuid(client: AsyncClient, test_service_key: str, test_db):
    """Test get-task with invalid UUID format returns 400."""
    # Arrange
    payload = {
        "action": "get-task",
        "user_id": "test-user-get",
        "payload": {"task_id": "invalid-uuid-format"}
    }

    # Act
    response = await client.post(
        "/execute",
        headers={"X-Service-Key": test_service_key},
        json=payload
    )

    # Assert
    assert response.status_code == 400
    data = response.json()
    assert "Invalid UUID format" in data["detail"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_task_missing_task_id(client: AsyncClient, test_service_key: str, test_db):
    """Test get-task with missing task_id returns 400."""
    # Arrange
    payload = {
        "action": "get-task",
        "user_id": "test-user-get",
        "payload": {}
    }

    # Act
    response = await client.post(
        "/execute",
        headers={"X-Service-Key": test_service_key},
        json=payload
    )

    # Assert
    assert response.status_code == 400
    data = response.json()
    assert "Missing required field: task_id" in data["detail"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_task_with_all_fields(client: AsyncClient, test_service_key: str, test_db):
    """Test get-task returns all fields including completed_at."""
    # Arrange - Create a completed task
    row = await test_db.fetchrow(
        """
        INSERT INTO tasks (
            user_id, title, description, status, priority, due_date, completed_at
        )
        VALUES (
            'test-user-get-complete',
            'Completed Task',
            'Full description',
            'completed',
            'urgent',
            '2025-11-20T10:00:00Z',
            NOW()
        )
        RETURNING id
        """
    )
    task_id = str(row["id"])

    payload = {
        "action": "get-task",
        "user_id": "test-user-get-complete",
        "payload": {"task_id": task_id}
    }

    # Act
    response = await client.post(
        "/execute",
        headers={"X-Service-Key": test_service_key},
        json=payload
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    task = data["data"]

    assert task["title"] == "Completed Task"
    assert task["description"] == "Full description"
    assert task["status"] == "completed"
    assert task["priority"] == "urgent"
    assert task["due_date"] is not None
    assert task["completed_at"] is not None


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_task_no_user_ownership_check(client: AsyncClient, test_service_key: str, test_db):
    """Test get-task does not check user ownership (trusts Cat House)."""
    # Arrange - Create task for user-A
    row = await test_db.fetchrow(
        """
        INSERT INTO tasks (user_id, title, status)
        VALUES ('test-user-alice', 'Alice Task', 'pending')
        RETURNING id
        """
    )
    task_id = str(row["id"])

    # Act - Request as user-B (different user)
    payload = {
        "action": "get-task",
        "user_id": "test-user-bob",  # Different user
        "payload": {"task_id": task_id}
    }

    response = await client.post(
        "/execute",
        headers={"X-Service-Key": test_service_key},
        json=payload
    )

    # Assert - Should succeed (no ownership check)
    assert response.status_code == 200
    data = response.json()
    task = data["data"]
    assert task["id"] == task_id
    assert task["user_id"] == "test-user-alice"


# ============================================================================
# update-task Action Tests
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
async def test_update_task_partial_update_title_only(client: AsyncClient, test_service_key: str, test_db):
    """Test partial update with only title field."""
    # Arrange - Create test task
    row = await test_db.fetchrow(
        """
        INSERT INTO tasks (user_id, title, description, status, priority)
        VALUES ('test-user-update', 'Original Title', 'Description', 'pending', 'low')
        RETURNING id
        """
    )
    task_id = str(row["id"])

    payload = {
        "action": "update-task",
        "user_id": "test-user-update",
        "payload": {
            "task_id": task_id,
            "title": "Updated Title"
        }
    }

    # Act
    response = await client.post(
        "/execute",
        headers={"X-Service-Key": test_service_key},
        json=payload
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    task = data["data"]

    assert task["title"] == "Updated Title"
    assert task["description"] == "Description"  # Unchanged
    assert task["status"] == "pending"  # Unchanged
    assert task["priority"] == "low"  # Unchanged


@pytest.mark.asyncio
@pytest.mark.integration
async def test_update_task_multiple_fields(client: AsyncClient, test_service_key: str, test_db):
    """Test update with multiple fields."""
    # Arrange - Create test task
    row = await test_db.fetchrow(
        """
        INSERT INTO tasks (user_id, title, status, priority)
        VALUES ('test-user-update-multi', 'Original', 'pending', 'low')
        RETURNING id
        """
    )
    task_id = str(row["id"])

    payload = {
        "action": "update-task",
        "user_id": "test-user-update-multi",
        "payload": {
            "task_id": task_id,
            "title": "Updated Title",
            "description": "New description",
            "status": "in_progress",
            "priority": "high"
        }
    }

    # Act
    response = await client.post(
        "/execute",
        headers={"X-Service-Key": test_service_key},
        json=payload
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    task = data["data"]

    assert task["title"] == "Updated Title"
    assert task["description"] == "New description"
    assert task["status"] == "in_progress"
    assert task["priority"] == "high"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_update_task_status_to_completed_sets_completed_at(client: AsyncClient, test_service_key: str, test_db):
    """Test status change to 'completed' automatically sets completed_at."""
    # Arrange - Create pending task
    row = await test_db.fetchrow(
        """
        INSERT INTO tasks (user_id, title, status)
        VALUES ('test-user-complete', 'Task To Complete', 'pending')
        RETURNING id
        """
    )
    task_id = str(row["id"])

    payload = {
        "action": "update-task",
        "user_id": "test-user-complete",
        "payload": {
            "task_id": task_id,
            "status": "completed"
        }
    }

    # Act
    response = await client.post(
        "/execute",
        headers={"X-Service-Key": test_service_key},
        json=payload
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    task = data["data"]

    assert task["status"] == "completed"
    assert task["completed_at"] is not None

    # Verify in database
    db_row = await test_db.fetchrow(
        "SELECT completed_at FROM tasks WHERE id = $1",
        row["id"]
    )
    assert db_row["completed_at"] is not None


@pytest.mark.asyncio
@pytest.mark.integration
async def test_update_task_status_to_pending_clears_completed_at(client: AsyncClient, test_service_key: str, test_db):
    """Test status change to non-completed clears completed_at."""
    # Arrange - Create completed task
    row = await test_db.fetchrow(
        """
        INSERT INTO tasks (user_id, title, status, completed_at)
        VALUES ('test-user-uncomplete', 'Task To Reopen', 'completed', NOW())
        RETURNING id
        """
    )
    task_id = str(row["id"])

    payload = {
        "action": "update-task",
        "user_id": "test-user-uncomplete",
        "payload": {
            "task_id": task_id,
            "status": "in_progress"
        }
    }

    # Act
    response = await client.post(
        "/execute",
        headers={"X-Service-Key": test_service_key},
        json=payload
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    task = data["data"]

    assert task["status"] == "in_progress"
    assert task["completed_at"] is None

    # Verify in database
    db_row = await test_db.fetchrow(
        "SELECT completed_at FROM tasks WHERE id = $1",
        row["id"]
    )
    assert db_row["completed_at"] is None


@pytest.mark.asyncio
@pytest.mark.integration
async def test_update_task_nonexistent(client: AsyncClient, test_service_key: str, test_db):
    """Test update non-existent task returns 404."""
    # Arrange
    payload = {
        "action": "update-task",
        "user_id": "test-user-update",
        "payload": {
            "task_id": "550e8400-e29b-41d4-a716-446655440000",
            "title": "Updated Title"
        }
    }

    # Act
    response = await client.post(
        "/execute",
        headers={"X-Service-Key": test_service_key},
        json=payload
    )

    # Assert
    assert response.status_code == 404
    data = response.json()
    assert "Task not found" in data["detail"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_update_task_invalid_task_id(client: AsyncClient, test_service_key: str, test_db):
    """Test update with invalid task_id returns 400."""
    # Arrange
    payload = {
        "action": "update-task",
        "user_id": "test-user-update",
        "payload": {
            "task_id": "invalid-uuid",
            "title": "Updated Title"
        }
    }

    # Act
    response = await client.post(
        "/execute",
        headers={"X-Service-Key": test_service_key},
        json=payload
    )

    # Assert
    assert response.status_code == 400
    data = response.json()
    assert "Invalid UUID format" in data["detail"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_update_task_no_fields(client: AsyncClient, test_service_key: str, test_db):
    """Test update with no fields returns 400."""
    # Arrange - Create task
    row = await test_db.fetchrow(
        """
        INSERT INTO tasks (user_id, title, status)
        VALUES ('test-user-update', 'Task', 'pending')
        RETURNING id
        """
    )
    task_id = str(row["id"])

    payload = {
        "action": "update-task",
        "user_id": "test-user-update",
        "payload": {
            "task_id": task_id
        }
    }

    # Act
    response = await client.post(
        "/execute",
        headers={"X-Service-Key": test_service_key},
        json=payload
    )

    # Assert
    assert response.status_code == 400
    data = response.json()
    assert "No fields provided for update" in data["detail"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_update_task_invalid_field_values(client: AsyncClient, test_service_key: str, test_db):
    """Test update with invalid field values returns 400."""
    # Arrange - Create task
    row = await test_db.fetchrow(
        """
        INSERT INTO tasks (user_id, title, status)
        VALUES ('test-user-update', 'Task', 'pending')
        RETURNING id
        """
    )
    task_id = str(row["id"])

    payload = {
        "action": "update-task",
        "user_id": "test-user-update",
        "payload": {
            "task_id": task_id,
            "status": "invalid_status"
        }
    }

    # Act
    response = await client.post(
        "/execute",
        headers={"X-Service-Key": test_service_key},
        json=payload
    )

    # Assert
    assert response.status_code == 400
    data = response.json()
    assert "status" in data["detail"].lower()


# ============================================================================
# delete-task Action Tests
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_task_success(client: AsyncClient, test_service_key: str, test_db):
    """Test successful task deletion via delete-task action."""
    # Arrange - Create test task
    row = await test_db.fetchrow(
        """
        INSERT INTO tasks (user_id, title, status)
        VALUES ('test-user-delete', 'Task To Delete', 'pending')
        RETURNING id
        """
    )
    task_id = str(row["id"])

    payload = {
        "action": "delete-task",
        "user_id": "test-user-delete",
        "payload": {"task_id": task_id}
    }

    # Act
    response = await client.post(
        "/execute",
        headers={"X-Service-Key": test_service_key},
        json=payload
    )

    # Assert - Response
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

    result = data["data"]
    assert result["success"] is True
    assert result["deleted_id"] == task_id

    # Assert - Task deleted from database
    db_row = await test_db.fetchrow(
        "SELECT * FROM tasks WHERE id = $1",
        row["id"]
    )
    assert db_row is None


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_task_verify_cannot_get_after_delete(client: AsyncClient, test_service_key: str, test_db):
    """Test deleted task cannot be retrieved."""
    # Arrange - Create and delete task
    row = await test_db.fetchrow(
        """
        INSERT INTO tasks (user_id, title, status)
        VALUES ('test-user-delete', 'Task', 'pending')
        RETURNING id
        """
    )
    task_id = str(row["id"])

    # Delete task
    delete_payload = {
        "action": "delete-task",
        "user_id": "test-user-delete",
        "payload": {"task_id": task_id}
    }
    await client.post(
        "/execute",
        headers={"X-Service-Key": test_service_key},
        json=delete_payload
    )

    # Act - Try to get deleted task
    get_payload = {
        "action": "get-task",
        "user_id": "test-user-delete",
        "payload": {"task_id": task_id}
    }
    response = await client.post(
        "/execute",
        headers={"X-Service-Key": test_service_key},
        json=get_payload
    )

    # Assert
    assert response.status_code == 404
    data = response.json()
    assert "Task not found" in data["detail"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_task_nonexistent(client: AsyncClient, test_service_key: str, test_db):
    """Test delete non-existent task returns 404."""
    # Arrange
    payload = {
        "action": "delete-task",
        "user_id": "test-user-delete",
        "payload": {"task_id": "550e8400-e29b-41d4-a716-446655440000"}
    }

    # Act
    response = await client.post(
        "/execute",
        headers={"X-Service-Key": test_service_key},
        json=payload
    )

    # Assert
    assert response.status_code == 404
    data = response.json()
    assert "Task not found" in data["detail"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_task_invalid_task_id(client: AsyncClient, test_service_key: str, test_db):
    """Test delete with invalid task_id returns 400."""
    # Arrange
    payload = {
        "action": "delete-task",
        "user_id": "test-user-delete",
        "payload": {"task_id": "invalid-uuid"}
    }

    # Act
    response = await client.post(
        "/execute",
        headers={"X-Service-Key": test_service_key},
        json=payload
    )

    # Assert
    assert response.status_code == 400
    data = response.json()
    assert "Invalid UUID format" in data["detail"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_task_missing_task_id(client: AsyncClient, test_service_key: str, test_db):
    """Test delete with missing task_id returns 400."""
    # Arrange
    payload = {
        "action": "delete-task",
        "user_id": "test-user-delete",
        "payload": {}
    }

    # Act
    response = await client.post(
        "/execute",
        headers={"X-Service-Key": test_service_key},
        json=payload
    )

    # Assert
    assert response.status_code == 400
    data = response.json()
    assert "Missing required field: task_id" in data["detail"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_task_verify_database_persistence(client: AsyncClient, test_service_key: str, test_db):
    """Test delete operation permanently removes task from database."""
    # Arrange - Create task
    row = await test_db.fetchrow(
        """
        INSERT INTO tasks (user_id, title, description, status, priority, due_date)
        VALUES (
            'test-user-delete-verify',
            'Task With All Fields',
            'Description',
            'in_progress',
            'high',
            '2025-11-20T10:00:00Z'
        )
        RETURNING id
        """
    )
    task_id = str(row["id"])

    # Verify task exists before deletion
    before_delete = await test_db.fetchrow(
        "SELECT * FROM tasks WHERE id = $1",
        row["id"]
    )
    assert before_delete is not None

    # Act - Delete task
    payload = {
        "action": "delete-task",
        "user_id": "test-user-delete-verify",
        "payload": {"task_id": task_id}
    }
    response = await client.post(
        "/execute",
        headers={"X-Service-Key": test_service_key},
        json=payload
    )

    # Assert - Response success
    assert response.status_code == 200

    # Assert - Task no longer in database
    after_delete = await test_db.fetchrow(
        "SELECT * FROM tasks WHERE id = $1",
        row["id"]
    )
    assert after_delete is None
