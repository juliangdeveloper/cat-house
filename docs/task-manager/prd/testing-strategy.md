# Testing Strategy - Task Manager API

**Document Version:** 1.0  
**Last Updated:** November 12, 2025  
**Status:** Active

---

## Overview

This document outlines the testing approach for Task Manager API based on implemented test patterns across Stories 1.2-3.2. The strategy emphasizes **practical testing** that maintains code quality while keeping tests simple and maintainable.

---

## Testing Philosophy

**Test What Matters:**
- Focus on business logic, not framework behavior
- Test real bugs and edge cases, not theoretical scenarios
- Keep tests simple enough that future developers can understand them

**Three-Level Approach:**
1. **Unit Tests:** Test individual functions in isolation
2. **Integration Tests:** Test API endpoints with real database
3. **Manual Verification:** Test infrastructure changes (migrations, Docker setup)

---

## Unit Testing Standards

### When to Write Unit Tests

Write unit tests for:
- **Business logic functions** (validation, data transformation, calculations)
- **Configuration loading** (environment variables, settings validation)
- **Utility functions** (key generation, parsing, formatting)
- **Authentication logic** (key validation, admin checks)

**Do NOT test:**
- FastAPI framework behavior (routing, middleware)
- Third-party libraries (Pydantic, asyncpg, structlog)
- Database operations (use integration tests instead)

### Unit Test Structure

```python
# tests/unit/test_module.py
import pytest
from app.module import function_to_test

def test_function_happy_path():
    """Test the normal, expected behavior"""
    result = function_to_test(valid_input)
    assert result == expected_output

def test_function_invalid_input():
    """Test error handling with invalid data"""
    with pytest.raises(ValueError) as exc_info:
        function_to_test(invalid_input)
    assert "expected error message" in str(exc_info.value)
```

**Key Patterns:**
- One test per scenario (happy path, error cases)
- Clear test names describing what is tested
- Use docstrings to explain WHY the test exists
- Keep setup minimal (no complex fixtures unless necessary)

### Example: Configuration Testing (Story 1.5)

```python
# Test required field validation
def test_settings_requires_database_url(monkeypatch):
    """DATABASE_URL is required - app should fail fast if missing"""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ValidationError) as exc_info:
        Settings()
    assert "database_url" in str(exc_info.value)

# Test default values
def test_settings_has_default_log_level():
    """LOG_LEVEL defaults to INFO if not set"""
    settings = Settings(database_url="postgresql://test")
    assert settings.log_level == "INFO"
```

**Why This Works:**
- Tests validate actual requirements (DATABASE_URL required)
- Tests document expected behavior (defaults)
- Tests catch configuration bugs early (fail fast)

---

## Integration Testing Standards

### When to Write Integration Tests

Write integration tests for:
- **API endpoints** (POST /execute, GET /health, admin endpoints)
- **Database operations** (CRUD, queries, transactions)
- **Authentication flows** (service keys, admin keys)
- **CORS configuration** (preflight, headers, origins)

### Integration Test Setup

```python
# tests/integration/conftest.py
import pytest
import asyncpg
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.fixture
async def test_db():
    """Provide real database connection for tests"""
    conn = await asyncpg.connect(
        "postgresql://taskuser:taskpass@localhost:5435/taskmanager_dev"
    )
    yield conn
    await conn.close()

@pytest.fixture
async def client():
    """Provide HTTP client for API testing"""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

@pytest.fixture(autouse=True)
async def cleanup_test_data(test_db):
    """Clean up test data before AND after each test"""
    await test_db.execute("DELETE FROM tasks WHERE user_id LIKE 'test-%'")
    yield
    await test_db.execute("DELETE FROM tasks WHERE user_id LIKE 'test-%'")
```

**Key Principles:**
- Use **real database** (not mocks) to catch SQL errors
- Use **test prefixes** (`test-` in user_id) for easy cleanup
- **Clean up before AND after** tests (prevents test pollution)
- Use **ASGITransport** for proper async client support

### Example: Admin Endpoint Testing (Story 2.2)

