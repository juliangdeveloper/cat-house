"""
Unit tests for statistics command handler.

Tests the get_stats_handler function in isolation using mocked service layer.
Tests cover successful retrieval, empty payload acceptance, zero tasks edge case,
and error handling.
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from app.commands.handlers.stats import get_stats_handler


@pytest.mark.unit
@pytest.mark.asyncio
class TestGetStatsHandler:
    """Unit tests for get_stats_handler function."""

    async def test_successful_stats_retrieval(self):
        """Test successful statistics retrieval from service layer."""
        # Arrange
        mock_db = AsyncMock()
        test_user_id = "test-user"
        test_payload = {}
        expected_stats = {
            "total_tasks": 10,
            "pending_tasks": 3,
            "in_progress_tasks": 2,
            "completed_tasks": 5,
            "completion_rate": 50.0,
            "overdue_tasks": 1
        }

        with patch("app.commands.handlers.stats.get_task_statistics", new_callable=AsyncMock) as mock_get_stats:
            mock_get_stats.return_value = expected_stats

            # Act
            result = await get_stats_handler(test_user_id, test_payload, mock_db)

            # Assert
            assert result == expected_stats
            mock_get_stats.assert_called_once_with(test_user_id, mock_db)

    async def test_empty_payload_accepted(self):
        """Test handler accepts empty payload without errors."""
        # Arrange
        mock_db = AsyncMock()
        test_user_id = "test-user"
        empty_payload = {}
        expected_stats = {
            "total_tasks": 5,
            "pending_tasks": 2,
            "in_progress_tasks": 1,
            "completed_tasks": 2,
            "completion_rate": 40.0,
            "overdue_tasks": 0
        }

        with patch("app.commands.handlers.stats.get_task_statistics", new_callable=AsyncMock) as mock_get_stats:
            mock_get_stats.return_value = expected_stats

            # Act
            result = await get_stats_handler(test_user_id, empty_payload, mock_db)

            # Assert - handler ignores payload and calls service layer
            assert result == expected_stats
            mock_get_stats.assert_called_once_with(test_user_id, mock_db)

    async def test_zero_tasks_edge_case(self):
        """Test handler returns zeros for user with no tasks."""
        # Arrange
        mock_db = AsyncMock()
        test_user_id = "empty-user"
        test_payload = {}
        expected_stats = {
            "total_tasks": 0,
            "pending_tasks": 0,
            "in_progress_tasks": 0,
            "completed_tasks": 0,
            "completion_rate": 0.0,
            "overdue_tasks": 0
        }

        with patch("app.commands.handlers.stats.get_task_statistics", new_callable=AsyncMock) as mock_get_stats:
            mock_get_stats.return_value = expected_stats

            # Act
            result = await get_stats_handler(test_user_id, test_payload, mock_db)

            # Assert
            assert result == expected_stats
            assert result["total_tasks"] == 0
            assert result["completion_rate"] == 0.0

    async def test_service_layer_exception_handling(self):
        """Test handler raises HTTPException(500) on service layer errors."""
        # Arrange
        mock_db = AsyncMock()
        test_user_id = "error-user"
        test_payload = {}

        with patch("app.commands.handlers.stats.get_task_statistics", new_callable=AsyncMock) as mock_get_stats:
            mock_get_stats.side_effect = Exception("Database connection error")

            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await get_stats_handler(test_user_id, test_payload, mock_db)

            # Verify HTTP 500 error
            assert exc_info.value.status_code == 500
            assert exc_info.value.detail == "Failed to calculate statistics"
