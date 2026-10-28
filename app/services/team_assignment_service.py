
from typing import Any

from app.repositories.team_assignment_repository import (
    assign_complaint_to_team,
    get_assignment_history,
)


def assign_complaint(
    *,
    complaint_number: str,
    team_id: int,
    assigned_by: str,
    assignment_reason: str,
    assigned_to: str | None = None,
) -> dict[str, Any]:
    """Validate assignment input and assign a complaint to a team."""

    return assign_complaint_to_team(
        complaint_number=complaint_number.strip().upper(),
        team_id=team_id,
        assigned_by=assigned_by.strip(),
        assignment_reason=assignment_reason.strip(),
        assigned_to=assigned_to.strip() if assigned_to else None,
    )


def fetch_assignment_history(
    complaint_number: str,
) -> dict[str, Any] | None:
    """Retrieve all assignments and reassignments for a complaint."""

    return get_assignment_history(complaint_number.strip().upper())
