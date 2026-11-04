
from typing import Any

from app.database.connection import get_db_connection


TEAM_ASSIGNMENT_OUTCOMES = {
    "ISSUE_IDENTIFIED",
    "REPAIR_REQUIRED",
}

VALID_INSPECTION_OUTCOMES = {
    "ISSUE_IDENTIFIED",
    "NO_ISSUE_FOUND",
    "FURTHER_TESTING_REQUIRED",
    "REPAIR_REQUIRED",
}


def create_inspection(
    *,
    complaint_number: str,
    inspected_by: str,
    inspection_findings: str,
    issue_type_id: int | None,
    inspection_outcome: str,
    recommended_action: str | None,
    inspection_notes: str | None,
) -> dict[str, Any]:
    """Create an inspection and process its outcome atomically."""

    if inspection_outcome not in VALID_INSPECTION_OUTCOMES:
        return {"error": "invalid_inspection_outcome"}

    if (
        inspection_outcome in TEAM_ASSIGNMENT_OUTCOMES
        and issue_type_id is None
    ):
        return {"error": "issue_type_required_for_team_assignment"}

    with get_db_connection() as connection:
        complaint = connection.execute(
            """
            SELECT
                complaint_id,
                complaint_number,
                complaint_status,
                issue_type_id
            FROM complaints
            WHERE complaint_number = %s
            FOR UPDATE
            """,
            (complaint_number,),
        ).fetchone()

        if complaint is None:
            return {"error": "complaint_not_found"}

        if complaint["complaint_status"] not in {
            "REGISTERED",
            "UNDER_INSPECTION",
        }:
            return {
                "error": "complaint_not_ready_for_inspection",
                "current_status": complaint["complaint_status"],
            }

        # Validate the issue type before creating any records.
        if issue_type_id is not None:
            issue_type = connection.execute(
                """
                SELECT it.issue_type_id
                FROM issue_types AS it
                INNER JOIN complaint_categories AS cc
                    ON cc.category_id = it.category_id
                WHERE it.issue_type_id = %s
                  AND it.is_active = TRUE
                  AND cc.is_active = TRUE
                """,
                (issue_type_id,),
            ).fetchone()

            if issue_type is None:
                return {"error": "invalid_issue_type"}

        # Find the primary team before inserting the inspection.
        # This prevents an inspection from being saved without its
        # required assignment when a team mapping is unavailable.
        team = None

        if inspection_outcome in TEAM_ASSIGNMENT_OUTCOMES:
            team = connection.execute(
                """
                SELECT
                    t.team_id,
                    t.team_name
                FROM issue_type_team_mapping AS itm
                INNER JOIN teams AS t
                    ON t.team_id = itm.team_id
                INNER JOIN issue_types AS it
                    ON it.issue_type_id = itm.issue_type_id
                WHERE itm.issue_type_id = %s
                  AND itm.is_primary = TRUE
                  AND itm.is_active = TRUE
                  AND t.is_active = TRUE
                  AND it.is_active = TRUE
                ORDER BY itm.mapping_id
                LIMIT 1
                """,
                (issue_type_id,),
            ).fetchone()

            if team is None:
                return {"error": "primary_team_mapping_not_found"}

            active_assignment = connection.execute(
                """
                SELECT assignment_id
                FROM complaint_assignments
                WHERE complaint_id = %s
                  AND assignment_status = 'ACTIVE'
                FOR UPDATE
                """,
                (complaint["complaint_id"],),
            ).fetchone()

            if active_assignment is not None:
                return {"error": "complaint_already_has_active_assignment"}

        # Determine the complaint's next status.
        if inspection_outcome in TEAM_ASSIGNMENT_OUTCOMES:
            new_status = "ASSIGNED"
        elif inspection_outcome == "NO_ISSUE_FOUND":
            new_status = "AWAITING_QUALITY_REVIEW"
        else:
            new_status = "UNDER_TESTING"

        # Calculate the next inspection attempt number.
        next_inspection = connection.execute(
            """
            SELECT COALESCE(MAX(inspection_number), 0) + 1
                AS next_number
            FROM inspections
            WHERE complaint_id = %s
            """,
            (complaint["complaint_id"],),
        ).fetchone()

        inspection_number = next_inspection["next_number"]

        # Record the inspection.
        inspection = connection.execute(
            """
            INSERT INTO inspections (
                complaint_id,
                inspection_number,
                inspected_by,
                inspection_findings,
                issue_type_id,
                inspection_outcome,
                recommended_action,
                inspection_notes
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING
                inspection_id,
                complaint_id,
                inspection_number,
                inspected_by,
                inspection_findings,
                issue_type_id,
                inspection_outcome,
                recommended_action,
                inspection_notes,
                inspected_at,
                created_at
            """,
            (
                complaint["complaint_id"],
                inspection_number,
                inspected_by,
                inspection_findings,
                issue_type_id,
                inspection_outcome,
                recommended_action,
                inspection_notes,
            ),
        ).fetchone()

        # Save the confirmed issue type when supplied.
        if issue_type_id is not None:
            connection.execute(
                """
                UPDATE complaints
                SET issue_type_id = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE complaint_id = %s
                """,
                (
                    issue_type_id,
                    complaint["complaint_id"],
                ),
            )

        previous_status = complaint["complaint_status"]

        # Update complaint status.
        connection.execute(
            """
            UPDATE complaints
            SET complaint_status = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE complaint_id = %s
            """,
            (
                new_status,
                complaint["complaint_id"],
            ),
        )

        # Record the status transition.
        history_reason = (
            f"Inspection attempt {inspection_number} completed. "
            f"Outcome: {inspection_outcome}."
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
                previous_status,
                new_status,
                inspected_by,
                history_reason,
            ),
        )

        assignment_result = None

        # Automatically assign the primary team for confirmed issues.
        if team is not None:
            assignment_reason = (
                f"Inspection identified issue type ID {issue_type_id}. "
                f"Automatically assigned to the primary mapped team."
            )

            assignment = connection.execute(
                """
                INSERT INTO complaint_assignments (
                    complaint_id,
                    team_id,
                    assigned_to,
                    assigned_by,
                    assignment_reason,
                    assignment_status
                )
                VALUES (%s, %s, NULL, %s, %s, 'ACTIVE')
                RETURNING
                    assignment_id,
                    complaint_id,
                    team_id,
                    assigned_to,
                    assigned_by,
                    assignment_reason,
                    assignment_status,
                    assigned_at
                """,
                (
                    complaint["complaint_id"],
                    team["team_id"],
                    inspected_by,
                    assignment_reason,
                ),
            ).fetchone()

            notification_message = (
                f"Complaint {complaint['complaint_number']} "
                f"has been assigned to team {team['team_name']}. "
                f"Reason: {assignment_reason}"
            )

            notification = connection.execute(
                """
                INSERT INTO team_notifications (
                    complaint_id,
                    assignment_id,
                    team_id,
                    notification_type,
                    notification_message,
                    delivery_status
                )
                VALUES (%s, %s, %s, 'NEW_ASSIGNMENT', %s, 'PENDING')
                RETURNING
                    notification_id,
                    notification_type,
                    notification_message,
                    delivery_status,
                    created_at
                """,
                (
                    complaint["complaint_id"],
                    assignment["assignment_id"],
                    team["team_id"],
                    notification_message,
                ),
            ).fetchone()

            assignment_result = {
                "team": dict(team),
                "assignment": dict(assignment),
                "notification": dict(notification),
            }

        # Retrieve the complaint's saved classification.
        saved_classification = connection.execute(
            """
            SELECT
                c.issue_type_id,
                it.issue_type_name,
                cc.category_id,
                cc.category_name
            FROM complaints AS c
            LEFT JOIN issue_types AS it
                ON it.issue_type_id = c.issue_type_id
            LEFT JOIN complaint_categories AS cc
                ON cc.category_id = it.category_id
            WHERE c.complaint_id = %s
            """,
            (complaint["complaint_id"],),
        ).fetchone()

        return {
            "complaint_number": complaint["complaint_number"],
            "previous_status": previous_status,
            "complaint_status": new_status,
            "complaint_classification": dict(saved_classification),
            "inspection": dict(inspection),
            "assignment": assignment_result,
        }


