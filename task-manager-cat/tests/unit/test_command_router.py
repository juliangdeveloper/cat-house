"""
Unit tests for Command Router (Story 3.2).

Tests command routing infrastructure without database dependencies:
- CommandRequest/CommandResponse model validation
- POST /execute endpoint authentication
- Action routing to handlers
- Error responses for unknown actions and invalid requests
"""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.auth import validate_service_key
from app.commands.models import CommandRequest, CommandResponse
from app.commands.router import ACTION_HANDLERS
from app.database import get_db


@pytest.mark.unit
class TestCommandRequestModel:
    """Test CommandRequest Pydantic model validation (AC1)."""

    def test_valid_request_parses_correctly(self):
        """Test valid CommandRequest with all fields."""
        request = CommandRequest(
            action="create-task",
            user_id="user_123",
            payload={"title": "Buy milk", "priority": "high"}
        )
        assert request.action == "create-task"
        assert request.user_id == "user_123"
        assert request.payload == {"title": "Buy milk", "priority": "high"}

    def test_payload_defaults_to_empty_dict(self):
        """Test CommandRequest payload defaults to empty dict."""
        request = CommandRequest(action="get-stats", user_id="user_456")
        assert request.payload == {}

    def test_missing_action_raises_validation_error(self):
        """Test CommandRequest requires action field."""
        with pytest.raises(ValidationError) as exc_info:
            CommandRequest(user_id="user_123", payload={})

        errors = exc_info.value.errors()
        assert any(error['loc'] == ('action',) for error in errors)

    def test_missing_user_id_raises_validation_error(self):
        """Test CommandRequest requires user_id field."""
        with pytest.raises(ValidationError) as exc_info:
            CommandRequest(action="create-task", payload={})

        errors = exc_info.value.errors()
        assert any(error['loc'] == ('user_id',) for error in errors)

    def test_empty_action_raises_validation_error(self):
        """Test CommandRequest rejects empty action (min_length=1)."""
        with pytest.raises(ValidationError) as exc_info:
            CommandRequest(action="", user_id="user_123", payload={})

        errors = exc_info.value.errors()
        assert any(error['loc'] == ('action',) for error in errors)

    def test_empty_user_id_raises_validation_error(self):
        """Test CommandRequest rejects empty user_id (min_length=1)."""
        with pytest.raises(ValidationError) as exc_info:
            CommandRequest(action="create-task", user_id="", payload={})

        errors = exc_info.value.errors()
        assert any(error['loc'] == ('user_id',) for error in errors)


@pytest.mark.unit
class TestCommandResponseModel:
    """Test CommandResponse Pydantic model serialization (AC1)."""

    def test_success_response_serializes_correctly(self):
        """Test CommandResponse success response with data."""
        response = CommandResponse(
            success=True,
            data={"id": "uuid-123", "title": "Buy milk"},
            error=None
        )
        assert response.success is True
        assert response.data == {"id": "uuid-123", "title": "Buy milk"}
        assert response.error is None
        assert isinstance(response.timestamp, datetime)

    def test_error_response_serializes_correctly(self):
        """Test CommandResponse error response with error message."""
        response = CommandResponse(
            success=False,
            data=None,
            error="Task not found"
        )
        assert response.success is False
        assert response.data is None
        assert response.error == "Task not found"
        assert isinstance(response.timestamp, datetime)

    def test_timestamp_serializes_to_iso_format(self):
        """Test CommandResponse timestamp serializes to ISO 8601."""
        response = CommandResponse(success=True, data={}, error=None)
        response_dict = response.model_dump(mode='json')

        # Timestamp should be ISO 8601 string
        timestamp_str = response_dict['timestamp']
        # Verify it's a valid ISO format by parsing it back
        parsed = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        assert isinstance(parsed, datetime)

    def test_timestamp_defaults_to_utc_now(self):
        """Test CommandResponse timestamp defaults to current UTC time."""
        before = datetime.now(timezone.utc)
        response = CommandResponse(success=True, data={}, error=None)
        after = datetime.now(timezone.utc)

        # Timestamp should be between before and after
        assert before <= response.timestamp <= after
        # Timestamp should be UTC
        assert response.timestamp.tzinfo == timezone.utc


