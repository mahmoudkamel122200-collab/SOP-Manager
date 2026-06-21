-- =============================================================================
-- FACTORY MANAGEMENT SYSTEM — SEED DATA
-- Run AFTER schema.sql
-- =============================================================================

BEGIN;

-- ---------------------------------------------------------------------------
-- 1. ROLES
-- ---------------------------------------------------------------------------
INSERT INTO roles (id, name, description) VALUES
    ('00000000-0000-0000-0000-000000000001', 'ADMIN',
     'Full system access — can manage users, documents, warehouse, and settings.'),
    ('00000000-0000-0000-0000-000000000002', 'EMPLOYEE',
     'Standard employee — read access to assigned sections; write access where granted.');


-- ---------------------------------------------------------------------------
-- 2. USERS
-- Password hashes below are Argon2id of:
--   admin    → "Admin@1234"
--   ahmed_ali → "Employee@1234"
-- Generated with: argon2 time_cost=2, memory_cost=65536, parallelism=2
-- ---------------------------------------------------------------------------
INSERT INTO users (id, username, email, password_hash, full_name, role_id, is_active) VALUES
    ('00000000-0000-0000-0001-000000000001',
     'admin',
     'admin@factory.local',
     '$argon2id$v=19$m=65536,t=2,p=2$q0gDpoMUKgpZJeMsl7n/fw$owpFcqtDu/2FQv3FFRtUX2iQsN4e5UJ+Abr0fIjtvJY',  -- Admin@1234
     'System Administrator',
     '00000000-0000-0000-0000-000000000001',
     TRUE),

    ('00000000-0000-0000-0001-000000000002',
     'ahmed_ali',
     'ahmed.ali@factory.local',
     '$argon2id$v=19$m=65536,t=2,p=2$cgcZLkj2xINf1L0dWX++3w$qVquDVaQJDHHi0Ih5/bg4eZ/3xIJ+LFdoq1H211P/oI',  -- Employee@1234
     'Ahmed Ali (Warehouse)',
     '00000000-0000-0000-0000-000000000002',
     TRUE),

    ('00000000-0000-0000-0001-000000000003',
     'fatima_labs',
     'fatima.labs@factory.local',
     '$argon2id$v=19$m=65536,t=2,p=2$cgcZLkj2xINf1L0dWX++3w$qVquDVaQJDHHi0Ih5/bg4eZ/3xIJ+LFdoq1H211P/oI',  -- Employee@1234
     'Fatima (Labs)',
     '00000000-0000-0000-0000-000000000002',
     TRUE),

    ('00000000-0000-0000-0001-000000000004',
     'omar_prod',
     'omar.prod@factory.local',
     '$argon2id$v=19$m=65536,t=2,p=2$cgcZLkj2xINf1L0dWX++3w$qVquDVaQJDHHi0Ih5/bg4eZ/3xIJ+LFdoq1H211P/oI',  -- Employee@1234
     'Omar (Production)',
     '00000000-0000-0000-0000-000000000002',
     TRUE),

    ('00000000-0000-0000-0001-000000000005',
     'sara_quality',
     'sara.quality@factory.local',
     '$argon2id$v=19$m=65536,t=2,p=2$cgcZLkj2xINf1L0dWX++3w$qVquDVaQJDHHi0Ih5/bg4eZ/3xIJ+LFdoq1H211P/oI',  -- Employee@1234
     'Sara (Quality)',
     '00000000-0000-0000-0000-000000000002',
     TRUE);


-- ---------------------------------------------------------------------------
-- 3. SECTIONS (Factory Departments)
-- ---------------------------------------------------------------------------
INSERT INTO sections (id, name, description) VALUES
    ('00000000-0000-0000-0002-000000000001', 'Production',
     'Manages all manufacturing and production line operations.'),
    ('00000000-0000-0000-0002-000000000002', 'Labs',
     'Quality control and chemical analysis laboratory.'),
    ('00000000-0000-0000-0002-000000000003', 'Warehouse',
     'Raw materials and finished goods storage and logistics.'),
    ('00000000-0000-0000-0002-000000000004', 'Quality',
     'Oversees quality assurance processes across all departments.');


-- ---------------------------------------------------------------------------
-- 4. USER_SECTIONS — Access Assignments
-- ---------------------------------------------------------------------------
-- Admin gets ADMIN access to all sections
INSERT INTO user_sections (user_id, section_id, permission_level) VALUES
    ('00000000-0000-0000-0001-000000000001', '00000000-0000-0000-0002-000000000001', 'ADMIN'),
    ('00000000-0000-0000-0001-000000000001', '00000000-0000-0000-0002-000000000002', 'ADMIN'),
    ('00000000-0000-0000-0001-000000000001', '00000000-0000-0000-0002-000000000003', 'ADMIN'),
    ('00000000-0000-0000-0001-000000000001', '00000000-0000-0000-0002-000000000004', 'ADMIN');

