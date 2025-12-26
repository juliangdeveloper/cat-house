# Epic 2: Authentication & Security

**Goal:** Implement Service API Key authentication for validating client applications (Cat House, mobile apps), create reusable authentication utilities, and configure CORS for cross-origin requests. This epic must be completed before implementing the command router to ensure proper security from the start.

## Story 2.1: Database Schema & Service Key Dependency

As a **developer**,  
I want **Service API Key database schema and validation dependency**,  
so that **only authorized client applications (Cat House) can access the /execute endpoint**.

**Acceptance Criteria:**
1. Create Alembic migration for service_api_keys table with columns: id (UUID PRIMARY KEY), key_name (VARCHAR UNIQUE NOT NULL), api_key (VARCHAR UNIQUE NOT NULL), active (BOOLEAN DEFAULT true), created_at (TIMESTAMPTZ DEFAULT NOW()), expires_at (TIMESTAMPTZ nullable)
2. Add index on api_key column with WHERE active = true for performance
3. Run migration to create table in development database
4. Create `validate_service_key` dependency function in app/auth.py that extracts X-Service-Key header
5. Dependency validates service key against service_api_keys table (active = true AND (expires_at IS NULL OR expires_at > NOW()))
6. Dependency returns key_name for logging/monitoring purposes
7. Dependency raises HTTPException(401) for missing, invalid, inactive, or expired service keys
8. Dependency is reusable via FastAPI dependency injection pattern

## Story 2.2: Admin Endpoints & Key Management

As a **developer**,  
I want **admin endpoints to generate and rotate service API keys**,  
so that **I can manage client application access securely**.

**Acceptance Criteria:**
1. Create helper function `generate_service_key(environment: str)` that generates cryptographically secure keys with prefix 'sk_prod_' or 'sk_dev_' (32 random bytes, hex-encoded)
2. Create `validate_admin_key` dependency that validates X-Admin-Key header against settings.admin_api_key, raises HTTPException(401) if missing or invalid
3. Create admin endpoint POST /admin/service-keys (protected by validate_admin_key dependency):
   - Request body: `{ "key_name": "cat-house-prod", "environment": "prod" }`
   - Response: `{ "id": "uuid", "key_name": "...", "service_key": "sk_prod_...", "created_at": "..." }`
   - Returns 400 if key_name already exists
4. Create admin endpoint POST /admin/rotate-key (protected by validate_admin_key dependency):
   - Request body: `{ "key_name": "cat-house-prod" }`
   - Response: `{ "new_key": "sk_prod_...", "old_key_expires_at": "ISO-date" }`
   - Generates new key, marks old key with expires_at = NOW() + 7 days (grace period)
5. All functions include type hints and docstrings
6. Unit tests verify:
   - Key generation format (sk_prod_xxx, sk_dev_xxx with 64 hex chars)
   - Admin key validation rejects invalid/missing X-Admin-Key
   - Service key validation rejects expired keys
   - Admin endpoints require valid admin key

## Story 2.3: CORS Configuration for Cat House Integration

As a **Cat House Platform**,  
I want **CORS properly configured for production**,  
so that **I can make API requests from my web application**.

**Acceptance Criteria:**
1. Update CORSMiddleware in app/main.py to explicitly allow X-Service-Key and Content-Type headers
2. Update allow_methods to specific methods: ["GET", "POST", "PATCH", "DELETE", "OPTIONS"]
3. Verify CORS origins are loaded from settings.get_cors_origins_list() (already configured in Story 1.4/1.5)
4. Add comment documenting that allow_headers and allow_methods wildcards (*) are replaced with explicit values for production
5. Test preflight OPTIONS request returns correct Access-Control-Allow-* headers
6. Update README.md CORS section to document X-Service-Key header requirement and production restrictions
7. Verify Cat House origin (https://cathouse.gamificator.click) is in CORS_ORIGINS environment variable

---
