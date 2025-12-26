# Requirements

## Functional Requirements

**FR1:** The API shall provide a command action (`create-task`) for creating tasks with title, description, status, priority, and due_date fields

**FR2:** The API shall provide a command action (`list-tasks`) for listing all tasks for the authenticated user with optional status filtering via payload parameter

**FR3:** The API shall provide command actions (`get-task`, `update-task`, `delete-task`) for retrieving, updating, and deleting individual tasks by ID

**FR4:** The API shall provide a command action (`get-stats`) that returns aggregated metrics including total tasks, pending tasks, completed tasks, and completion rate

**FR5:** The API shall persist all task data with timestamps for created_at, completed_at, and due_date

**FR6:** The API shall support user-scoped data access via user_id provided in command payload (validated by Cat House), with permission checks enforced by Cat House gateway

**FR7:** The API shall support task status transitions (e.g., pending → in_progress → completed)

## Non-Functional Requirements

**NFR1:** The API shall require Service API Key authentication (via X-Service-Key header) for the `/execute` endpoint, with Cat House responsible for JWT validation and user_id extraction

**NFR2:** The API shall respond to requests within 200ms for standard CRUD operations under normal load

**NFR3:** The API shall use a command-based routing pattern with a single `/execute` endpoint, accepting standardized command objects with action-based routing and returning JSON responses with appropriate status codes

**NFR4:** The API shall be completely stateless to enable horizontal scaling

**NFR5:** The API shall provide comprehensive API documentation (OpenAPI/Swagger)

**NFR6:** The API shall implement structured logging for debugging and monitoring

**NFR7:** The API shall be testable via standard API testing tools (Postman, curl, etc.)

---
