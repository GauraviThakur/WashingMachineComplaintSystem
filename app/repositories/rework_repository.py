
from typing import Any

from app.database.connection import get_db_connection


def create_rework_attempt(
    *,
    complaint_number: str,
    performed_by: str,
    rework_action: str,
    parts_replaced: str | None,
    rework_result: str,
    requires_testing: bool,
    rework_notes: str | None,
) -> dict[str, Any]:
    with get_db_connection() as connection:
        complaint = connection.execute(
            """
            SELECT complaint_id, complaint_number, complaint_status
            FROM complaints
            WHERE complaint_number = %s
            FOR UPDATE
            """,
            (complaint_number,),
        ).fetchone()

        if not complaint:
            return {"error": "complaint_not_found"}

        complaint_id = complaint["complaint_id"]
        current_status = complaint["complaint_status"]

        if current_status not in ("ASSIGNED", "UNDER_REWORK"):
            return {
                "error": "invalid_complaint_status",
                "current_status": current_status,
            }

        assignment = connection.execute(
            """
            SELECT assignment_id
            FROM complaint_assignments
            WHERE complaint_id = %s
              AND assignment_status = 'ACTIVE'
            ORDER BY assigned_at DESC
            LIMIT 1
            """,
            (complaint_id,),
        ).fetchone()

        if not assignment:
            return {"error": "active_assignment_not_found"}

        previous_attempt = connection.execute(
            """
            SELECT COALESCE(MAX(attempt_number), 0) AS last_attempt
            FROM rework_attempts
            WHERE complaint_id = %s
            """,
            (complaint_id,),
        ).fetchone()

        attempt_number = previous_attempt["last_attempt"] + 1

        result = connection.execute(
            """
            INSERT INTO rework_attempts (
                complaint_id,
                assignment_id,
                attempt_number,
                performed_by,
                rework_action,
                parts_replaced,
                rework_result,
                requires_testing,
                rework_notes,
                completed_at
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s,
                CURRENT_TIMESTAMP
            )
            RETURNING
                rework_id,
                complaint_id,
                assignment_id,
                attempt_number,
                performed_by,
                rework_action,
                parts_replaced,
                rework_result,
                requires_testing,
                rework_notes,
                started_at,
                completed_at,
                created_at
            """,
            (
                complaint_id,
                assignment["assignment_id"],
                attempt_number,
                performed_by,
                rework_action,
                parts_replaced,
                rework_result,
                requires_testing,
                rework_notes,
            ),
        ).fetchone()

        new_status = "UNDER_TESTING" if (
            rework_result == "COMPLETED" and requires_testing
        ) else "UNDER_REWORK"

        if current_status != new_status:
            connection.execute(
                """
                UPDATE complaints
                SET complaint_status = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE complaint_id = %s
                """,
                (new_status, complaint_id),
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
                    complaint_id,
                    current_status,
                    new_status,
                    performed_by,
                    f"Rework attempt {attempt_number}: {rework_result}",
                ),
            )

        return {
            "complaint_number": complaint["complaint_number"],
            "complaint_status": new_status,
            "rework_attempt": dict(result),
        }


def get_rework_history(
    complaint_number: str,
) -> dict[str, Any] | None:
    with get_db_connection() as connection:
        complaint = connection.execute(
            """
            SELECT complaint_id, complaint_number, complaint_status
            FROM complaints
            WHERE complaint_number = %s
            """,
            (complaint_number,),
        ).fetchone()

        if not complaint:
            return None

        attempts = connection.execute(
            """
            SELECT
                rework_id,
                attempt_number,
                assignment_id,
                performed_by,
                rework_action,
                parts_replaced,
                rework_result,
                requires_testing,
                rework_notes,
                started_at,
                completed_at,
                created_at
            FROM rework_attempts
            WHERE complaint_id = %s
            ORDER BY attempt_number
            """,
            (complaint["complaint_id"],),
        ).fetchall()

        return {
            "complaint_number": complaint["complaint_number"],
            "complaint_status": complaint["complaint_status"],
            "rework_attempts": [dict(attempt) for attempt in attempts],
        }
