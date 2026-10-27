
-- ============================================================
-- Washing Machine Complaint Management System
-- File: sql/01_initial_schema.sql
-- Database: PostgreSQL
-- ============================================================

BEGIN;

-- 1. Machine master records
CREATE TABLE IF NOT EXISTS machines (
    machine_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    serial_number VARCHAR(100) NOT NULL UNIQUE,
    model_number VARCHAR(100) NOT NULL,
    batch_number VARCHAR(100),
    manufacturing_date DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 2. Complaint categories
CREATE TABLE IF NOT EXISTS complaint_categories (
    category_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 3. Issue types
CREATE TABLE IF NOT EXISTS issue_types (
    issue_type_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    category_id BIGINT NOT NULL REFERENCES complaint_categories(category_id),
    issue_type_name VARCHAR(150) NOT NULL UNIQUE,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 4. Bulk intake requests
-- One bulk request can contain multiple machine complaints.
CREATE TABLE IF NOT EXISTS bulk_requests (
    bulk_request_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_file_name VARCHAR(255) NOT NULL,
    uploaded_by VARCHAR(150) NOT NULL,
    total_rows INTEGER NOT NULL DEFAULT 0 CHECK (total_rows >= 0),
    valid_rows INTEGER NOT NULL DEFAULT 0 CHECK (valid_rows >= 0),
    invalid_rows INTEGER NOT NULL DEFAULT 0 CHECK (invalid_rows >= 0),
    request_status VARCHAR(30) NOT NULL DEFAULT 'RECEIVED'
        CHECK (
            request_status IN (
                'RECEIVED',
                'VALIDATING',
                'PARTIALLY_PROCESSED',
                'PROCESSED',
                'FAILED'
            )
        ),
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ
);

-- 5. Main complaint records
CREATE TABLE IF NOT EXISTS complaints (
    complaint_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    complaint_number VARCHAR(40) NOT NULL UNIQUE,
    machine_id BIGINT NOT NULL REFERENCES machines(machine_id),
    bulk_request_id BIGINT REFERENCES bulk_requests(bulk_request_id),
    previous_complaint_id BIGINT REFERENCES complaints(complaint_id),
    customer_name VARCHAR(200) NOT NULL,
    customer_contact VARCHAR(100),
    dealer_email VARCHAR(255),
    reported_issue TEXT NOT NULL,
    issue_type_id BIGINT REFERENCES issue_types(issue_type_id),
    priority VARCHAR(20) NOT NULL DEFAULT 'MEDIUM'
        CHECK (
            priority IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')
        ),
    complaint_status VARCHAR(40) NOT NULL DEFAULT 'REGISTERED'
        CHECK (
            complaint_status IN (
                'REGISTERED',
                'UNDER_INSPECTION',
                'ASSIGNED',
                'UNDER_REWORK',
                'UNDER_TESTING',
                'AWAITING_DECISION',
                'AWAITING_DISPOSITION',
                'AWAITING_DISPATCH',
                'CLOSED'
            )
        ),
    is_repeat_complaint BOOLEAN NOT NULL DEFAULT FALSE,
    registered_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_complaint_closure
        CHECK (
            (complaint_status = 'CLOSED' AND closed_at IS NOT NULL)
            OR
            (complaint_status <> 'CLOSED' AND closed_at IS NULL)
        )
);

-- 6. Bulk import row results
-- Records row-level validation outcomes, including invalid rows.
CREATE TABLE IF NOT EXISTS bulk_request_rows (
    bulk_row_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    bulk_request_id BIGINT NOT NULL
        REFERENCES bulk_requests(bulk_request_id) ON DELETE CASCADE,
    row_number INTEGER NOT NULL CHECK (row_number > 0),
    row_data JSONB NOT NULL,
    validation_status VARCHAR(20) NOT NULL DEFAULT 'PENDING'
        CHECK (
            validation_status IN ('PENDING', 'VALID', 'INVALID', 'PROCESSED')
        ),
    validation_errors JSONB,
    complaint_id BIGINT REFERENCES complaints(complaint_id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (bulk_request_id, row_number)
);

-- 7. Complaint status and workflow history
CREATE TABLE IF NOT EXISTS complaint_history (
    history_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    complaint_id BIGINT NOT NULL
        REFERENCES complaints(complaint_id) ON DELETE CASCADE,
    previous_status VARCHAR(40),
    new_status VARCHAR(40) NOT NULL,
    changed_by VARCHAR(150) NOT NULL,
    change_reason TEXT,
    changed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Useful indexes for common searches
CREATE INDEX IF NOT EXISTS idx_machines_model_number
    ON machines(model_number);

CREATE INDEX IF NOT EXISTS idx_machines_batch_number
    ON machines(batch_number);

CREATE INDEX IF NOT EXISTS idx_complaints_machine_id
    ON complaints(machine_id);

CREATE INDEX IF NOT EXISTS idx_complaints_status
    ON complaints(complaint_status);

CREATE INDEX IF NOT EXISTS idx_complaints_priority
    ON complaints(priority);

CREATE INDEX IF NOT EXISTS idx_complaints_registered_at
    ON complaints(registered_at);

CREATE INDEX IF NOT EXISTS idx_complaints_previous_complaint
    ON complaints(previous_complaint_id);

CREATE INDEX IF NOT EXISTS idx_complaints_bulk_request
    ON complaints(bulk_request_id);

CREATE INDEX IF NOT EXISTS idx_bulk_rows_request
    ON bulk_request_rows(bulk_request_id);

CREATE INDEX IF NOT EXISTS idx_complaint_history_complaint
    ON complaint_history(complaint_id);

COMMIT;
