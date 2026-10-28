
from typing import Any

from app.database.connection import get_db_connection


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
    """Create an inspection record for an existing complaint."""

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

        if issue_type_id is not None:
            issue_type = connection.execute(
                """
                SELECT issue_type_id
                FROM issue_types
                WHERE issue_type_id = %s
                  AND is_active = TRUE
                """,
                (issue_type_id,),
            ).fetchone()

            if issue_type is None:
                return {"error": "invalid_issue_type"}

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

        if complaint["complaint_status"] == "REGISTERED":
            connection.execute(
                """
                UPDATE complaints
                SET complaint_status = 'UNDER_INSPECTION',
                    updated_at = CURRENT_TIMESTAMP
                WHERE complaint_id = %s
                """,
                (complaint["complaint_id"],),
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
                    "REGISTERED",
                    "UNDER_INSPECTION",
                    inspected_by,
                    "Inspection started and inspection findings recorded.",
                ),
            )

        return {
            "complaint_number": complaint["complaint_number"],
            "complaint_status": "UNDER_INSPECTION",
            "inspection": dict(inspection),
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
                i.inspection_outcome,
                i.recommended_action,
                i.inspection_notes,
                i.inspected_at,
                i.created_at
            FROM inspections AS i
            LEFT JOIN issue_types AS it
                ON it.issue_type_id = i.issue_type_id
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
