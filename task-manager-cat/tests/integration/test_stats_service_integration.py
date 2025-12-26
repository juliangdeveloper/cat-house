"""
Integration tests for Statistics Service.

Tests the statistics service with real database connections to verify SQL queries
and calculations work correctly with actual data.
"""

from datetime import datetime, timedelta

import pytest

from app.services.stats_service import (
    calculate_overdue_tasks,
    calculate_tasks_by_status,
    calculate_total_tasks,
    get_task_statistics,
)


@pytest.fixture(autouse=True)
async def cleanup_test_data(test_db):
    """Cleanup test data before and after each test"""
    # Cleanup before test
    await test_db.execute("DELETE FROM tasks WHERE user_id LIKE 'test-stats-%'")
    yield
    # Cleanup after test
    await test_db.execute("DELETE FROM tasks WHERE user_id LIKE 'test-stats-%'")


async def create_task(db, user_id: str, title: str, status: str = "pending",
                      due_date: datetime = None):
    """Helper function to create test tasks"""
    query = """
        INSERT INTO tasks (user_id, title, status, due_date)
        VALUES ($1, $2, $3, $4)
        RETURNING id
    """
    return await db.fetchval(query, user_id, title, status, due_date)


# ============================================================================
# Tests for calculate_total_tasks with real database
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
async def test_calculate_total_tasks_with_real_tasks(test_db):
    """Create 5 tasks for user and verify count = 5"""
    # Arrange
    user_id = "test-stats-user-1"
    for i in range(5):
        await create_task(test_db, user_id, f"Task {i+1}")

    # Act
    result = await calculate_total_tasks(user_id, test_db)

    # Assert
    assert result == 5


@pytest.mark.asyncio
@pytest.mark.integration
async def test_calculate_total_tasks_user_isolation(test_db):
    """Different user should see count = 0 (user isolation)"""
    # Arrange
    user_id_1 = "test-stats-user-1"
    user_id_2 = "test-stats-user-2"

    # Create 3 tasks for user 1
    for i in range(3):
        await create_task(test_db, user_id_1, f"Task {i+1}")

    # Act - Query for user 2
    result = await calculate_total_tasks(user_id_2, test_db)

    # Assert
    assert result == 0


# ============================================================================
# Tests for calculate_tasks_by_status with real database
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
async def test_calculate_tasks_by_status_mixed_statuses(test_db):
    """Create tasks with different statuses and verify exact counts"""
    # Arrange
    user_id = "test-stats-user-3"
    await create_task(test_db, user_id, "Task 1", "pending")
    await create_task(test_db, user_id, "Task 2", "pending")
    await create_task(test_db, user_id, "Task 3", "in_progress")
    await create_task(test_db, user_id, "Task 4", "completed")
    await create_task(test_db, user_id, "Task 5", "completed")
    await create_task(test_db, user_id, "Task 6", "completed")

    # Act
    result = await calculate_tasks_by_status(user_id, test_db)

    # Assert
    assert result == {"pending": 2, "in_progress": 1, "completed": 3}


@pytest.mark.asyncio
@pytest.mark.integration
async def test_calculate_tasks_by_status_only_pending(test_db):
    """Create only pending tasks, verify in_progress=0, completed=0"""
    # Arrange
    user_id = "test-stats-user-4"
    await create_task(test_db, user_id, "Task 1", "pending")
    await create_task(test_db, user_id, "Task 2", "pending")

    # Act
    result = await calculate_tasks_by_status(user_id, test_db)

    # Assert
    assert result == {"pending": 2, "in_progress": 0, "completed": 0}


@pytest.mark.asyncio
@pytest.mark.integration
async def test_calculate_tasks_by_status_no_tasks(test_db):
    """Query user with no tasks, verify all zeros"""
    # Arrange
    user_id = "test-stats-user-5"

    # Act
    result = await calculate_tasks_by_status(user_id, test_db)

    # Assert
    assert result == {"pending": 0, "in_progress": 0, "completed": 0}


# ============================================================================
# Tests for calculate_overdue_tasks with real database
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
async def test_calculate_overdue_tasks_past_due_pending(test_db):
    """Task with past due_date and status=pending should be overdue"""
    # Arrange
    user_id = "test-stats-user-6"
    yesterday = datetime.now() - timedelta(days=1)
    await create_task(test_db, user_id, "Overdue Task", "pending", yesterday)

    # Act
    result = await calculate_overdue_tasks(user_id, test_db)

    # Assert
    assert result == 1


