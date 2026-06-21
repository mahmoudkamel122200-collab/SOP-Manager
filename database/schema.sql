-- =============================================================================
-- FACTORY MANAGEMENT SYSTEM — DATABASE SCHEMA
-- PostgreSQL 15+
-- Modules: Identity & Access Management | SOP Document Management | Warehouse
-- =============================================================================

-- ---------------------------------------------------------------------------
-- EXTENSIONS
-- ---------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS "pgcrypto";   -- gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS "citext";     -- case-insensitive text for emails

-- ---------------------------------------------------------------------------
-- ENUMS
-- ---------------------------------------------------------------------------

CREATE TYPE permission_level_enum AS ENUM (
    'READ',
    'WRITE',
    'ADMIN'
);

CREATE TYPE document_status_enum AS ENUM (
    'DRAFT',
    'UNDER_REVIEW',
    'APPROVED',
    'ARCHIVED',
    'REJECTED'
);

CREATE TYPE item_status_enum AS ENUM (
    'AVAILABLE',
    'RESERVED',
    'CONSUMED',
    'DAMAGED',
    'QUARANTINE'
);

CREATE TYPE audit_action_enum AS ENUM (
    'LOGIN',
    'LOGOUT',
    'CREATE',
    'READ',
    'UPDATE',
    'DELETE',
    'UPLOAD_DOCUMENT',
    'OPEN_DOCUMENT',
    'ARCHIVE_DOCUMENT',
    'MOVE_ITEM',
    'ADD_ITEM',
    'REMOVE_ITEM',
    'CREATE_LOCATION',
    'CREATE_ITEM',
    'SEARCH_ITEM',
    'VIEW_HISTORY',
    'GRANT_ACCESS',
    'REVOKE_ACCESS'
);

CREATE TYPE audit_module_enum AS ENUM (
    'IAM',
    'SOP',
    'WAREHOUSE',
    'SYSTEM'
);


-- =============================================================================
-- MODULE 1 — IDENTITY & ACCESS MANAGEMENT (IAM)
-- =============================================================================

-- ---------------------------------------------------------------------------
-- TABLE: roles
-- ---------------------------------------------------------------------------
CREATE TABLE roles (
    id          UUID            DEFAULT gen_random_uuid() PRIMARY KEY,
    name        VARCHAR(50)     NOT NULL,
    description TEXT,
    created_at  TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_roles_name UNIQUE (name),
    CONSTRAINT chk_roles_name_not_empty CHECK (TRIM(name) <> '')
);

COMMENT ON TABLE  roles              IS 'Stores system roles for RBAC (Role-Based Access Control).';
COMMENT ON COLUMN roles.id          IS 'Surrogate primary key — UUID v4.';
COMMENT ON COLUMN roles.name        IS 'Unique role identifier (e.g., ADMIN, EMPLOYEE).';
COMMENT ON COLUMN roles.description IS 'Human-readable description of the role.';
COMMENT ON COLUMN roles.created_at  IS 'UTC timestamp when the role was created.';