```python
@pytest.mark.asyncio
async def test_create_service_key_success(client, test_db):
    """POST /admin/service-keys creates a new service key"""
    response = await client.post(
        "/admin/service-keys",
        headers={"X-Admin-Key": "dev-admin-key-12345"},
        json={"key_name": "test-client", "environment": "dev"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["key_name"] == "test-client"
    assert data["service_key"].startswith("sk_dev_")
    
    # Verify database state
    row = await test_db.fetchrow(
        "SELECT * FROM service_api_keys WHERE key_name = $1",
        "test-client"
    )
    assert row is not None
    assert row['active'] is True
```

**Why This Works:**
- Tests full request/response cycle (HTTP → database)
- Tests both API response AND database state
- Uses real authentication headers (catches auth bugs)

### Example: CORS Testing (Story 2.3)

```python
@pytest.mark.asyncio
async def test_cors_preflight_options_request(client):
    """Browser preflight request returns correct CORS headers"""
    response = await client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "X-Service-Key, Content-Type",
        }
    )
    
    assert response.status_code == 200
    assert response.headers["Access-Control-Allow-Origin"] == "http://localhost:3000"
    assert "POST" in response.headers["Access-Control-Allow-Methods"]
```

**Why This Works:**
- Tests real browser behavior (OPTIONS preflight)
- Tests CORS headers correctly configured
- Catches integration issues between FastAPI and CORSMiddleware

---

## Test Naming Conventions

### Good Test Names

✅ `test_create_service_key_duplicate_name` - Clear scenario  
✅ `test_validate_service_key_expired` - Specific edge case  
✅ `test_cors_disallowed_origin` - Clear behavior description

### Bad Test Names

❌ `test_1` - No context  
❌ `test_service_keys` - Too vague  
❌ `test_everything` - Not specific

**Pattern:** `test_{function_or_endpoint}_{scenario}`

---

## Mocking Guidelines

### When to Mock

Mock **only when necessary**:
- External API calls (Cat House, third-party services)
- Time-sensitive functions (datetime.now)
- Expensive operations (file I/O, network calls)

### When NOT to Mock

**Do NOT mock:**
- Database operations (use real database in tests)
- Pydantic validation (use real models)
- FastAPI dependencies (use dependency_overrides instead)

### Good Mocking Example

```python
def test_service_key_generation_uniqueness():
    """Generated keys should be unique"""
    keys = [generate_service_key('prod') for _ in range(100)]
    assert len(set(keys)) == 100  # All unique
```

**No mocking needed** - tests real function behavior

### Dependency Overrides (Better than Mocking)

```python
# GOOD: Use FastAPI dependency_overrides
async def mock_validate_service_key():
    return "test-service"

app.dependency_overrides[validate_service_key] = mock_validate_service_key

# BAD: Use @patch decorator
@patch("app.commands.router.validate_service_key")
def test_endpoint(mock_validate):
    # Fragile, breaks with refactoring
```

---

## pytest Configuration

### Required pytest.ini Settings

```ini
[pytest]
# Async test support
asyncio_mode = auto
asyncio_default_fixture_loop_scope = function

# Test markers (prevents warnings)
markers =
    unit: Unit tests (fast, no external dependencies)
    integration: Integration tests (requires database)
    slow: Slow tests (optional, for full test runs)

# Test discovery
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

### Running Tests

```bash
# All tests
pytest

# Only unit tests (fast)
pytest -m unit

# Only integration tests
pytest -m integration

# With coverage report
pytest --cov=app --cov-report=term-missing

# Verbose output
pytest -v
```

---

## Common Patterns

### Pattern 1: Database Cleanup

```python
@pytest.fixture(autouse=True)
async def cleanup_test_data(test_db):
    """Clean before and after each test"""
    await test_db.execute("DELETE FROM tasks WHERE user_id LIKE 'test-%'")
    yield
    await test_db.execute("DELETE FROM tasks WHERE user_id LIKE 'test-%'")
```

**Why autouse=True:** Runs automatically for every test, prevents forgotten cleanup

### Pattern 2: Test Data Prefixes

```python
# Use test- prefix for easy identification and cleanup
test_user_id = "test-user-123"
test_key_name = "test-client"
```

**Benefit:** Easy to find and delete test data, clear distinction from real data

### Pattern 3: Validation Error Testing

```python
def test_invalid_input_raises_error():
    """Invalid input should raise ValidationError with clear message"""
    with pytest.raises(ValidationError) as exc_info:
        Model(invalid_field="bad")
    assert "expected error" in str(exc_info.value)
