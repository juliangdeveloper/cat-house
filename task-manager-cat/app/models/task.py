"""
Task Pydantic models for Task Manager API.

Defines request/response models for task CRUD operations:
- TaskCreate: Request payload for create-task action
- TaskUpdate: Request payload for update-task action (partial updates)
- TaskResponse: API response format for all task actions
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TaskCreate(BaseModel):
    """
    Request model for create-task action.
    
    Used in create-task handler to validate user input from Cat House.
    All fields except title are optional with sensible defaults.
    
    Example:
        {
            "title": "Buy milk",
            "priority": "high",
            "due_date": "2025-11-20T10:00:00Z"
        }
    """
    title: str = Field(..., max_length=500, description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    status: str = Field("pending", pattern="^(pending|in_progress|completed)$", description="Task status")
    priority: Optional[str] = Field(None, pattern="^(low|medium|high|urgent)$", description="Task priority")
    due_date: Optional[datetime] = Field(None, description="Task due date (UTC)")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "title": "Buy cat food",
                    "description": "Whiskers needs more treats",
                    "status": "pending",
                    "priority": "high",
                    "due_date": "2025-11-15T10:00:00Z"
                },
                {
                    "title": "Schedule vet appointment",
                    "priority": "urgent",
                    "due_date": "2025-11-14T09:00:00Z"
                },
                {
                    "title": "Clean litter box",
                    "status": "pending"
                }
            ]
        }
    )


class TaskUpdate(BaseModel):
    """
    Request model for update-task action.
    
    All fields are optional to support partial updates.
    Only provided fields will be updated in database.
    
    Example (update status only):
        {"status": "completed"}
    """
    title: Optional[str] = Field(None, max_length=500, description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    status: Optional[str] = Field(None, pattern="^(pending|in_progress|completed)$", description="Task status")
    priority: Optional[str] = Field(None, pattern="^(low|medium|high|urgent)$", description="Task priority")
    due_date: Optional[datetime] = Field(None, description="Task due date (UTC)")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "status": "completed"
                },
                {
                    "status": "in_progress",
                    "priority": "urgent"
                },
                {
                    "title": "Buy premium cat food",
                    "description": "Get the organic brand",
                    "due_date": "2025-11-16T10:00:00Z"
                }
            ]
        }
    )


class TaskResponse(BaseModel):
    """
    Response model for all task actions.
    
    Includes all database fields with generated values (id, created_at, etc.).
    Compatible with asyncpg Row objects via from_attributes.
    
    Example:
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "user_id": "user_123",
            "title": "Buy milk",
            "description": null,
            "status": "pending",
            "priority": "high",
            "created_at": "2025-11-12T10:00:00Z",
            "completed_at": null,
            "due_date": "2025-11-20T10:00:00Z"
        }
    """
    id: UUID
    user_id: str
    title: str
    description: Optional[str]
    status: str
    priority: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]
    due_date: Optional[datetime]

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
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
                {
                    "id": "661f9511-f39c-52e5-b827-557766551111",
                    "user_id": "user_456",
                    "title": "Schedule vet appointment",
                    "description": None,
                    "status": "completed",
                    "priority": "urgent",
                    "created_at": "2025-11-10T08:00:00Z",
                    "completed_at": "2025-11-12T14:30:00Z",
                    "due_date": "2025-11-14T09:00:00Z"
                }
            ]
        }
    )
