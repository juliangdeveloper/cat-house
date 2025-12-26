"""
Integration tests for get-stats command action.

Tests end-to-end statistics retrieval through POST /execute endpoint:
- get-stats action with real tasks
- Zero tasks edge case
- Authentication requirement
- User isolation
- Performance (< 200ms for 1000 tasks)

Uses real database and HTTP client from conftest.py fixtures.
"""

import time
from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_stats_with_real_tasks(client: AsyncClient, test_service_key: str, test_db):
    """Test get-stats with real tasks in mixed statuses."""
    # Arrange - Create 10 test tasks with mixed statuses
    test_user_id = "test-stats-user-1"

    # Create 3 pending tasks (2 overdue)
    await test_db.execute(
        "INSERT INTO tasks (user_id, title, status, due_date) VALUES ($1, $2, $3, $4)",
        test_user_id, "Pending task 1", "pending", datetime.now() - timedelta(days=1)
    )
    await test_db.execute(
        "INSERT INTO tasks (user_id, title, status, due_date) VALUES ($1, $2, $3, $4)",
        test_user_id, "Pending task 2", "pending", datetime.now() - timedelta(days=2)
    )
    await test_db.execute(
        "INSERT INTO tasks (user_id, title, status) VALUES ($1, $2, $3)",
        test_user_id, "Pending task 3", "pending"
    )

    # Create 2 in_progress tasks (not overdue)
    await test_db.execute(
        "INSERT INTO tasks (user_id, title, status, due_date) VALUES ($1, $2, $3, $4)",
        test_user_id, "In progress 1", "in_progress", datetime.now() + timedelta(days=1)
    )
    await test_db.execute(
        "INSERT INTO tasks (user_id, title, status) VALUES ($1, $2, $3)",
        test_user_id, "In progress 2", "in_progress"
    )

    # Create 5 completed tasks
    for i in range(5):
        await test_db.execute(
            "INSERT INTO tasks (user_id, title, status) VALUES ($1, $2, $3)",
            test_user_id, f"Completed task {i+1}", "completed"
        )

    # Act
    payload = {
        "action": "get-stats",
        "user_id": test_user_id,
        "payload": {}
    }

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

    # Assert - Statistics data
    stats = data["data"]
    assert stats["total_tasks"] == 10
    assert stats["pending_tasks"] == 3
    assert stats["in_progress_tasks"] == 2
    assert stats["completed_tasks"] == 5
    assert stats["completion_rate"] == 50.0
    assert stats["overdue_tasks"] == 2


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_stats_with_zero_tasks(client: AsyncClient, test_service_key: str, test_db):
    """Test get-stats for user with no tasks returns zeros."""
    # Arrange - Use user with no tasks
    test_user_id = "test-stats-empty-user"

    # Act
    payload = {
        "action": "get-stats",
        "user_id": test_user_id,
        "payload": {}
    }

    response = await client.post(
        "/execute",
        headers={"X-Service-Key": test_service_key},
        json=payload
    )

    # Assert - Response structure
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

    # Assert - All zeros
    stats = data["data"]
    assert stats["total_tasks"] == 0
    assert stats["pending_tasks"] == 0
    assert stats["in_progress_tasks"] == 0
    assert stats["completed_tasks"] == 0
    assert stats["completion_rate"] == 0.0
    assert stats["overdue_tasks"] == 0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_stats_requires_authentication(client: AsyncClient, test_db):
    """Test get-stats requires valid X-Service-Key authentication."""
    # Arrange
    payload = {
        "action": "get-stats",
        "user_id": "test-user",
        "payload": {}
    }

    # Act - Send request with invalid X-Service-Key header
    response = await client.post(
        "/execute",
        headers={"X-Service-Key": "invalid-key"},
        json=payload
    )

    # Assert - 401 Unauthorized (invalid key)
    assert response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_stats_user_isolation(client: AsyncClient, test_service_key: str, test_db):
    """Test get-stats enforces user isolation (no cross-user data leaks)."""
    # Arrange - Create tasks for user-A
    test_user_a = "test-stats-user-a"
    test_user_b = "test-stats-user-b"

    # Create 5 tasks for user-A
    for i in range(5):
        await test_db.execute(
            "INSERT INTO tasks (user_id, title, status) VALUES ($1, $2, $3)",
            test_user_a, f"Task {i+1}", "completed"
        )

    # Act - Query stats for user-B (should see zero tasks)
    payload = {
        "action": "get-stats",
        "user_id": test_user_b,
        "payload": {}
    }

    response = await client.post(
        "/execute",
        headers={"X-Service-Key": test_service_key},
        json=payload
    )

    # Assert - User-B sees zero tasks (not user-A's tasks)
    assert response.status_code == 200
    data = response.json()
    stats = data["data"]
    assert stats["total_tasks"] == 0
    assert stats["completed_tasks"] == 0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_stats_performance(client: AsyncClient, test_service_key: str, test_db):
    """Test get-stats response time < 200ms for 1000 tasks."""
    # Arrange - Create 1000 tasks for single user
    test_user_id = "test-stats-perf-user"

    # Bulk insert 1000 tasks
    tasks = []
    for i in range(1000):
        status = ["pending", "in_progress", "completed"][i % 3]
        tasks.append((test_user_id, f"Task {i+1}", status))

    await test_db.executemany(
        "INSERT INTO tasks (user_id, title, status) VALUES ($1, $2, $3)",
        tasks
    )

    # Act - Measure response time
    payload = {
        "action": "get-stats",
        "user_id": test_user_id,
        "payload": {}
    }

    start_time = time.time()
    response = await client.post(
        "/execute",
        headers={"X-Service-Key": test_service_key},
        json=payload
    )
    end_time = time.time()

    response_time_ms = (end_time - start_time) * 1000

    # Assert - Response is successful
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

    # Assert - Statistics are correct
    stats = data["data"]
    assert stats["total_tasks"] == 1000

    # Assert - Performance requirement (< 200ms)
    assert response_time_ms < 200, f"Response time {response_time_ms:.2f}ms exceeds 200ms threshold"
