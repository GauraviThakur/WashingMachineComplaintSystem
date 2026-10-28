
from typing import Any

from app.repositories.team_assignment_repository import (
    assign_complaint_to_team,
    get_assignment_history,
    get_primary_team_for_issue,
)
from app.database.connection import get_db_connection


def assign_complaint(
    *,
    complaint_number: str,
    team_id: int,
    assigned_by: str,
    assignment_reason: str,
    assigned_to: str | None = None,
) -> dict[str, Any]:
    """Manually assign or reassign a complaint to a team."""

    return assign_complaint_to_team(
        complaint_number=complaint_number.strip().upper(),
        team_id=team_id,
        assigned_by=assigned_by.strip(),
        assignment_reason=assignment_reason.strip(),
        assigned_to=assigned_to.strip() if assigned_to else None,
    )


def assign_complaint_automatically(
    *,
    complaint_number: str,
    assigned_by: str,
    assigned_to: str | None = None,
) -> dict[str, Any]:
    """Select the primary team using the latest inspection issue type."""

    normalized_number = complaint_number.strip().upper()

    with get_db_connection() as connection:
        complaint = connection.execute(
            """
            SELECT complaint_id, complaint_status
            FROM complaints
            WHERE complaint_number = %s
            """,
            (normalized_number,),
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

        inspection = connection.execute(
            """
            SELECT issue_type_id
            FROM inspections
            WHERE complaint_id = %s
              AND issue_type_id IS NOT NULL
            ORDER BY inspection_number DESC
            LIMIT 1
            """,
            (complaint["complaint_id"],),
        ).fetchone()

    if inspection is None:
        return {"error": "inspection_issue_type_missing"}

    team = get_primary_team_for_issue(inspection["issue_type_id"])

    if team is None:
        return {"error": "primary_team_mapping_not_found"}

    reason = (
        f"Automatically assigned based on inspection issue type "
        f"{inspection['issue_type_id']}."
    )

    return assign_complaint_to_team(
        complaint_number=normalized_number,
        team_id=team["team_id"],
        assigned_by=assigned_by.strip(),
        assigned_to=assigned_to.strip() if assigned_to else None,
        assignment_reason=reason,
    )


def fetch_assignment_history(
    complaint_number: str,
) -> dict[str, Any] | None:
    """Retrieve all assignments and reassignments for a complaint."""

    return get_assignment_history(complaint_number.strip().upper())
