
-- ============================================================
-- Washing Machine Complaint Management System
-- File: 08_decision_disposition_schema.sql
-- Purpose: Store final decisions and machine dispositions
-- ============================================================

CREATE TABLE IF NOT EXISTS complaint_decisions (
    decision_id BIGSERIAL PRIMARY KEY,

    complaint_id BIGINT NOT NULL
        REFERENCES complaints(complaint_id),

    decision_type VARCHAR(20) NOT NULL
        CHECK (
            decision_type IN ('ACCEPTED', 'REJECTED')
        ),

    decision_reason TEXT NOT NULL
        CHECK (LENGTH(TRIM(decision_reason)) >= 3),

    rejection_reason TEXT,

    decided_by VARCHAR(150) NOT NULL
        CHECK (LENGTH(TRIM(decided_by)) >= 2),

    decided_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_rejection_reason_required
        CHECK (
            decision_type <> 'REJECTED'
            OR (
                rejection_reason IS NOT NULL
                AND LENGTH(TRIM(rejection_reason)) >= 3
            )
        )
);

-- A complaint can have only one final decision.
CREATE UNIQUE INDEX IF NOT EXISTS
    uq_complaint_decisions_complaint_id
ON complaint_decisions(complaint_id);


CREATE TABLE IF NOT EXISTS complaint_dispositions (
    disposition_id BIGSERIAL PRIMARY KEY,

    complaint_id BIGINT NOT NULL
        REFERENCES complaints(complaint_id),

    disposition_type VARCHAR(30) NOT NULL
        CHECK (
            disposition_type IN (
                'RETURN_TO_STOCK',
                'SCRAP',
                'HOLD',
                'RETURN_TO_DEALER',
                'OTHER'
            )
        ),

    disposition_reason TEXT NOT NULL
        CHECK (LENGTH(TRIM(disposition_reason)) >= 3),

    recorded_by VARCHAR(150) NOT NULL
        CHECK (LENGTH(TRIM(recorded_by)) >= 2),

    recorded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_complaint_dispositions_complaint_id
        UNIQUE (complaint_id)
);


CREATE INDEX IF NOT EXISTS
    idx_complaint_decisions_decision_type
ON complaint_decisions(decision_type);

CREATE INDEX IF NOT EXISTS
    idx_complaint_dispositions_disposition_type
ON complaint_dispositions(disposition_type);