-- Employees get access to their respective sections
INSERT INTO user_sections (user_id, section_id, permission_level) VALUES
    ('00000000-0000-0000-0001-000000000002', '00000000-0000-0000-0002-000000000003', 'WRITE'), -- Ahmed -> Warehouse
    ('00000000-0000-0000-0001-000000000003', '00000000-0000-0000-0002-000000000002', 'WRITE'), -- Fatima -> Labs
    ('00000000-0000-0000-0001-000000000004', '00000000-0000-0000-0002-000000000001', 'WRITE'), -- Omar -> Production
    ('00000000-0000-0000-0001-000000000005', '00000000-0000-0000-0002-000000000004', 'WRITE'); -- Sara -> Quality


-- ---------------------------------------------------------------------------
-- 5. DOCUMENTS — Sample SOPs
-- ---------------------------------------------------------------------------
INSERT INTO documents (id, section_id, title, description, file_path, version, uploaded_by, status) VALUES
    ('00000000-0000-0000-0003-000000000001',
     '00000000-0000-0000-0002-000000000001',
     'SOP-PRD-001: Machine Startup Procedure',
     'Step-by-step procedure for safely starting up production line machinery.',
     'sops/production/SOP-PRD-001-v1.0.pdf',
     '1.0',
     '00000000-0000-0000-0001-000000000001',
     'APPROVED'),

    ('00000000-0000-0000-0003-000000000002',
     '00000000-0000-0000-0002-000000000001',
     'SOP-PRD-002: Emergency Shutdown Protocol',
     'Emergency shutdown sequence for all production line equipment.',
     'sops/production/SOP-PRD-002-v2.1.pdf',
     '2.1',
     '00000000-0000-0000-0001-000000000001',
     'APPROVED'),

    ('00000000-0000-0000-0003-000000000003',
     '00000000-0000-0000-0002-000000000002',
     'SOP-LAB-001: Sample Analysis Protocol',
     'Standard procedure for preparing and analysing raw material samples.',
     'sops/labs/SOP-LAB-001-v1.0.pdf',
     '1.0',
     '00000000-0000-0000-0001-000000000001',
     'UNDER_REVIEW'),

    ('00000000-0000-0000-0003-000000000004',
     '00000000-0000-0000-0002-000000000003',
     'SOP-WHS-001: Receiving Raw Materials',
     'Incoming goods inspection and storage assignment procedure.',
     'sops/warehouse/SOP-WHS-001-v1.0.pdf',
     '1.0',
     '00000000-0000-0000-0001-000000000002',
     'DRAFT'),

    ('00000000-0000-0000-0003-000000000005',
     '00000000-0000-0000-0002-000000000004',
     'SOP-QA-001: Final Product Inspection',
     'Quality assurance checklist for finished product release.',
     'sops/quality/SOP-QA-001-v3.0.pdf',
     '3.0',
     '00000000-0000-0000-0001-000000000001',
     'APPROVED');


-- ---------------------------------------------------------------------------
-- 6. LOCATIONS — Warehouse Storage Grid
-- ---------------------------------------------------------------------------
INSERT INTO locations (id, warehouse_name, rack, shelf, position, location_code) VALUES
    ('00000000-0000-0000-0004-000000000001', 'Warehouse A', 'R01', 'S01', 'P01', 'A-R01-S01-P01'),
    ('00000000-0000-0000-0004-000000000002', 'Warehouse A', 'R01', 'S01', 'P02', 'A-R01-S01-P02'),
    ('00000000-0000-0000-0004-000000000003', 'Warehouse A', 'R01', 'S03', 'P05', 'A-R01-S03-P05'),
    ('00000000-0000-0000-0004-000000000004', 'Warehouse A', 'R02', 'S01', 'P01', 'A-R02-S01-P01'),
    ('00000000-0000-0000-0004-000000000005', 'Warehouse A', 'R02', 'S01', 'P02', 'A-R02-S01-P02'),
    ('00000000-0000-0000-0004-000000000006', 'Warehouse A', 'R02', 'S02', 'P03', 'A-R02-S02-P03'),
    ('00000000-0000-0000-0004-000000000007', 'Warehouse B', 'R01', 'S01', 'P01', 'B-R01-S01-P01'),
    ('00000000-0000-0000-0004-000000000008', 'Warehouse B', 'R01', 'S02', 'P04', 'B-R01-S02-P04');


