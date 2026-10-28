
BEGIN;

CREATE TABLE IF NOT EXISTS inspections (
    inspection_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    complaint_id BIGINT NOT NULL
        REFERENCES complaints(complaint_id),

    inspection_number INTEGER NOT NULL,

    inspected_by VARCHAR(150) NOT NULL,

    inspection_findings TEXT NOT NULL,

    issue_type_id INTEGER
        REFERENCES issue_types(issue_type_id),

    inspection_outcome VARCHAR(30) NOT NULL
        CHECK (
            inspection_outcome IN (
                'ISSUE_IDENTIFIED',
                'NO_ISSUE_FOUND',
                'FURTHER_TESTING_REQUIRED',
                'REPAIR_REQUIRED'
            )
        ),

    recommended_action TEXT,

    inspection_notes TEXT,

    inspected_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_inspection_number_per_complaint
        UNIQUE (complaint_id, inspection_number)
);

CREATE INDEX IF NOT EXISTS idx_inspections_complaint_id
    ON inspections(complaint_id);

CREATE INDEX IF NOT EXISTS idx_inspections_inspected_at
    ON inspections(inspected_at);


CREATE TABLE IF NOT EXISTS inspection_evidence (
    evidence_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    inspection_id BIGINT NOT NULL
        REFERENCES inspections(inspection_id),

    file_name VARCHAR(255) NOT NULL,

    file_path TEXT NOT NULL,

    file_type VARCHAR(100) NOT NULL,

    description TEXT,

    uploaded_by VARCHAR(150) NOT NULL,

    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_inspection_evidence_inspection_id
    ON inspection_evidence(inspection_id);

COMMIT;
