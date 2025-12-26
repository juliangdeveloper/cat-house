"""
Integration tests for OpenAPI specification validation.

Tests verify that OpenAPI/Swagger documentation is properly configured
and accessible for Cat House Platform integration.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_openapi_json_accessible(client: AsyncClient):
    """OpenAPI JSON specification should be accessible at /openapi.json"""
    response = await client.get("/openapi.json")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"


@pytest.mark.asyncio
async def test_openapi_spec_has_required_metadata(client: AsyncClient):
    """OpenAPI spec should include required metadata fields"""
    response = await client.get("/openapi.json")
    spec = response.json()

    # Verify OpenAPI version
    assert "openapi" in spec
    assert spec["openapi"].startswith("3.")  # OpenAPI 3.x

    # Verify API metadata
    assert "info" in spec
    assert spec["info"]["title"] == "Task Manager API"
    assert spec["info"]["version"] == "1.0.0"
    assert "description" in spec["info"]
    assert "Cat House Platform" in spec["info"]["description"]

    # Verify contact information
    assert "contact" in spec["info"]
    assert spec["info"]["contact"]["name"] == "Cat House Platform Team"

    # Verify license information
    assert "license" in spec["info"]
    assert spec["info"]["license"]["name"] == "MIT License"

    # Verify paths are documented
    assert "paths" in spec
    assert "/execute" in spec["paths"]
    assert "/health" in spec["paths"]


@pytest.mark.asyncio
async def test_openapi_spec_documents_security_schemes(client: AsyncClient):
    """OpenAPI spec should document authentication security schemes"""
    response = await client.get("/openapi.json")
    spec = response.json()

    # Verify components section exists
    assert "components" in spec
    assert "securitySchemes" in spec["components"]

    # Verify ServiceKey scheme
    assert "ServiceKey" in spec["components"]["securitySchemes"]
    service_key_scheme = spec["components"]["securitySchemes"]["ServiceKey"]
    assert service_key_scheme["type"] == "apiKey"
    assert service_key_scheme["in"] == "header"
    assert service_key_scheme["name"] == "X-Service-Key"
    assert "description" in service_key_scheme

    # Verify AdminKey scheme
    assert "AdminKey" in spec["components"]["securitySchemes"]
    admin_key_scheme = spec["components"]["securitySchemes"]["AdminKey"]
    assert admin_key_scheme["type"] == "apiKey"
    assert admin_key_scheme["in"] == "header"
    assert admin_key_scheme["name"] == "X-Admin-Key"
    assert "description" in admin_key_scheme


@pytest.mark.asyncio
async def test_openapi_spec_documents_all_command_actions(client: AsyncClient):
    """OpenAPI spec should document all 6 command actions in /execute endpoint"""
    response = await client.get("/openapi.json")
    spec = response.json()

    # Get /execute endpoint documentation
    execute_endpoint = spec["paths"]["/execute"]["post"]
    description = execute_endpoint["description"]

    # Verify all 6 actions are mentioned in documentation
    expected_actions = [
        "create-task",
        "list-tasks",
        "get-task",
        "update-task",
        "delete-task",
        "get-stats"
    ]

    for action in expected_actions:
        assert action in description, f"Action '{action}' not documented in /execute endpoint"


@pytest.mark.asyncio
async def test_openapi_spec_has_request_response_examples(client: AsyncClient):
    """OpenAPI spec should include examples for request/response models"""
    response = await client.get("/openapi.json")
    spec = response.json()

    # Verify CommandRequest model has examples
    command_request = spec["components"]["schemas"]["CommandRequest"]
    assert "examples" in command_request
    assert len(command_request["examples"]) >= 6  # At least one example per action

    # Verify CommandResponse model has examples
    command_response = spec["components"]["schemas"]["CommandResponse"]
    assert "examples" in command_response
    assert len(command_response["examples"]) >= 2  # Success and error examples


@pytest.mark.asyncio
async def test_swagger_ui_accessible(client: AsyncClient):
    """Swagger UI should be accessible at /docs endpoint"""
    response = await client.get("/docs")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    # Verify it's actually Swagger UI
    assert b"swagger-ui" in response.content.lower()


@pytest.mark.asyncio
async def test_redoc_accessible(client: AsyncClient):
    """ReDoc UI should be accessible at /redoc endpoint"""
    response = await client.get("/redoc")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    # Verify it's actually ReDoc
    assert b"redoc" in response.content.lower()