-- ---------------------------------------------------------------------------
-- 7. ITEMS — Sample Materials / Bags
-- ---------------------------------------------------------------------------
INSERT INTO items (id, item_code, material_name, quantity, unit, location_id, created_by, status) VALUES
    ('00000000-0000-0000-0005-000000000001',
     'BG-000001', 'Raw Material X — Polymer Granules',
     50.000, 'KG',
     '00000000-0000-0000-0004-000000000003',   -- A-R01-S03-P05
     '00000000-0000-0000-0001-000000000002',
     'AVAILABLE'),

    ('00000000-0000-0000-0005-000000000002',
     'BG-000002', 'Chemical Compound Y — Solvent Base',
     200.000, 'L',
     '00000000-0000-0000-0004-000000000001',   -- A-R01-S01-P01
     '00000000-0000-0000-0001-000000000002',
     'AVAILABLE'),

    ('00000000-0000-0000-0005-000000000003',
     'BG-000003', 'Packaging Material Z — Cardboard Boxes',
     150.000, 'PCS',
     '00000000-0000-0000-0004-000000000007',   -- B-R01-S01-P01
     '00000000-0000-0000-0001-000000000001',
     'AVAILABLE'),

    ('00000000-0000-0000-0005-000000000004',
     'BG-000004', 'Raw Material W — Steel Rods',
     75.500, 'KG',
     '00000000-0000-0000-0004-000000000004',   -- A-R02-S01-P01
     '00000000-0000-0000-0001-000000000002',
     'RESERVED'),

    ('00000000-0000-0000-0005-000000000005',
     'BG-000005', 'Chemical Reagent V — pH Buffer',
     10.250, 'L',
     '00000000-0000-0000-0004-000000000008',   -- B-R01-S02-P04
     '00000000-0000-0000-0001-000000000001',
     'QUARANTINE');


-- ---------------------------------------------------------------------------
-- 8. MOVEMENT_LOGS — Sample Movements (Ahmed moved BG-000001)
-- ---------------------------------------------------------------------------
INSERT INTO movement_logs (item_id, from_location, to_location, moved_by, notes) VALUES
    -- Initial placement — no from_location
    ('00000000-0000-0000-0005-000000000001',
     NULL,
     '00000000-0000-0000-0004-000000000001',   -- A-R01-S01-P01 (initial)
     '00000000-0000-0000-0001-000000000002',
     'Initial placement on arrival.'),

    -- Ahmed moved BG-000001 from A-R01-S01-P01 → A-R01-S03-P05
    ('00000000-0000-0000-0005-000000000001',
     '00000000-0000-0000-0004-000000000001',   -- A-R01-S01-P01
     '00000000-0000-0000-0004-000000000003',   -- A-R01-S03-P05
     '00000000-0000-0000-0001-000000000002',
     'Relocated to designated polymer storage area.'),

    -- Admin moved BG-000004 to reserved slot
    ('00000000-0000-0000-0005-000000000004',
     NULL,
     '00000000-0000-0000-0004-000000000004',   -- A-R02-S01-P01
     '00000000-0000-0000-0001-000000000001',
     'Reserved for production run PR-2026-06.');


-- ---------------------------------------------------------------------------
-- 9. AUDIT_LOGS — Bootstrap entries
-- ---------------------------------------------------------------------------
INSERT INTO audit_logs (user_id, action, module, description, ip_address) VALUES
    ('00000000-0000-0000-0001-000000000001', 'LOGIN',    'IAM',       'Admin initial login.',          '127.0.0.1'),
    ('00000000-0000-0000-0001-000000000002', 'LOGIN',    'IAM',       'Ahmed Ali initial login.',      '192.168.1.42'),
    ('00000000-0000-0000-0001-000000000001', 'CREATE',   'SOP',       'Uploaded SOP-PRD-001 v1.0.',    '127.0.0.1'),
    ('00000000-0000-0000-0001-000000000001', 'CREATE',   'SOP',       'Uploaded SOP-PRD-002 v2.1.',    '127.0.0.1'),
    ('00000000-0000-0000-0001-000000000002', 'ADD_ITEM', 'WAREHOUSE', 'Registered BG-000001.',         '192.168.1.42'),
    ('00000000-0000-0000-0001-000000000002', 'MOVE_ITEM','WAREHOUSE', 'Moved BG-000001 to A-R01-S03-P05.', '192.168.1.42');

COMMIT;
