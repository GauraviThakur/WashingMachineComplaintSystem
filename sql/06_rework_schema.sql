
-- ============================================================
-- Washing Machine Complaint Management System
-- File: 06_rework_schema.sql
-- Purpose: Store complaint repair/rework attempts
-- ============================================================

CREATE TABLE IF NOT EXISTS rework_attempts (
    rework_id BIGSERIAL PRIMARY KEY,

    complaint_id BIGINT NOT NULL
        REFERENCES complaints(complaint_id),

    assignment_id BIGINT
        REFERENCES complaint_assignments(assignment_id),

    attempt_number INTEGER NOT NULL
        CHECK (attempt_number >= 1),

    performed_by VARCHAR(150) NOT NULL,

    rework_action TEXT NOT NULL
        CHECK (LENGTH(TRIM(rework_action)) >= 3),

    parts_replaced TEXT,

    rework_result VARCHAR(30) NOT NULL
        CHECK (
            rework_result IN (
                'COMPLETED',
                'UNSUCCESSFUL',
                'PARTIALLY_COMPLETED'
            )
        ),

    requires_testing BOOLEAN NOT NULL DEFAULT TRUE,

    rework_notes TEXT,

    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    completed_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_rework_complaint_attempt
        UNIQUE (complaint_id, attempt_number),

    CONSTRAINT chk_rework_completion_time
        CHECK (
            completed_at IS NULL
            OR completed_at >= started_at
        )
);

CREATE INDEX IF NOT EXISTS idx_rework_attempts_complaint
    ON rework_attempts (complaint_id);

CREATE INDEX IF NOT EXISTS idx_rework_attempts_assignment
    ON rework_attempts (assignment_id);

CREATE INDEX IF NOT EXISTS idx_rework_attempts_result
    ON rework_attempts (rework_result);
