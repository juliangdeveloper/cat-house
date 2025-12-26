"""
Command Pattern Request/Response Models for Task Manager API.

Implements Universal Command Pattern with standardized request/response formats
for Cat House Platform integration. All actions use these models for consistency
and extensibility.

Architecture:
    - CommandRequest: Standardized input from Cat House
    - CommandResponse: Standardized output to Cat House
    - Single endpoint (POST /execute) routes to multiple action handlers
"""

from datetime import datetime, timezone
from typing import Dict, Optional

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class CommandRequest(BaseModel):
    """
    Universal command request from Cat House Platform.
    
    All actions use this standardized format for consistency and extensibility.
    Cat House validates user JWT and permissions before sending command.
    
    Examples:
        Create task:
        {
          "action": "create-task",
          "user_id": "user_123",
          "payload": {"title": "Buy milk", "priority": "high"}
        }
        
        List tasks with filter:
        {
          "action": "list-tasks",
          "user_id": "user_456",
          "payload": {"status": "pending"}
        }
        
        Get statistics:
        {
          "action": "get-stats",
          "user_id": "user_789",
          "payload": {}
        }
    """
    action: str = Field(..., min_length=1, description="Action to execute")
    user_id: str = Field(..., min_length=1, description="User ID from Cat House")
    payload: Dict = Field(default_factory=dict, description="Action-specific parameters")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "action": "create-task",
                    "user_id": "user_123",
                    "payload": {
                        "title": "Buy cat food",
                        "description": "Whiskers needs more treats",
                        "status": "pending",
                        "priority": "high",
                        "due_date": "2025-11-15T10:00:00Z"
                    }
                },
                {
                    "action": "list-tasks",
                    "user_id": "user_456",
                    "payload": {
                        "status": "pending"
                    }
                },
                {
                    "action": "get-task",
                    "user_id": "user_123",
                    "payload": {
                        "task_id": "550e8400-e29b-41d4-a716-446655440000"
                    }
                },
                {
                    "action": "update-task",
                    "user_id": "user_123",
                    "payload": {
                        "task_id": "550e8400-e29b-41d4-a716-446655440000",
                        "status": "completed"
                    }
                },
                {
                    "action": "delete-task",
                    "user_id": "user_123",
                    "payload": {
                        "task_id": "550e8400-e29b-41d4-a716-446655440000"
                    }
                },
                {
                    "action": "get-stats",
                    "user_id": "user_789",
                    "payload": {}
                }
            ]
        }
    )


class CommandResponse(BaseModel):
    """
    Standardized response format for all command executions.
    
    Provides consistent structure for Cat House to parse results:
    - Success indicator (boolean)
    - Response data (handler-specific)
    - Error message (if failed)
    - Timestamp (for logging/debugging)
    
    Examples:
        Success response:
        {
          "success": true,
          "data": {"id": "uuid", "title": "Buy milk", ...},
          "error": null,
          "timestamp": "2025-11-12T10:30:00Z"
        }
        
        Error response:
        {
          "success": false,
          "data": null,
          "error": "Task not found",
          "timestamp": "2025-11-12T10:30:15Z"
        }
    """
    success: bool = Field(..., description="Operation success indicator")
    data: Optional[Dict] = Field(None, description="Response data from handler")
    error: Optional[str] = Field(None, description="Error message if failed")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Response timestamp (UTC)"
    )

    @field_serializer('timestamp')
    def serialize_timestamp(self, dt: datetime) -> str:
        """Serialize timestamp to ISO 8601 format."""
        return dt.isoformat()

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "success": True,
                    "data": {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "user_id": "user_123",
                        "title": "Buy cat food",
                        "description": "Whiskers needs more treats",
                        "status": "pending",
                        "priority": "high",
                        "created_at": "2025-11-13T10:00:00Z",
                        "completed_at": None,
                        "due_date": "2025-11-15T10:00:00Z"
                    },
                    "error": None,
                    "timestamp": "2025-11-13T10:00:05Z"
                },
                {
                    "success": True,
                    "data": {
                        "total_tasks": 10,
                        "pending_tasks": 3,
                        "in_progress_tasks": 2,
                        "completed_tasks": 5,
                        "completion_rate": 50.0,
                        "overdue_tasks": 2
                    },
                    "error": None,
                    "timestamp": "2025-11-13T12:00:00Z"
                },
                {
                    "success": False,
                    "data": None,
                    "error": "Task not found",
                    "timestamp": "2025-11-13T10:30:15Z"
                }
            ]
        }
    )