-- ---------------------------------------------------------------------------
-- TABLE: users
-- ---------------------------------------------------------------------------
CREATE TABLE users (
    id            UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
    username      VARCHAR(50) NOT NULL,
    email         CITEXT      NOT NULL,
    password_hash TEXT        NOT NULL,
    full_name     VARCHAR(150),
    role_id       UUID        NOT NULL,
    is_active     BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_login    TIMESTAMPTZ,

    CONSTRAINT uq_users_username UNIQUE (username),
    CONSTRAINT uq_users_email    UNIQUE (email),

    CONSTRAINT fk_users_role
        FOREIGN KEY (role_id)
        REFERENCES roles(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT chk_users_username_len  CHECK (LENGTH(TRIM(username)) >= 3),
    CONSTRAINT chk_users_email_format  CHECK (email ~* '^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$'),
    CONSTRAINT chk_users_password_len  CHECK (LENGTH(password_hash) >= 60)   -- bcrypt minimum
);

COMMENT ON TABLE  users               IS 'Stores system users and their authentication credentials.';
COMMENT ON COLUMN users.id            IS 'Surrogate primary key — UUID v4.';
COMMENT ON COLUMN users.username      IS 'Unique login handle (min 3 chars).';
COMMENT ON COLUMN users.email         IS 'Case-insensitive unique email address.';
COMMENT ON COLUMN users.password_hash IS 'bcrypt/argon2 hashed password — plain text is NEVER stored.';
COMMENT ON COLUMN users.role_id       IS 'FK to roles.id — determines RBAC permissions.';
COMMENT ON COLUMN users.is_active     IS 'Soft-disable flag; FALSE blocks authentication.';
COMMENT ON COLUMN users.last_login    IS 'UTC timestamp of the most recent successful login.';

-- Performance indexes for authentication lookups
CREATE INDEX idx_users_username  ON users (username);
CREATE INDEX idx_users_email     ON users (email);
CREATE INDEX idx_users_role_id   ON users (role_id);
CREATE INDEX idx_users_is_active ON users (is_active) WHERE is_active = TRUE;


-- ---------------------------------------------------------------------------
-- TABLE: sections
-- ---------------------------------------------------------------------------
CREATE TABLE sections (
    id          UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    description TEXT,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_sections_name UNIQUE (name),
    CONSTRAINT chk_sections_name_not_empty CHECK (TRIM(name) <> '')
);

COMMENT ON TABLE  sections             IS 'Represents factory departments (e.g., Production, Labs, Warehouse).';
COMMENT ON COLUMN sections.id          IS 'Surrogate primary key — UUID v4.';
COMMENT ON COLUMN sections.name        IS 'Unique department/section name.';
COMMENT ON COLUMN sections.description IS 'Optional description of the section responsibilities.';
COMMENT ON COLUMN sections.created_at  IS 'UTC timestamp when the section was created.';


-- ---------------------------------------------------------------------------
-- TABLE: user_sections  (Users ←M:N→ Sections)
-- ---------------------------------------------------------------------------
CREATE TABLE user_sections (
    id               UUID                  DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id          UUID                  NOT NULL,
    section_id       UUID                  NOT NULL,
    permission_level permission_level_enum NOT NULL DEFAULT 'READ',
    created_at       TIMESTAMPTZ           NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_user_sections_user_section UNIQUE (user_id, section_id),

    CONSTRAINT fk_user_sections_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    CONSTRAINT fk_user_sections_section
        FOREIGN KEY (section_id)
        REFERENCES sections(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

COMMENT ON TABLE  user_sections                  IS 'Junction table — grants users access to sections with a permission level.';
COMMENT ON COLUMN user_sections.permission_level IS 'READ | WRITE | ADMIN within the given section.';

CREATE INDEX idx_user_sections_user_id    ON user_sections (user_id);
CREATE INDEX idx_user_sections_section_id ON user_sections (section_id);


-- =============================================================================
-- MODULE 2 — SOP DOCUMENT MANAGEMENT
-- =============================================================================

-- ---------------------------------------------------------------------------
-- TABLE: documents
-- ---------------------------------------------------------------------------
CREATE TABLE documents (
    id          UUID                  DEFAULT gen_random_uuid() PRIMARY KEY,
    section_id  UUID                  NOT NULL,
    title       VARCHAR(255)          NOT NULL,
    description TEXT,
    file_path   TEXT                  NOT NULL,
    version     VARCHAR(20)           NOT NULL DEFAULT '1.0',
    uploaded_by UUID                  NOT NULL,
    status      document_status_enum  NOT NULL DEFAULT 'DRAFT',
    created_at  TIMESTAMPTZ           NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_documents_section
        FOREIGN KEY (section_id)
        REFERENCES sections(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_documents_uploader
        FOREIGN KEY (uploaded_by)
        REFERENCES users(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT chk_documents_title_not_empty   CHECK (TRIM(title)     <> ''),
    CONSTRAINT chk_documents_filepath_not_empty CHECK (TRIM(file_path) <> ''),
    CONSTRAINT chk_documents_version_format    CHECK (version ~ '^\d+\.\d+(\.\d+)?$')
);

COMMENT ON TABLE  documents             IS 'SOP document metadata; actual files live in external storage referenced by file_path.';
COMMENT ON COLUMN documents.file_path   IS 'Relative or absolute path / object-storage key (e.g., s3://bucket/key).';
COMMENT ON COLUMN documents.version     IS 'Semantic version string (MAJOR.MINOR or MAJOR.MINOR.PATCH).';
COMMENT ON COLUMN documents.status      IS 'Lifecycle state: DRAFT → UNDER_REVIEW → APPROVED → ARCHIVED/REJECTED.';
COMMENT ON COLUMN documents.uploaded_by IS 'FK to users.id — user who uploaded this version.';

CREATE INDEX idx_documents_section_id  ON documents (section_id);
CREATE INDEX idx_documents_uploaded_by ON documents (uploaded_by);
CREATE INDEX idx_documents_status      ON documents (status);
CREATE INDEX idx_documents_created_at  ON documents (created_at DESC);


-- ---------------------------------------------------------------------------
-- TABLE: audit_logs
-- ---------------------------------------------------------------------------
CREATE TABLE audit_logs (
    id          UUID              DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id     UUID,                         -- nullable: system events have no user
    action      audit_action_enum NOT NULL,
    module      audit_module_enum NOT NULL,
    target_id   UUID,                         -- generic reference to any affected entity
    description TEXT,
    ip_address  INET,
    created_at  TIMESTAMPTZ       NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_audit_logs_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON UPDATE CASCADE
        ON DELETE SET NULL            -- preserve logs even if user is deleted
);

COMMENT ON TABLE  audit_logs            IS 'Immutable audit trail for all significant user and system actions.';
COMMENT ON COLUMN audit_logs.user_id    IS 'Actor — NULL for automated/system events.';
COMMENT ON COLUMN audit_logs.target_id  IS 'UUID of the affected entity (document, item, user …).';
COMMENT ON COLUMN audit_logs.ip_address IS 'Client IP stored as PostgreSQL INET type for subnet queries.';

-- Audit logs are write-heavy; optimise for time-range and user queries
CREATE INDEX idx_audit_logs_user_id    ON audit_logs (user_id);
CREATE INDEX idx_audit_logs_action     ON audit_logs (action);
CREATE INDEX idx_audit_logs_module     ON audit_logs (module);
CREATE INDEX idx_audit_logs_target_id  ON audit_logs (target_id) WHERE target_id IS NOT NULL;
CREATE INDEX idx_audit_logs_created_at ON audit_logs (created_at DESC);


-- =============================================================================
-- MODULE 3 — WAREHOUSE MANAGEMENT
-- =============================================================================

-- ---------------------------------------------------------------------------
-- TABLE: locations
-- ---------------------------------------------------------------------------
CREATE TABLE locations (
    id             UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
    warehouse_name VARCHAR(100) NOT NULL,
    rack           VARCHAR(20)  NOT NULL,
    shelf          VARCHAR(20)  NOT NULL,
    position       VARCHAR(20)  NOT NULL,
    location_code  VARCHAR(50)  NOT NULL,
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_locations_code UNIQUE (location_code),

    CONSTRAINT chk_locations_code_format
        CHECK (location_code ~ '^[A-Z0-9]+-[A-Z0-9]+-[A-Z0-9]+-[A-Z0-9]+$')
);

COMMENT ON TABLE  locations               IS 'Physical warehouse storage positions identified by a composite code.';
COMMENT ON COLUMN locations.warehouse_name IS 'Logical warehouse name (e.g., Warehouse A).';
COMMENT ON COLUMN locations.rack           IS 'Rack identifier within the warehouse (e.g., R01).';
COMMENT ON COLUMN locations.shelf          IS 'Shelf identifier on the rack (e.g., S03).';
COMMENT ON COLUMN locations.position       IS 'Slot/position on the shelf (e.g., P05).';
COMMENT ON COLUMN locations.location_code  IS 'Generated composite unique code: WAREHOUSE-RACK-SHELF-POSITION.';

CREATE INDEX idx_locations_warehouse_name ON locations (warehouse_name);
CREATE INDEX idx_locations_location_code  ON locations (location_code);


-- ---------------------------------------------------------------------------
-- TABLE: items
-- ---------------------------------------------------------------------------
CREATE TABLE items (
    id            UUID             DEFAULT gen_random_uuid() PRIMARY KEY,
    item_code     VARCHAR(20)      NOT NULL,
    material_name VARCHAR(200)     NOT NULL,
    quantity      NUMERIC(12, 3)   NOT NULL DEFAULT 0,
    unit          VARCHAR(20)      NOT NULL,
    location_id   UUID             NOT NULL,
    created_by    UUID             NOT NULL,
    status        item_status_enum NOT NULL DEFAULT 'AVAILABLE',
    created_at    TIMESTAMPTZ      NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_items_item_code UNIQUE (item_code),

    CONSTRAINT fk_items_location
        FOREIGN KEY (location_id)
        REFERENCES locations(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_items_created_by
        FOREIGN KEY (created_by)
        REFERENCES users(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT chk_items_quantity_non_negative CHECK (quantity >= 0),
    CONSTRAINT chk_items_code_format
        CHECK (item_code ~ '^[A-Z]{2}-\d{6}$')      -- e.g. BG-000123
);

COMMENT ON TABLE  items               IS 'Physical materials / bags tracked in the warehouse.';
COMMENT ON COLUMN items.item_code     IS 'Human-readable barcode-style code: PREFIX-NNNNNN (e.g., BG-000123).';
COMMENT ON COLUMN items.quantity      IS 'Current quantity with up to 3 decimal places.';
COMMENT ON COLUMN items.unit          IS 'Unit of measurement (KG, L, PCS, BOX …).';
COMMENT ON COLUMN items.location_id   IS 'Current storage location FK.';
COMMENT ON COLUMN items.created_by    IS 'User who registered this item.';
COMMENT ON COLUMN items.status        IS 'AVAILABLE | RESERVED | CONSUMED | DAMAGED | QUARANTINE.';

CREATE INDEX idx_items_item_code   ON items (item_code);
CREATE INDEX idx_items_location_id ON items (location_id);
CREATE INDEX idx_items_status      ON items (status);
CREATE INDEX idx_items_created_by  ON items (created_by);


-- ---------------------------------------------------------------------------
-- TABLE: movement_logs
-- ---------------------------------------------------------------------------
CREATE TABLE movement_logs (
    id            UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
    item_id       UUID        NOT NULL,
    from_location UUID,                     -- nullable: initial placement has no origin
    to_location   UUID        NOT NULL,
    moved_by      UUID        NOT NULL,
    notes         TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_movement_logs_item
        FOREIGN KEY (item_id)
        REFERENCES items(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    CONSTRAINT fk_movement_logs_from_location
        FOREIGN KEY (from_location)
        REFERENCES locations(id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,

    CONSTRAINT fk_movement_logs_to_location
        FOREIGN KEY (to_location)
        REFERENCES locations(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_movement_logs_moved_by
        FOREIGN KEY (moved_by)
        REFERENCES users(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT chk_movement_logs_different_locations
        CHECK (from_location IS NULL OR from_location <> to_location)
);

COMMENT ON TABLE  movement_logs               IS 'Immutable ledger of every warehouse item movement.';
COMMENT ON COLUMN movement_logs.from_location IS 'Source location — NULL on initial item placement.';
COMMENT ON COLUMN movement_logs.to_location   IS 'Destination location — always required.';
COMMENT ON COLUMN movement_logs.notes         IS 'Optional free-text reason / remarks for the movement.';

CREATE INDEX idx_movement_logs_item_id       ON movement_logs (item_id);
CREATE INDEX idx_movement_logs_from_location ON movement_logs (from_location) WHERE from_location IS NOT NULL;
CREATE INDEX idx_movement_logs_to_location   ON movement_logs (to_location);
CREATE INDEX idx_movement_logs_moved_by      ON movement_logs (moved_by);
CREATE INDEX idx_movement_logs_created_at    ON movement_logs (created_at DESC);


-- =============================================================================
-- UTILITY: updated_at TRIGGER (attach to mutable tables as needed)
-- =============================================================================
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;