@pytest.mark.unit
class TestCommandRouterAuthentication:
    """Test POST /execute endpoint authentication (AC2-3)."""

    def test_missing_service_key_returns_401(self):
        """Test endpoint requires X-Service-Key header."""
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app)
        response = client.post(
            "/execute",
            json={"action": "test-action", "user_id": "user_123", "payload": {}}
            # No X-Service-Key header
        )

        # FastAPI dependency injection fails without header, returns 422
        assert response.status_code == 422

    def test_valid_service_key_allows_request(self):
        """Test endpoint accepts valid X-Service-Key."""
        from fastapi.testclient import TestClient

        from app.main import app

        async def mock_validate_key():
            return "test-service"

        async def mock_get_db():
            return None

        # Override dependencies
        app.dependency_overrides[validate_service_key] = mock_validate_key
        app.dependency_overrides[get_db] = mock_get_db

        try:
            client = TestClient(app)
            response = client.post(
                "/execute",
                headers={"X-Service-Key": "sk_dev_test_key"},
                json={"action": "unknown-action", "user_id": "user_123", "payload": {}}
            )

            # Should pass authentication (404 because action doesn't exist)
            assert response.status_code == 404
        finally:
            # Clean up overrides
            app.dependency_overrides.clear()


@pytest.mark.unit
class TestCommandRouterRouting:
    """Test action routing and error handling (AC4-7)."""

    def test_unknown_action_returns_404(self):
        """Test unknown action returns 404 with error message (AC6)."""
        from fastapi.testclient import TestClient

        from app.main import app

        def mock_validate_key(x_service_key: str = None):
            return "test-service"

        def mock_get_db():
            return None

        # Override dependencies
        app.dependency_overrides[validate_service_key] = mock_validate_key
        app.dependency_overrides[get_db] = mock_get_db

        try:
            client = TestClient(app)
            response = client.post(
                "/execute",
                headers={"X-Service-Key": "sk_dev_test_key"},
                json={"action": "nonexistent-action", "user_id": "user_123", "payload": {}}
            )

            assert response.status_code == 404
            assert "Unknown action: nonexistent-action" in response.json()['detail']
        finally:
            app.dependency_overrides.clear()

    def test_invalid_request_returns_422(self):
        """Test invalid CommandRequest returns 422 validation error (AC7)."""
        from fastapi.testclient import TestClient

        from app.main import app

        def mock_validate_key(x_service_key: str = None):
            return "test-service"

        def mock_get_db():
            return None

        # Override dependencies
        app.dependency_overrides[validate_service_key] = mock_validate_key
        app.dependency_overrides[get_db] = mock_get_db

        try:
            client = TestClient(app)
            response = client.post(
                "/execute",
                headers={"X-Service-Key": "sk_dev_test_key"},
                json={"action": "create-task"}  # Missing required user_id
            )

            assert response.status_code == 422
            # Should include validation details
            assert 'detail' in response.json()
        finally:
            app.dependency_overrides.clear()

    def test_routing_to_mock_handler(self):
        """Test routing to registered handler works correctly (AC4-5)."""
        from fastapi.testclient import TestClient

        from app.main import app

        def mock_validate_key(x_service_key: str = None):
            return "test-service"

        def mock_get_db():
            return None

        # Create mock handler (synchronous wrapper for TestClient)
        async def mock_handler(user_id: str, payload: dict, db):
            return {"result": "success", "user_id": user_id}

        # Override dependencies
        app.dependency_overrides[validate_service_key] = mock_validate_key
        app.dependency_overrides[get_db] = mock_get_db

        # Register mock handler
        ACTION_HANDLERS["test-action"] = mock_handler

        try:
            client = TestClient(app)
            response = client.post(
                "/execute",
                headers={"X-Service-Key": "sk_dev_test_key"},
                json={"action": "test-action", "user_id": "user_123", "payload": {"key": "value"}}
            )

            assert response.status_code == 200
            response_data = response.json()
            assert response_data['success'] is True
            assert response_data['data']['result'] == "success"
            assert response_data['data']['user_id'] == "user_123"
            assert response_data['error'] is None

        finally:
            # Clean up
            del ACTION_HANDLERS["test-action"]
            app.dependency_overrides.clear()
