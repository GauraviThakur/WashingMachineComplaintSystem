
-- Prevent more than one active complaint per machine.
-- A new complaint is allowed after the previous one is CLOSED.

CREATE UNIQUE INDEX IF NOT EXISTS
    uq_complaints_one_active_per_machine
ON complaints (machine_id)
WHERE complaint_status <> 'CLOSED';
