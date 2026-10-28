
-- ============================================================
-- Washing Machine Complaint Management System
-- Migration: 04 - Team Assignment and Notifications
-- ============================================================

-- 1. Teams responsible for resolving washing machine issues
CREATE TABLE IF NOT EXISTS teams (
    team_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    team_name VARCHAR(150) NOT NULL UNIQUE,
    team_description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 2. Map issue types to their responsible teams
CREATE TABLE IF NOT EXISTS issue_type_team_mapping (
    mapping_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    issue_type_id BIGINT NOT NULL
        REFERENCES issue_types(issue_type_id),
    team_id BIGINT NOT NULL REFERENCES teams(team_id),
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (issue_type_id, team_id)
);

CREATE INDEX IF NOT EXISTS idx_issue_team_mapping_issue_type
    ON issue_type_team_mapping(issue_type_id);

-- 3. Preserve every assignment and reassignment
CREATE TABLE IF NOT EXISTS complaint_assignments (
    assignment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    complaint_id BIGINT NOT NULL
        REFERENCES complaints(complaint_id),
    team_id BIGINT NOT NULL REFERENCES teams(team_id),
    assigned_to VARCHAR(150),
    assigned_by VARCHAR(150) NOT NULL,
    assignment_reason TEXT NOT NULL,
    assignment_status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE'
        CHECK (assignment_status IN ('ACTIVE', 'COMPLETED', 'CANCELLED')),
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- A complaint can have only one active team assignment.
CREATE UNIQUE INDEX IF NOT EXISTS uq_complaint_active_assignment
    ON complaint_assignments(complaint_id)
    WHERE assignment_status = 'ACTIVE';

CREATE INDEX IF NOT EXISTS idx_complaint_assignments_complaint
    ON complaint_assignments(complaint_id, assigned_at DESC);

CREATE INDEX IF NOT EXISTS idx_complaint_assignments_team
    ON complaint_assignments(team_id, assignment_status);

-- 4. Store notification records for traceability
CREATE TABLE IF NOT EXISTS team_notifications (
    notification_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    complaint_id BIGINT NOT NULL
        REFERENCES complaints(complaint_id),
    assignment_id BIGINT
        REFERENCES complaint_assignments(assignment_id),
    team_id BIGINT NOT NULL REFERENCES teams(team_id),
    notification_type VARCHAR(50) NOT NULL
        CHECK (notification_type IN (
            'NEW_ASSIGNMENT',
            'REASSIGNMENT',
            'STATUS_UPDATE'
        )),
    recipient VARCHAR(255),
    notification_message TEXT NOT NULL,
    delivery_status VARCHAR(20) NOT NULL DEFAULT 'PENDING'
        CHECK (delivery_status IN (
            'PENDING',
            'SENT',
            'FAILED',
            'NOT_CONFIGURED'
        )),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMPTZ,
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_team_notifications_status
    ON team_notifications(delivery_status, created_at);

CREATE INDEX IF NOT EXISTS idx_team_notifications_complaint
    ON team_notifications(complaint_id, created_at DESC);
