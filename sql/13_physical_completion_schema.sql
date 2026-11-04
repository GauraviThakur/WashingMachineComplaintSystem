
-- ============================================================
-- Washing Machine Complaint Management System
-- Migration: 13_physical_completion_schema.sql
-- Purpose:
-- 1. Add physical completion tracking.
-- 2. Add stock transfer and scrap workflow statuses.
-- 3. Restrict permitted disposition types.
-- 4. Close complaints only after physical completion.
-- ============================================================

BEGIN;

-- 1. Update permitted complaint statuses.

ALTER TABLE complaints
    DROP CONSTRAINT IF EXISTS complaints_complaint_status_check;

ALTER TABLE complaints
    ADD CONSTRAINT complaints_complaint_status_check
    CHECK (
        complaint_status IN (
            'REGISTERED',
            'UNDER_INSPECTION',
            'ASSIGNED',
            'UNDER_REWORK',
            'UNDER_TESTING',
            'AWAITING_QUALITY_REVIEW',
            'AWAITING_DECISION',
            'AWAITING_DISPOSITION',
            'AWAITING_DISPATCH',
            'AWAITING_STOCK_TRANSFER',
            'AWAITING_SCRAP',
            'CLOSED'
        )
    );

-- 2. Restrict disposition options to the agreed workflow.

ALTER TABLE complaint_dispositions
    DROP CONSTRAINT IF EXISTS complaint_dispositions_disposition_type_check;

ALTER TABLE complaint_dispositions
    ADD CONSTRAINT chk_complaint_disposition_type
    CHECK (
        disposition_type IN (
            'RETURN_TO_DEALER',
            'RETURN_TO_STOCK',
            'SCRAP'
        )
    );

-- 3. Store physical completion details.

CREATE TABLE IF NOT EXISTS complaint_physical_completions (
    completion_id BIGSERIAL PRIMARY KEY,

    complaint_id BIGINT NOT NULL
        REFERENCES complaints(complaint_id),

    disposition_id BIGINT NOT NULL
        REFERENCES complaint_dispositions(disposition_id),

    completion_type VARCHAR(30) NOT NULL
        CHECK (
            completion_type IN (
                'DISPATCH',
                'STOCK_TRANSFER',
                'SCRAP'
            )
        ),

    reference_number VARCHAR(100),

    completion_details TEXT,

    completed_by VARCHAR(150) NOT NULL
        CHECK (LENGTH(TRIM(completed_by)) >= 2),

    completed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_physical_completion_complaint
        UNIQUE (complaint_id),

    CONSTRAINT uq_physical_completion_disposition
        UNIQUE (disposition_id),

    CONSTRAINT chk_physical_completion_reference
        CHECK (
            completion_type = 'SCRAP'
            OR (
                reference_number IS NOT NULL
                AND LENGTH(TRIM(reference_number)) >= 1
            )
        )
);

CREATE INDEX IF NOT EXISTS
    idx_physical_completion_type
ON complaint_physical_completions(completion_type);

COMMIT;
