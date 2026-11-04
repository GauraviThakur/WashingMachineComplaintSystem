
from typing import Any

from app.database.connection import get_db_connection


def get_pending_team_assessments() -> dict[str, Any]:
    """Retrieve complaints waiting for an active team's assessment."""

    with get_db_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                c.complaint_id,
                c.complaint_number,
                c.customer_name,
                c.reported_issue,
                c.priority,
                c.complaint_status,
                c.registered_at,

                m.serial_number,
                m.model_number,
                m.batch_number,

                ca.assignment_id,
                ca.team_id,
                t.team_name,
                ca.assigned_to,
                ca.assigned_by,
                ca.assigned_at

            FROM complaint_assignments AS ca

            INNER JOIN complaints AS c
                ON c.complaint_id = ca.complaint_id

            INNER JOIN machines AS m
                ON m.machine_id = c.machine_id

            INNER JOIN teams AS t
                ON t.team_id = ca.team_id

            WHERE c.complaint_status = 'ASSIGNED'
              AND ca.assignment_status = 'ACTIVE'
              AND ca.assessment_outcome IS NULL

            ORDER BY ca.assigned_at ASC, ca.assignment_id ASC
            """
        ).fetchall()

        items = [dict(row) for row in rows]

        return {
            "items": items,
            "total": len(items),
        }


def submit_team_assessment(
    *,
    complaint_number: str,
    assessed_by: str,
    assessment_findings: str,
    recommended_action: str,
    assessment_outcome: str,
) -> dict[str, Any]:
    """Save a technical assessment against the active team assignment."""

    with get_db_connection() as connection:
        complaint = connection.execute(
            """
            SELECT
                complaint_id,
                complaint_number,
                complaint_status
            FROM complaints
            WHERE complaint_number = %s
            FOR UPDATE
            """,
            (complaint_number.strip().upper(),),
        ).fetchone()

        if complaint is None:
            return {"error": "complaint_not_found"}

        if complaint["complaint_status"] != "ASSIGNED":
            return {
                "error": "complaint_not_ready_for_assessment",
                "current_status": complaint["complaint_status"],
            }

        assignment = connection.execute(
            """
            SELECT
                assignment_id,
                team_id,
                assigned_to,
                assignment_status,
                assessment_outcome
            FROM complaint_assignments
            WHERE complaint_id = %s
              AND assignment_status = 'ACTIVE'
            ORDER BY assigned_at DESC, assignment_id DESC
            LIMIT 1
            FOR UPDATE
            """,
            (complaint["complaint_id"],),
        ).fetchone()

        if assignment is None:
            return {"error": "active_assignment_not_found"}

        if assignment["assessment_outcome"] is not None:
            return {"error": "assignment_already_assessed"}

        new_status_by_outcome = {
            "REPAIR_REQUIRED": "UNDER_REWORK",
            "NO_REPAIR_REQUIRED": "UNDER_TESTING",
            "FURTHER_INVESTIGATION_REQUIRED": "UNDER_INSPECTION",
        }

        new_status = new_status_by_outcome.get(assessment_outcome)

        if new_status is None:
            return {"error": "invalid_assessment_outcome"}

        # Keep the assignment active when repair is required.
        # The existing rework workflow needs an active assignment.
        if assessment_outcome == "REPAIR_REQUIRED":
            assignment_status = "ACTIVE"
            completed_at_sql = "NULL"
        else:
            assignment_status = "COMPLETED"
            completed_at_sql = "CURRENT_TIMESTAMP"

        updated_assignment = connection.execute(
            f"""
            UPDATE complaint_assignments
            SET assessment_findings = %s,
                recommended_action = %s,
                assessment_outcome = %s,
                assessed_by = %s,
                assessed_at = CURRENT_TIMESTAMP,
                assignment_status = %s,
                completed_at = {completed_at_sql}
            WHERE assignment_id = %s
              AND assignment_status = 'ACTIVE'
            RETURNING
                assignment_id,
                complaint_id,
                team_id,
                assessment_findings,
                recommended_action,
                assessment_outcome,
                assessed_by,
                assessed_at,
                assignment_status,
                completed_at
            """,
            (
                assessment_findings,
                recommended_action,
                assessment_outcome,
                assessed_by,
                assignment_status,
                assignment["assignment_id"],
            ),
        ).fetchone()

        if updated_assignment is None:
            return {"error": "assignment_already_assessed"}

        connection.execute(
            """
            UPDATE complaints
            SET complaint_status = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE complaint_id = %s
            """,
            (new_status, complaint["complaint_id"]),
        )

        history_reason = (
            f"Team assessment completed. "
            f"Outcome: {assessment_outcome}. "
            f"Recommended action: {recommended_action}"
        )

        connection.execute(
            """
            INSERT INTO complaint_history (
                complaint_id,
                previous_status,
                new_status,
                changed_by,
                reason
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                complaint["complaint_id"],
                complaint["complaint_status"],
                new_status,
                assessed_by,
                history_reason,
            ),
        )

        return {
            "complaint_number": complaint["complaint_number"],
            "previous_status": complaint["complaint_status"],
            "complaint_status": new_status,
            "assessment": dict(updated_assignment),
        }


def get_team_assessment_history(
    complaint_number: str,
) -> dict[str, Any] | None:
    """Return all assessments recorded against a complaint's assignments."""

    with get_db_connection() as connection:
        complaint = connection.execute(
            """
            SELECT
                complaint_id,
                complaint_number,
                complaint_status
            FROM complaints
            WHERE complaint_number = %s
            """,
            (complaint_number.strip().upper(),),
        ).fetchone()

        if complaint is None:
            return None

        assessments = connection.execute(
            """
            SELECT
                ca.assignment_id,
                ca.team_id,
                t.team_name,
                ca.assessment_findings,
                ca.recommended_action,
                ca.assessment_outcome,
                ca.assessed_by,
                ca.assessed_at,
                ca.assignment_status,
                ca.assigned_at,
                ca.completed_at
            FROM complaint_assignments AS ca
            JOIN teams AS t
                ON t.team_id = ca.team_id
            WHERE ca.complaint_id = %s
              AND ca.assessment_outcome IS NOT NULL
            ORDER BY ca.assessed_at, ca.assignment_id
            """,
            (complaint["complaint_id"],),
        ).fetchall()

        return {
            "complaint_number": complaint["complaint_number"],
            "complaint_status": complaint["complaint_status"],
            "assessment_history": [
                dict(assessment) for assessment in assessments
            ],
        }
