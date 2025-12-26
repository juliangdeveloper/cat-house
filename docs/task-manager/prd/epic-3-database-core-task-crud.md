# Epic 3: Database & Core Task CRUD

**Goal:** Implement tasks database schema with migration, and deliver complete CRUD operations for tasks via command-based routing with user-scoped data access and data persistence using Service API Key authentication.

**Prerequisites (Already Completed):**
- ✅ Story 2.1: Alembic migration system configured
- ✅ Story 2.1: Database connection pool (`app/database.py`) implemented
- ✅ Story 2.1: `validate_service_key` dependency for authentication
- ✅ Story 2.1: `service_api_keys` table created and indexed
- ✅ Story 2.2: Service key generation and admin endpoints functional

**This Epic Delivers:**
- Tasks table schema with proper indexing
- Command router (`POST /execute`) with action-based routing
- Five task handlers: create-task, list-tasks, get-task, update-task, delete-task
- User-scoped data access (tasks filtered by user_id from Cat House)

## Story 3.1: Task Schema & Migration System

As a **developer**,  
I want **a database schema for tasks with a migration system**,  
so that **database changes are versioned and repeatable across environments**.

**Note:** Alembic migration system was already initialized in Story 2.1. The `service_api_keys` table was already created in Story 2.1 migration `3d76e0c7a711`. This story focuses on creating the `tasks` table only.

**Acceptance Criteria:**
1. ✅ Create Alembic migration system and initialize configuration - **Already completed in Story 2.1**
2. ~~Create service_api_keys table~~ **REMOVED - Already exists from Story 2.1**
3. Create tasks table with columns: id (UUID), user_id (VARCHAR), title (VARCHAR, required), description (TEXT, nullable), status (VARCHAR), priority (VARCHAR), created_at (TIMESTAMPTZ), completed_at (TIMESTAMPTZ, nullable), due_date (TIMESTAMPTZ, nullable)
4. Add indexes on user_id and (user_id, status) for query performance
5. Migration can be executed via command (alembic upgrade head)
6. Migration system supports rollback capability (alembic downgrade)
7. Document migration commands in README

**Implementation Note:** Use `alembic revision -m "create_tasks_table"` to generate new migration file. The migration should ONLY create the tasks table and its indexes.

## Story 3.2: Command Router & Request Models

As a **developer**,  
I want **a command router with standardized request/response models**,  
so that **I can implement action handlers following the Command Pattern**.

**Note:** The `validate_service_key` dependency was already implemented in Story 2.1 (`app/auth.py`) and is fully tested. This story will use that existing dependency for authentication.

**Acceptance Criteria:**
1. Create `app/commands/models.py` with Pydantic models:
   - `CommandRequest` with fields: action (str), user_id (str), payload (dict)
   - `CommandResponse` base model for standardized responses
2. Create `app/commands/router.py` with POST /execute endpoint
3. Endpoint uses existing `validate_service_key` dependency from Story 2.1 for X-Service-Key authentication
4. Endpoint extracts action from CommandRequest and routes to handler
5. Router maintains ACTION_HANDLERS dictionary mapping action names to handler functions
6. Router returns 404 for unknown actions with clear error message: `{"error": "Unknown action: {action}"}`
7. Router returns 400 for invalid CommandRequest payloads with validation details
8. Router logs action, user_id, and key_name for monitoring
9. Create `app/commands/handlers/__init__.py` for handler modules

**Implementation Reference:** Import `validate_service_key` from `app.auth` (already implemented and tested in Story 2.1).

## Story 3.3: Task Command Handlers (Create & List)

As a **user**,  
I want **to create and list tasks via command actions**,  
so that **I can manage my task list through the Cat House interface**.

**Acceptance Criteria:**
1. Create `app/commands/handlers/tasks.py` module
2. Implement `create_task_handler(user_id: str, payload: dict, db)`:
   - Accepts payload: `{ title, description?, status?, priority?, due_date? }`
   - Validates required fields (title) and returns 400 for invalid data
   - Creates task with user_id from command + generated UUID + created_at timestamp
   - Returns created task object with all fields
3. Implement `list_tasks_handler(user_id: str, payload: dict, db)`:
   - Accepts payload: `{ status?: string }` for optional filtering
   - Queries tasks WHERE user_id = command.user_id
   - Applies status filter if provided in payload
   - Returns array of task objects
4. Both handlers use asyncpg for database operations
5. Both handlers include error handling with descriptive messages
6. Register both handlers in ACTION_HANDLERS dictionary: `"create-task": create_task_handler`, `"list-tasks": list_tasks_handler`
7. Handlers return dict responses compatible with CommandResponse model

## Story 3.4: Task Command Handlers (Get, Update, Delete)

As a **user**,  
I want **to retrieve, update, and delete tasks via command actions**,  
so that **I can manage individual tasks through the Cat House interface**.

**Acceptance Criteria:**
1. Implement `get_task_handler(user_id: str, payload: dict, db)` in `app/commands/handlers/tasks.py`:
   - Accepts payload: `{ task_id: uuid }`
   - Queries task by ID (no user ownership check - trusts Cat House)
   - Returns 404 if task not found: `{"error": "Task not found", "task_id": "..."}`
   - Returns task object with all fields
2. Implement `update_task_handler(user_id: str, payload: dict, db)`:
   - Accepts payload: `{ task_id: uuid, title?, description?, status?, priority?, due_date? }`
   - Updates only provided fields using partial update query
   - Automatically sets completed_at = NOW() when status changes to "completed"
   - Returns 404 if task not found
   - Returns updated task object
3. Implement `delete_task_handler(user_id: str, payload: dict, db)`:
   - Accepts payload: `{ task_id: uuid }`
   - Deletes task by ID (no user ownership check - trusts Cat House)
   - Returns 404 if task not found
   - Returns success response: `{ "success": true, "deleted_id": "uuid" }`
4. Register all handlers in ACTION_HANDLERS dictionary: `"get-task": get_task_handler`, `"update-task": update_task_handler`, `"delete-task": delete_task_handler`
5. All handlers include comprehensive error handling with appropriate HTTP status codes
6. Handlers are unit testable independent of HTTP layer

---

## Architecture Notes

### Stats Action Placement (get-stats)

**Decision:** The `get-stats` action is intentionally deferred to **Epic 4** for the following architectural reasons:

1. **Command Pattern Consistency:** Epic 4 implements `get-stats` as a command action via `/execute` endpoint, following the Universal Command Pattern established in this epic
2. **User-Scoped Authentication:** Stats require X-Service-Key authentication and user_id isolation, consistent with other CRUD operations
3. **API Contract Standardization:** Epic 4 focuses on standardizing the response format for Cat House integration and comprehensive API documentation
4. **Business Logic Separation:** Statistics calculation logic is developed as an independent service layer for testability

**Pattern Established:** The `get-stats` action follows the same handler signature and routing pattern as task CRUD operations: `async def get_stats_handler(user_id: str, payload: dict, db) -> dict`

**Reference:** See `docs/prd/requirements.md` FR4 for stats requirements and `docs/architecture/command-pattern-architecture.md` for Universal Command Pattern.

---