```

**Why:** Tests both that error is raised AND message is helpful

### Pattern 4: Event Loop Management

```python
# In conftest.py
@pytest.fixture(scope="function")
async def test_client():
    """Recreate client for each test (prevents event loop conflicts)"""
    async with AsyncClient(transport=ASGITransport(app=app)) as client:
        yield client
```

**Why scope="function":** Prevents "Event loop is closed" errors

---

## Testing Anti-Patterns

### ❌ Don't Test Framework Behavior

```python
# BAD: Testing FastAPI routing
def test_fastapi_routes_requests_correctly():
    # FastAPI already tests this
```

### ❌ Don't Test Third-Party Libraries

```python
# BAD: Testing Pydantic validation
def test_pydantic_validates_fields():
    # Pydantic already tests this
```

### ❌ Don't Over-Mock

```python
# BAD: Mocking everything
@patch("app.database.asyncpg.connect")
@patch("app.auth.validate_service_key")
@patch("app.models.task.TaskCreate")
def test_create_task(mock1, mock2, mock3):
    # Not testing real behavior anymore
```

**Better:** Use real database, real models, real dependencies

### ❌ Don't Write Brittle Tests

```python
# BAD: Testing exact SQL query string
assert query == "SELECT * FROM tasks WHERE user_id = $1"

# GOOD: Test result, not implementation
result = await db.fetchrow("...", user_id)
assert result['title'] == expected_title
```

---

## Manual Verification Checklist

Some changes are better verified manually than with automated tests:

### Infrastructure Changes
- [ ] Database migrations (run upgrade/downgrade cycle)
- [ ] Docker configuration (start containers, verify ports)
- [ ] Environment variables (test with missing/invalid values)

### CORS Configuration
- [ ] Use browser DevTools to verify CORS headers
- [ ] Test preflight requests with curl -v
- [ ] Test disallowed origins return no CORS headers

### Logging
- [ ] Check docker logs for structured JSON output
- [ ] Verify log fields include required context
- [ ] Test log levels (DEBUG, INFO, ERROR)

---

## Test Coverage Goals

**Target Coverage: 80%+ overall**

### Coverage by Component

- **Business Logic:** 100% (critical)
- **API Endpoints:** 90%+ (high priority)
- **Configuration:** 100% (fail-fast validation)
- **Database Models:** 80%+ (covered by integration tests)
- **Utilities:** 100% (easy to test)

### Coverage Tools

```bash
# Generate coverage report
pytest --cov=app --cov-report=html

# View report
open htmlcov/index.html
```

**Focus on:**
- Uncovered branches (if statements not tested)
- Uncovered error paths (exception handling)
- Critical business logic gaps

---

## Test Maintenance

### When Tests Fail

1. **Read the error message** - pytest output is usually clear
2. **Check test isolation** - does test depend on external state?
3. **Check database cleanup** - leftover data from previous test?
4. **Check async fixtures** - event loop scope correct?

### When to Update Tests

Update tests when:
- Requirements change (AC updated)
- Bugs found (add regression test)
- Refactoring changes behavior (not implementation)

**Don't update tests when:**
- Refactoring doesn't change behavior
- Implementation details change (same result)

---

## Key Takeaways

1. **Test behavior, not implementation** - Tests should survive refactoring
2. **Use real dependencies** - Database, Pydantic, FastAPI (not mocks)
3. **Keep tests simple** - Future developers should understand them
4. **Clean up test data** - Use prefixes and autouse fixtures
5. **Focus on edge cases** - Happy path is obvious, test the errors
6. **Fast feedback** - Unit tests run in seconds, integration tests in minutes

---

## Example Test File Structure

```python
# tests/integration/test_feature.py
import pytest
from httpx import AsyncClient

# Test class for organization (optional)
class TestFeature:
    """Tests for feature X"""
    
    @pytest.mark.asyncio
    async def test_happy_path(self, client, test_db):
        """Feature works with valid input"""
        # Arrange: Set up test data
        # Act: Call API/function
        # Assert: Verify behavior
        
    @pytest.mark.asyncio
    async def test_error_case(self, client):
        """Feature handles invalid input correctly"""
        # Arrange, Act, Assert
```

---

**Document Maintenance:** Update this document when new testing patterns emerge or when common issues are resolved.
