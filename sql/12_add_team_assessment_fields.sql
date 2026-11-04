
ALTER TABLE complaint_assignments
ADD COLUMN IF NOT EXISTS assessment_findings TEXT,
ADD COLUMN IF NOT EXISTS recommended_action TEXT,
ADD COLUMN IF NOT EXISTS assessment_outcome VARCHAR(40),
ADD COLUMN IF NOT EXISTS assessed_by VARCHAR(150),
ADD COLUMN IF NOT EXISTS assessed_at TIMESTAMPTZ;

ALTER TABLE complaint_assignments
ADD CONSTRAINT chk_team_assessment_outcome
CHECK (
    assessment_outcome IS NULL
    OR assessment_outcome IN (
        'REPAIR_REQUIRED',
        'NO_REPAIR_REQUIRED',
        'FURTHER_INVESTIGATION_REQUIRED'
    )
);
