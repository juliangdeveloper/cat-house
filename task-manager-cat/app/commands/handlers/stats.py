"""
Statistics command handler for Task Manager API.

Implements HTTP handler for get-stats action that integrates statistics service layer
with the universal command pattern router.

Handler:
    - get_stats_handler: Retrieve task statistics for user

Architecture:
    - user_id: External user ID from Cat House (already authenticated)
    - payload: Empty dict {} for get-stats (no parameters needed)
    - db: asyncpg database connection from pool
    - Returns: dict with statistics (wrapped in CommandResponse by router)
    - Raises: HTTPException for unexpected errors (500)

Statistics Response Schema:
    {
        "total_tasks": int,
        "pending_tasks": int,
        "in_progress_tasks": int,
        "completed_tasks": int,
        "completion_rate": float,  # Percentage (0.0 to 100.0)
        "overdue_tasks": int
    }
"""

from typing import Any

import structlog
from fastapi import HTTPException

from app.services.stats_service import get_task_statistics

logger = structlog.get_logger()


async def get_stats_handler(user_id: str, payload: dict, db: Any) -> dict:
    """
    Retrieve task statistics for a user.
    
    Handler for 'get-stats' action. Calls statistics service layer to calculate
    real-time task metrics for Cat House Whiskers integration.
    
    Args:
        user_id: External user ID from Cat House (already authenticated)
        payload: Empty dict {} (no parameters needed for get-stats)
        db: asyncpg database connection from pool
    
    Returns:
        dict: Statistics object with 6 fields:
            - total_tasks: Total task count for user
            - pending_tasks: Count where status = 'pending'
            - in_progress_tasks: Count where status = 'in_progress'
            - completed_tasks: Count where status = 'completed'
            - completion_rate: Percentage (0.0 to 100.0), rounded to 2 decimals
            - overdue_tasks: Count where due_date < NOW() AND status != 'completed'
    
    Raises:
        HTTPException(500): Unexpected error during statistics calculation
    
    Example:
        Input: user_id="user_123", payload={}
        Output: {
            "total_tasks": 10,
            "pending_tasks": 3,
            "in_progress_tasks": 2,
            "completed_tasks": 5,
            "completion_rate": 50.0,
            "overdue_tasks": 1
        }
    
    Performance:
        - Target: < 200ms for users with up to 1000 tasks
        - Statistics calculated in real-time (not cached)
    
    Notes:
        - Service layer handles all database queries and calculations
        - Handler is thin HTTP wrapper that adds error handling and logging
        - Zero tasks edge case: All counts = 0, completion_rate = 0.0
        - User isolation enforced by service layer (WHERE user_id = $1)
    """
    try:
        # Log handler invocation
        logger.info("get_stats_handler_invoked", user_id=user_id)

        # Call service layer to calculate statistics
        stats = await get_task_statistics(user_id, db)

        # Log successful retrieval with stats fields for observability
        logger.info("stats_retrieved", user_id=user_id, **stats)

        # Return statistics dict (will be wrapped in CommandResponse by router)
        return stats

    except Exception as e:
        # Log error with context
        logger.error("stats_calculation_error", user_id=user_id, error=str(e))

        # Raise HTTP 500 for unexpected errors
        raise HTTPException(
            status_code=500,
            detail="Failed to calculate statistics"
        )
