"""
Unit tests for Statistics Service.

Tests the business logic for calculating task statistics using mocked database connections.
"""

from unittest.mock import AsyncMock

import pytest

from app.services.stats_service import (
    calculate_completion_rate,
    calculate_overdue_tasks,
    calculate_tasks_by_status,
    calculate_total_tasks,
    get_task_statistics,
)

# ============================================================================
# Tests for calculate_total_tasks
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_calculate_total_tasks_with_tasks():
    """User with tasks should return correct count"""
    # Arrange
    mock_db = AsyncMock()
    mock_db.fetchval.return_value = 10

    # Act
    result = await calculate_total_tasks("test-user", mock_db)

    # Assert
    assert result == 10
    mock_db.fetchval.assert_called_once_with(
        "SELECT COUNT(*) FROM tasks WHERE user_id = $1",
        "test-user"
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_calculate_total_tasks_no_tasks():
    """User with no tasks should return 0"""
    # Arrange
    mock_db = AsyncMock()
    mock_db.fetchval.return_value = 0

    # Act
    result = await calculate_total_tasks("test-user", mock_db)

    # Assert
    assert result == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_calculate_total_tasks_database_error():
    """Database error should propagate exception"""
    # Arrange
    mock_db = AsyncMock()
    mock_db.fetchval.side_effect = Exception("Database connection failed")

    # Act & Assert
    with pytest.raises(Exception, match="Database connection failed"):
        await calculate_total_tasks("test-user", mock_db)


# ============================================================================
# Tests for calculate_tasks_by_status
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_calculate_tasks_by_status_all_statuses():
    """User with tasks in all statuses should return correct counts"""
    # Arrange
    mock_db = AsyncMock()
    mock_db.fetch.return_value = [
        {"status": "pending", "count": 3},
        {"status": "in_progress", "count": 2},
        {"status": "completed", "count": 5}
    ]

    # Act
    result = await calculate_tasks_by_status("test-user", mock_db)

    # Assert
    assert result == {"pending": 3, "in_progress": 2, "completed": 5}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_calculate_tasks_by_status_partial_statuses():
    """User with tasks in only some statuses should default missing statuses to 0"""
    # Arrange
    mock_db = AsyncMock()
    mock_db.fetch.return_value = [
        {"status": "pending", "count": 5}
    ]

    # Act
    result = await calculate_tasks_by_status("test-user", mock_db)

    # Assert
    assert result == {"pending": 5, "in_progress": 0, "completed": 0}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_calculate_tasks_by_status_no_tasks():
    """User with no tasks should return all zeros"""
    # Arrange
    mock_db = AsyncMock()
    mock_db.fetch.return_value = []

    # Act
    result = await calculate_tasks_by_status("test-user", mock_db)

    # Assert
    assert result == {"pending": 0, "in_progress": 0, "completed": 0}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_calculate_tasks_by_status_database_error():
    """Database error should propagate exception"""
    # Arrange
    mock_db = AsyncMock()
    mock_db.fetch.side_effect = Exception("Database connection failed")

    # Act & Assert
    with pytest.raises(Exception, match="Database connection failed"):
        await calculate_tasks_by_status("test-user", mock_db)


# ============================================================================
# Tests for calculate_completion_rate
# ============================================================================

@pytest.mark.unit
def test_calculate_completion_rate_60_percent():
    """60% completion should return 60.0"""
    # Act
    result = calculate_completion_rate({"pending": 3, "in_progress": 1, "completed": 6})

    # Assert
    assert result == 60.0


@pytest.mark.unit
def test_calculate_completion_rate_0_percent():
    """0% completion should return 0.0"""
    # Act
    result = calculate_completion_rate({"pending": 5, "in_progress": 0, "completed": 0})

    # Assert
    assert result == 0.0


@pytest.mark.unit
def test_calculate_completion_rate_100_percent():
    """100% completion should return 100.0"""
    # Act
    result = calculate_completion_rate({"pending": 0, "in_progress": 0, "completed": 10})

    # Assert
    assert result == 100.0


@pytest.mark.unit
def test_calculate_completion_rate_zero_tasks():
    """Zero tasks should return 0.0"""
    # Act
    result = calculate_completion_rate({"pending": 0, "in_progress": 0, "completed": 0})

    # Assert
    assert result == 0.0


@pytest.mark.unit
def test_calculate_completion_rate_rounding():
    """Completion rate should be rounded to 2 decimal places"""
    # Act
    result = calculate_completion_rate({"pending": 1, "in_progress": 0, "completed": 2})

    # Assert
    assert result == 66.67


# ============================================================================
# Tests for calculate_overdue_tasks
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_calculate_overdue_tasks_with_overdue():
    """User with overdue tasks should return correct count"""
    # Arrange
    mock_db = AsyncMock()
    mock_db.fetchval.return_value = 3

    # Act
    result = await calculate_overdue_tasks("test-user", mock_db)

    # Assert
    assert result == 3


@pytest.mark.unit
@pytest.mark.asyncio
async def test_calculate_overdue_tasks_no_overdue():
    """User with no overdue tasks should return 0"""
    # Arrange
    mock_db = AsyncMock()
    mock_db.fetchval.return_value = 0

    # Act
    result = await calculate_overdue_tasks("test-user", mock_db)

    # Assert
    assert result == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_calculate_overdue_tasks_database_error():
    """Database error should propagate exception"""
    # Arrange
    mock_db = AsyncMock()
    mock_db.fetchval.side_effect = Exception("Database connection failed")

    # Act & Assert
    with pytest.raises(Exception, match="Database connection failed"):
        await calculate_overdue_tasks("test-user", mock_db)


# ============================================================================
# Tests for get_task_statistics (integration of functions)
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_task_statistics_complete():
    """Complete statistics should aggregate all functions correctly"""
    # Arrange
    mock_db = AsyncMock()
    mock_db.fetchval.side_effect = [10, 2]  # total_tasks, overdue_tasks
    mock_db.fetch.return_value = [
        {"status": "pending", "count": 3},
        {"status": "in_progress", "count": 2},
        {"status": "completed", "count": 5}
    ]

    # Act
    result = await get_task_statistics("test-user", mock_db)

    # Assert
    assert result == {
        "total_tasks": 10,
        "pending_tasks": 3,
        "in_progress_tasks": 2,
        "completed_tasks": 5,
        "completion_rate": 50.0,
        "overdue_tasks": 2
    }


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_task_statistics_zero_tasks():
    """Zero tasks should return all zeros and 0.0 completion rate"""
    # Arrange
    mock_db = AsyncMock()
    mock_db.fetchval.side_effect = [0, 0]  # total_tasks, overdue_tasks
    mock_db.fetch.return_value = []

    # Act
    result = await get_task_statistics("test-user", mock_db)

    # Assert
    assert result == {
        "total_tasks": 0,
        "pending_tasks": 0,
        "in_progress_tasks": 0,
        "completed_tasks": 0,
        "completion_rate": 0.0,
        "overdue_tasks": 0
    }


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_task_statistics_100_percent_completion():
    """Only completed tasks should return 100.0 completion rate"""
    # Arrange
    mock_db = AsyncMock()
    mock_db.fetchval.side_effect = [10, 0]  # total_tasks, overdue_tasks
    mock_db.fetch.return_value = [
        {"status": "completed", "count": 10}
    ]

    # Act
    result = await get_task_statistics("test-user", mock_db)

    # Assert
    assert result == {
        "total_tasks": 10,
        "pending_tasks": 0,
        "in_progress_tasks": 0,
        "completed_tasks": 10,
        "completion_rate": 100.0,
        "overdue_tasks": 0
    }


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_task_statistics_mixed_scenario():
    """Mixed scenario should calculate correctly"""
    # Arrange
    mock_db = AsyncMock()
    mock_db.fetchval.side_effect = [6, 1]  # total_tasks, overdue_tasks
    mock_db.fetch.return_value = [
        {"status": "pending", "count": 2},
        {"status": "in_progress", "count": 1},
        {"status": "completed", "count": 3}
    ]

    # Act
    result = await get_task_statistics("test-user", mock_db)

    # Assert
    assert result == {
        "total_tasks": 6,
        "pending_tasks": 2,
        "in_progress_tasks": 1,
        "completed_tasks": 3,
        "completion_rate": 50.0,
        "overdue_tasks": 1
    }
