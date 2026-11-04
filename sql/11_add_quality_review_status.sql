-- Washing Machine Complaint Management System
-- Migration: Add AWAITING_QUALITY_REVIEW status

BEGIN;

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
            'CLOSED'
        )
    );

COMMIT;