@pytest.mark.asyncio
@pytest.mark.integration
async def test_calculate_overdue_tasks_past_due_completed(test_db):
    """Task with past due_date and status=completed should NOT be overdue"""
    # Arrange
    user_id = "test-stats-user-7"
    yesterday = datetime.now() - timedelta(days=1)
    await create_task(test_db, user_id, "Completed Task", "completed", yesterday)

    # Act
    result = await calculate_overdue_tasks(user_id, test_db)

    # Assert
    assert result == 0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_calculate_overdue_tasks_future_due_date(test_db):
    """Task with future due_date should NOT be overdue"""
    # Arrange
    user_id = "test-stats-user-8"
    tomorrow = datetime.now() + timedelta(days=1)
    await create_task(test_db, user_id, "Future Task", "pending", tomorrow)

    # Act
    result = await calculate_overdue_tasks(user_id, test_db)

    # Assert
    assert result == 0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_calculate_overdue_tasks_null_due_date(test_db):
    """Task with NULL due_date should NOT be overdue"""
    # Arrange
    user_id = "test-stats-user-9"
    await create_task(test_db, user_id, "No Due Date Task", "pending", None)

    # Act
    result = await calculate_overdue_tasks(user_id, test_db)

    # Assert
    assert result == 0


# ============================================================================
# Tests for get_task_statistics with real database
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_task_statistics_mixed_scenario(test_db):
    """Mixed scenario: Create 10 tasks with various statuses and overdue tasks"""
    # Arrange
    user_id = "test-stats-user-10"
    yesterday = datetime.now() - timedelta(days=1)
    tomorrow = datetime.now() + timedelta(days=1)

    # Create 3 pending tasks (2 overdue, 1 future)
    await create_task(test_db, user_id, "Overdue Pending 1", "pending", yesterday)
    await create_task(test_db, user_id, "Overdue Pending 2", "pending", yesterday)
    await create_task(test_db, user_id, "Future Pending", "pending", tomorrow)

    # Create 2 in_progress tasks (both not overdue)
    await create_task(test_db, user_id, "In Progress 1", "in_progress", None)
    await create_task(test_db, user_id, "In Progress 2", "in_progress", tomorrow)

    # Create 5 completed tasks (not overdue even if past due)
    await create_task(test_db, user_id, "Completed 1", "completed", yesterday)
    await create_task(test_db, user_id, "Completed 2", "completed", None)
    await create_task(test_db, user_id, "Completed 3", "completed", None)
    await create_task(test_db, user_id, "Completed 4", "completed", None)
    await create_task(test_db, user_id, "Completed 5", "completed", None)

    # Act
    result = await get_task_statistics(user_id, test_db)

    # Assert
    assert result["total_tasks"] == 10
    assert result["pending_tasks"] == 3
    assert result["in_progress_tasks"] == 2
    assert result["completed_tasks"] == 5
    assert result["completion_rate"] == 50.0
    assert result["overdue_tasks"] == 2  # Only 2 overdue pending tasks


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_task_statistics_zero_tasks(test_db):
    """Query non-existent user, verify all zeros and 0.0 completion rate"""
    # Arrange
    user_id = "test-stats-user-11"

    # Act
    result = await get_task_statistics(user_id, test_db)

    # Assert
    assert result == {
        "total_tasks": 0,
        "pending_tasks": 0,
        "in_progress_tasks": 0,
        "completed_tasks": 0,
        "completion_rate": 0.0,
        "overdue_tasks": 0
    }


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_task_statistics_completion_rate_calculation(test_db):
    """Create 1 pending + 2 completed, verify completion_rate = 66.67"""
    # Arrange
    user_id = "test-stats-user-12"
    await create_task(test_db, user_id, "Pending Task", "pending")
    await create_task(test_db, user_id, "Completed Task 1", "completed")
    await create_task(test_db, user_id, "Completed Task 2", "completed")

    # Act
    result = await get_task_statistics(user_id, test_db)

    # Assert
    assert result["total_tasks"] == 3
    assert result["pending_tasks"] == 1
    assert result["in_progress_tasks"] == 0
    assert result["completed_tasks"] == 2
    assert result["completion_rate"] == 66.67
    assert result["overdue_tasks"] == 0
