"""
Statistics Service for Task Manager API.

Provides business logic for calculating task statistics for users.
All functions are stateless and unit testable independent of HTTP layer.

Functions:
    - calculate_total_tasks: Total task count for user
    - calculate_tasks_by_status: Task counts by status (pending, in_progress, completed)
    - calculate_completion_rate: Percentage of completed tasks
    - calculate_overdue_tasks: Count of overdue incomplete tasks
    - get_task_statistics: Aggregated statistics (main function)
"""

from typing import Any

import structlog

logger = structlog.get_logger()


async def calculate_total_tasks(user_id: str, db: Any) -> int:
    """
    Calculate total task count for a user.

    Args:
        user_id: User identifier
        db: Database connection (asyncpg Connection)

    Returns:
        Total number of tasks for the user (0 if user has no tasks)

    Raises:
        Exception: Database query errors are propagated to caller
    """
    try:
        query = "SELECT COUNT(*) FROM tasks WHERE user_id = $1"
        result = await db.fetchval(query, user_id)
        logger.debug("calculating_total_tasks", user_id=user_id, count=result)
        return result
    except Exception as e:
        logger.error("total_tasks_error", user_id=user_id, error=str(e))
        raise


async def calculate_tasks_by_status(user_id: str, db: Any) -> dict[str, int]:
    """
    Calculate task counts grouped by status.

    Args:
        user_id: User identifier
        db: Database connection (asyncpg Connection)

    Returns:
        Dictionary with status counts: {"pending": 2, "in_progress": 1, "completed": 5}
        All statuses included with default 0 counts

    Raises:
        Exception: Database query errors are propagated to caller
    """
    try:
        # Initialize result with all statuses set to 0
        result = {"pending": 0, "in_progress": 0, "completed": 0}

        query = "SELECT status, COUNT(*) as count FROM tasks WHERE user_id = $1 GROUP BY status"
        rows = await db.fetch(query, user_id)

        # Update with actual counts from query
        for row in rows:
            result[row['status']] = row['count']

        logger.debug("calculating_tasks_by_status", user_id=user_id, **result)
        return result
    except Exception as e:
        logger.error("tasks_by_status_error", user_id=user_id, error=str(e))
        raise


def calculate_completion_rate(status_counts: dict[str, int]) -> float:
    """
    Calculate completion rate as percentage from status counts.

    This function does NOT query the database - it's a pure calculation function
    that uses the status counts dictionary from calculate_tasks_by_status.

    Args:
        status_counts: Dictionary with status counts from calculate_tasks_by_status

    Returns:
        Completion rate as percentage (0.0 to 100.0), rounded to 2 decimal places

    Example:
        >>> calculate_completion_rate({"pending": 3, "in_progress": 1, "completed": 6})
        60.0
    """
    total = sum(status_counts.values())

    if total == 0:
        return 0.0

    completion_rate = (status_counts["completed"] / total) * 100
    return round(completion_rate, 2)


async def calculate_overdue_tasks(user_id: str, db: Any) -> int:
    """
    Calculate count of overdue tasks for a user.

    Overdue tasks are defined as:
    - due_date < NOW() (past due)
    - status != 'completed' (not yet completed)
    - Tasks with NULL due_date are NOT considered overdue

    Args:
        user_id: User identifier
        db: Database connection (asyncpg Connection)

    Returns:
        Count of overdue tasks (0 if no overdue tasks)

    Raises:
        Exception: Database query errors are propagated to caller
    """
    try:
        query = """
            SELECT COUNT(*) FROM tasks
            WHERE user_id = $1
            AND due_date < NOW()
            AND status != 'completed'
        """
        result = await db.fetchval(query, user_id)
        logger.debug("calculating_overdue_tasks", user_id=user_id, overdue_count=result)
        return result
    except Exception as e:
        logger.error("overdue_tasks_error", user_id=user_id, error=str(e))
        raise


async def get_task_statistics(user_id: str, db: Any) -> dict:
    """
    Calculate aggregated task statistics for a user.

    Main function that calls all calculation functions and returns a comprehensive
    statistics object. Optimized for users with up to 1000 tasks (< 200ms).

    Args:
        user_id: User identifier
        db: Database connection (asyncpg Connection)

    Returns:
        Dictionary with all statistics fields:
        {
            "total_tasks": 10,
            "pending_tasks": 3,
            "in_progress_tasks": 2,
            "completed_tasks": 5,
            "completion_rate": 50.0,
            "overdue_tasks": 1
        }

    Example:
        >>> stats = await get_task_statistics("user_123", db)
        >>> print(stats["completion_rate"])
        60.0

    Raises:
        Exception: Database query errors are propagated to caller
    """
    # Call all calculation functions
    total = await calculate_total_tasks(user_id, db)
    status_counts = await calculate_tasks_by_status(user_id, db)
    completion_rate = calculate_completion_rate(status_counts)
    overdue = await calculate_overdue_tasks(user_id, db)

    # Build response dict
    result = {
        "total_tasks": total,
        "pending_tasks": status_counts["pending"],
        "in_progress_tasks": status_counts["in_progress"],
        "completed_tasks": status_counts["completed"],
        "completion_rate": completion_rate,
        "overdue_tasks": overdue
    }

    logger.info("calculated_user_stats", user_id=user_id, total=total, overdue=overdue)
    return result