def get_inspections_by_complaint(
    complaint_number: str,
) -> dict[str, Any] | None:
    """Retrieve all inspections associated with a complaint."""

    with get_db_connection() as connection:
        complaint = connection.execute(
            """
            SELECT complaint_id, complaint_number, complaint_status
            FROM complaints
            WHERE complaint_number = %s
            """,
            (complaint_number,),
        ).fetchone()

        if complaint is None:
            return None

        inspections = connection.execute(
            """
            SELECT
                i.inspection_id,
                i.inspection_number,
                i.inspected_by,
                i.inspection_findings,
                i.issue_type_id,
                it.issue_type_name,
                cc.category_name,
                i.inspection_outcome,
                i.recommended_action,
                i.inspection_notes,
                i.inspected_at,
                i.created_at
            FROM inspections AS i
            LEFT JOIN issue_types AS it
                ON it.issue_type_id = i.issue_type_id
            LEFT JOIN complaint_categories AS cc
                ON cc.category_id = it.category_id
            WHERE i.complaint_id = %s
            ORDER BY i.inspection_number
            """,
            (complaint["complaint_id"],),
        ).fetchall()

        return {
            "complaint_number": complaint["complaint_number"],
            "complaint_status": complaint["complaint_status"],
            "inspections": [dict(row) for row in inspections],
        }
