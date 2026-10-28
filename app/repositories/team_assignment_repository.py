
from typing import Any

from app.database.connection import get_db_connection


def get_primary_team_for_issue(
    issue_type_id: int,
) -> dict[str, Any] | None:
    """Find the active primary team mapped to an issue type."""

    with get_db_connection() as connection:
        team = connection.execute(
            """
            SELECT
                t.team_id,
                t.team_name,
                itm.issue_type_id
            FROM issue_type_team_mapping AS itm
            JOIN teams AS t
                ON t.team_id = itm.team_id
            JOIN issue_types AS it
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

        return dict(team) if team else None


def assign_complaint_to_team(
    *,
    complaint_number: str,
    team_id: int,
    assigned_by: str,
    assignment_reason: str,
    assigned_to: str | None = None,
) -> dict[str, Any]:
    """Assign or reassign a complaint to a team."""

    with get_db_connection() as connection:
        complaint = connection.execute(
            """
            SELECT complaint_id, complaint_number, complaint_status
            FROM complaints
            WHERE complaint_number = %s
            FOR UPDATE
            """,
            (complaint_number.strip().upper(),),
        ).fetchone()

        if complaint is None:
            return {"error": "complaint_not_found"}

        if complaint["complaint_status"] not in {
            "UNDER_INSPECTION",
            "ASSIGNED",
        }:
            return {
                "error": "complaint_not_ready_for_assignment",
                "current_status": complaint["complaint_status"],
            }

        team = connection.execute(
            """
            SELECT team_id, team_name
            FROM teams
            WHERE team_id = %s
              AND is_active = TRUE
            """,
            (team_id,),
        ).fetchone()

        if team is None:
            return {"error": "team_not_found"}

        active_assignment = connection.execute(
            """
            SELECT assignment_id, team_id
            FROM complaint_assignments
            WHERE complaint_id = %s
              AND assignment_status = 'ACTIVE'
            FOR UPDATE
            """,
            (complaint["complaint_id"],),
        ).fetchone()

        is_reassignment = active_assignment is not None

        if is_reassignment:
            if active_assignment["team_id"] == team_id:
                return {
                    "error": "complaint_already_assigned_to_team"
                }

            connection.execute(
                """
                UPDATE complaint_assignments
                SET assignment_status = 'CANCELLED',
                    completed_at = CURRENT_TIMESTAMP
                WHERE assignment_id = %s
                """,
                (active_assignment["assignment_id"],),
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
            VALUES (%s, %s, %s, %s, %s, 'ACTIVE')
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
                team_id,
                assigned_to,
                assigned_by,
                assignment_reason,
            ),
        ).fetchone()

        new_status = "ASSIGNED"

        if complaint["complaint_status"] != new_status:
            connection.execute(
                """
                UPDATE complaints
                SET complaint_status = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE complaint_id = %s
                """,
                (new_status, complaint["complaint_id"]),
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
                    assigned_by,
                    assignment_reason,
                ),
            )

        notification_type = (
            "REASSIGNMENT" if is_reassignment else "NEW_ASSIGNMENT"
        )

        notification_message = (
            f"Complaint {complaint['complaint_number']} "
            f"{'has been reassigned' if is_reassignment else 'has been assigned'} "
            f"to team {team['team_name']}. Reason: {assignment_reason}"
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
            VALUES (%s, %s, %s, %s, %s, 'PENDING')
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
                team_id,
                notification_type,
                notification_message,
            ),
        ).fetchone()

        return {
            "complaint_number": complaint["complaint_number"],
            "complaint_status": new_status,
            "team": dict(team),
            "assignment": dict(assignment),
            "notification": dict(notification),
        }


def get_assignment_history(
    complaint_number: str,
) -> dict[str, Any] | None:
    """Return the assignment history for a complaint."""

    with get_db_connection() as connection:
        complaint = connection.execute(
            """
            SELECT complaint_id, complaint_number, complaint_status
            FROM complaints
            WHERE complaint_number = %s
            """,
            (complaint_number.strip().upper(),),
        ).fetchone()

        if complaint is None:
            return None

        assignments = connection.execute(
            """
            SELECT
                ca.assignment_id,
                ca.team_id,
                t.team_name,
                ca.assigned_to,
                ca.assigned_by,
                ca.assignment_reason,
                ca.assignment_status,
                ca.assigned_at,
                ca.completed_at
            FROM complaint_assignments AS ca
            JOIN teams AS t
                ON t.team_id = ca.team_id
            WHERE ca.complaint_id = %s
            ORDER BY ca.assigned_at, ca.assignment_id
            """,
            (complaint["complaint_id"],),
        ).fetchall()

        return {
            "complaint_number": complaint["complaint_number"],
            "complaint_status": complaint["complaint_status"],
            "assignment_history": [
                dict(row) for row in assignments
            ],
        }
