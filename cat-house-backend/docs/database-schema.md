# Database Schema Design

## Entity Relationship Diagram

\\\mermaid
erDiagram
    USERS ||--o{ CATS : develops
    USERS ||--o{ INSTALLATIONS : owns
    CATS ||--o{ PERMISSIONS : requires
    CATS ||--o{ INSTALLATIONS : installed_as
    INSTALLATIONS ||--o{ INSTALLATION_PERMISSIONS : has
    PERMISSIONS ||--o{ INSTALLATION_PERMISSIONS : granted_in

    USERS {
        uuid id PK
        varchar email UK
        varchar password_hash
        varchar role
        varchar display_name
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    CATS {
        uuid id PK
        uuid developer_id FK
        varchar name
        text description
        varchar version
        varchar endpoint_url
        varchar status
        timestamp created_at
        timestamp updated_at
    }

    PERMISSIONS {
        uuid id PK
        uuid cat_id FK
        varchar permission_type
        text description
        boolean required
        timestamp created_at
        timestamp updated_at
    }

    INSTALLATIONS {
        uuid id PK
        uuid user_id FK
        uuid cat_id FK
        varchar instance_name
        jsonb config
        varchar status
        timestamp installed_at
        timestamp last_interaction_at
        timestamp created_at
        timestamp updated_at
    }

    INSTALLATION_PERMISSIONS {
        uuid installation_id PK,FK
        uuid permission_id PK,FK
        boolean granted
        timestamp granted_at
    }
\\\

## Table Structures

### users
**Owner:** auth-service (logical)
**Purpose:** Core user authentication and profile management

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier |
| email | VARCHAR(255) | UNIQUE, NOT NULL, INDEX | User email address |
| password_hash | VARCHAR(255) | NOT NULL | Bcrypt hashed password |
| role | VARCHAR(20) | NOT NULL | 'player', 'developer', 'admin' |
| display_name | VARCHAR(100) | NULL | User's display name |
| is_active | BOOLEAN | DEFAULT true | Account active status |
| created_at | TIMESTAMP | NOT NULL, DEFAULT now() | Record creation time |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT now() | Record last update time |

**Indexes:**
- PRIMARY KEY on id
- UNIQUE INDEX on email (for fast login lookups)
- INDEX on (role, is_active) for admin queries

### cats
**Owner:** catalog-service (logical)
**Purpose:** Cat metadata and discovery

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier |
| developer_id | UUID | FOREIGN KEY (users.id) | Cat developer |
| name | VARCHAR(100) | NOT NULL | Cat name |
| description | TEXT | NULL | Cat description |
| version | VARCHAR(20) | NULL | Semantic version |
| endpoint_url | VARCHAR(500) | NOT NULL | Cat API endpoint |
| status | VARCHAR(20) | NOT NULL | 'draft', 'published', 'suspended' |
| created_at | TIMESTAMP | NOT NULL, DEFAULT now() | Record creation time |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT now() | Record last update time |

**Indexes:**
- PRIMARY KEY on id
- FOREIGN KEY on developer_id
- INDEX on status for filtering
- INDEX on (developer_id, status) for developer dashboard

### permissions
**Owner:** catalog-service (logical)
**Purpose:** Cat permission definitions

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier |
| cat_id | UUID | FOREIGN KEY (cats.id) ON DELETE CASCADE | Associated cat |
| permission_type | VARCHAR(50) | NOT NULL | 'storage', 'notification', 'external_api' |
| description | TEXT | NULL | Permission description |
| required | BOOLEAN | DEFAULT false | Is permission mandatory |
| created_at | TIMESTAMP | NOT NULL, DEFAULT now() | Record creation time |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT now() | Record last update time |

**Indexes:**
- PRIMARY KEY on id
- FOREIGN KEY on cat_id with CASCADE DELETE
- INDEX on (cat_id, permission_type)

### installations
**Owner:** installation-service (logical)
**Purpose:** User cat installations

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier |
| user_id | UUID | FOREIGN KEY (users.id) | Cat owner |
| cat_id | UUID | FOREIGN KEY (cats.id) | Installed cat |
| instance_name | VARCHAR(100) | NULL | User-defined instance name |
| config | JSONB | NULL | Installation-specific configuration |
| status | VARCHAR(20) | NOT NULL | 'active', 'paused', 'uninstalled' |
| installed_at | TIMESTAMP | NOT NULL, DEFAULT now() | Installation time |
| last_interaction_at | TIMESTAMP | NULL | Last usage time |
| created_at | TIMESTAMP | NOT NULL, DEFAULT now() | Record creation time |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT now() | Record last update time |

**Constraints:**
- UNIQUE (user_id, cat_id, instance_name) - prevent duplicate installations

**Indexes:**
- PRIMARY KEY on id
- FOREIGN KEY on user_id
- FOREIGN KEY on cat_id
- UNIQUE INDEX on (user_id, cat_id, instance_name)
- INDEX on (user_id, status) for user dashboard
- INDEX on last_interaction_at for cleanup jobs

### installation_permissions
**Owner:** installation-service (logical)
**Purpose:** Track granted permissions per installation

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| installation_id | UUID | FOREIGN KEY (installations.id) ON DELETE CASCADE, PRIMARY KEY | Installation reference |
| permission_id | UUID | FOREIGN KEY (permissions.id) ON DELETE CASCADE, PRIMARY KEY | Permission reference |
| granted | BOOLEAN | DEFAULT false | Permission granted status |
| granted_at | TIMESTAMP | NULL | When permission was granted |

**Indexes:**
- COMPOSITE PRIMARY KEY on (installation_id, permission_id)
- FOREIGN KEY on installation_id with CASCADE DELETE
- FOREIGN KEY on permission_id with CASCADE DELETE

## Design Decisions

### UUID Primary Keys
**Rationale:** 
- Distributed system friendly (no sequence coordination)
- Non-sequential (security by obscurity)
- Globally unique across services
- Same size as BIGINT (128 bits)

### Timestamps
**Rationale:**
- All tables have created_at/updated_at for audit trail
- UTC timezone for consistency
- Automatic updates via SQLAlchemy onupdate

### JSONB for Configuration
**Rationale:**
- Flexible schema for cat-specific config
- Indexable and queryable with PostgreSQL
- Validation handled at application layer

### Soft Deletes
**Decision:** NOT implemented initially
**Rationale:**
- Simplifies queries (no WHERE deleted_at IS NULL everywhere)
- Can add later if audit requirements emerge
- Use status fields instead (is_active, status='uninstalled')

### Cascading Deletes
**Applied to:**
- permissions ON DELETE CASCADE cats (permissions tied to cat lifecycle)
- installation_permissions ON DELETE CASCADE installations (cleanup)

**NOT applied to:**
- users  cats (preserve cat ownership history)
- users  installations (preserve installation history)

## Index Strategy

### Query Patterns Optimized:
1. **User login:** email lookup (UNIQUE INDEX on users.email)
2. **Cat discovery:** status filtering (INDEX on cats.status)
3. **User dashboard:** user's installations (INDEX on installations.user_id, status)
4. **Developer dashboard:** developer's cats (INDEX on cats.developer_id, status)
5. **Permission checks:** installation permissions (COMPOSITE PK serves as index)

### Composite Indexes:
- (role, is_active) on users - admin queries
- (developer_id, status) on cats - developer dashboard
- (user_id, status) on installations - user dashboard
- (cat_id, permission_type) on permissions - permission lookups

## Shared Database Architecture

**Decision:** Single database cathouse shared by all services

**Benefits:**
- Simplified deployment (one connection string)
- ACID transactions across entities
- No distributed transaction complexity
- Foreign key constraints enforced at database level
- Easier to maintain consistency

**Service Boundaries (Logical Ownership):**
- **auth-service:** Manages migrations, owns users table
- **catalog-service:** Owns cats and permissions tables
- **installation-service:** Owns installations and installation_permissions tables
- **proxy-service:** Read-only access for request validation

**Migration Strategy:**
- Only auth-service contains Alembic configuration
- All services import models and connect to same database
- Single source of truth for schema changes

## Performance Considerations

### Connection Pooling (Neon Free Tier: 10 connections max)
- auth-service: pool_size=2, max_overflow=1 (max 3)
- catalog-service: pool_size=2, max_overflow=1 (max 3)
- installation-service: pool_size=2, max_overflow=1 (max 3)
- proxy-service: pool_size=1, max_overflow=0 (max 1)
- **Total: 10 connections**

### Query Optimization
- Use SELECT specific columns (not SELECT *)
- Eager load relationships with selectinload()
- Implement pagination for list endpoints
- Use database-level defaults where possible

### Future Scaling Considerations
- Add read replicas if read-heavy
- Implement caching layer (Redis) for frequently accessed data
- Monitor slow queries with pg_stat_statements
- Consider table partitioning for large tables (installations, audit logs)
