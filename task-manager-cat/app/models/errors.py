"""
Error Response Models for Task Manager API.

Defines standardized error response formats for OpenAPI documentation.
Used in endpoint responses parameter to document error structures.
"""

from typing import List

from pydantic import BaseModel, ConfigDict, Field


class ValidationErrorDetail(BaseModel):
    """
    Single validation error detail from FastAPI/Pydantic.
    
    Example:
        {
            "loc": ["body", "action"],
            "msg": "field required",
            "type": "value_error.missing"
        }
    """
    loc: List[str] = Field(..., description="Error location (field path)")
    msg: str = Field(..., description="Error message")
    type: str = Field(..., description="Error type")


class ValidationErrorResponse(BaseModel):
    """
    422 Unprocessable Entity response format.
    
    Returned when request body fails Pydantic validation.
    Contains list of all validation errors found.
    
    Example:
        {
            "detail": [
                {
                    "loc": ["body", "action"],
                    "msg": "field required",
                    "type": "value_error.missing"
                },
                {
                    "loc": ["body", "payload", "title"],
                    "msg": "field required",
                    "type": "value_error.missing"
                }
            ]
        }
    """
    detail: List[ValidationErrorDetail] = Field(..., description="List of validation errors")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "detail": [
                        {
                            "loc": ["body", "action"],
                            "msg": "field required",
                            "type": "value_error.missing"
                        }
                    ]
                },
                {
                    "detail": [
                        {
                            "loc": ["body", "payload", "title"],
                            "msg": "field required",
                            "type": "value_error.missing"
                        },
                        {
                            "loc": ["body", "payload", "status"],
                            "msg": "string does not match regex",
                            "type": "value_error.str.regex"
                        }
                    ]
                }
            ]
        }
    )


class ErrorResponse(BaseModel):
    """
    Standard error response for non-validation errors.
    
    Used for:
    - 400 Bad Request (unknown action, invalid payload)
    - 401 Unauthorized (invalid service key)
    - 404 Not Found (task not found, user mismatch)
    
    Example:
        {"detail": "Invalid service key"}
        {"detail": "Unknown action: invalid-action"}
        {"detail": "Task not found"}
    """
    detail: str = Field(..., description="Error message")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"detail": "Invalid service key"},
                {"detail": "Unknown action: invalid-action"},
                {"detail": "Task not found"},
                {"detail": "Admin key required"}
            ]
        }
    )
