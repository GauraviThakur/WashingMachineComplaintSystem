
from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.schemas.team_assignment import TeamAssignmentCreate
from app.services.team_assignment_service import (
    assign_complaint,
    fetch_assignment_history,
)

router = APIRouter(
    prefix="/team-assignments",
    tags=["Team Assignments"],
)


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_team_assignment(
    assignment_data: TeamAssignmentCreate,
) -> dict[str, Any]:
    """Assign or reassign a complaint to a team."""

    result = assign_complaint(
        complaint_number=assignment_data.complaint_number,
        team_id=assignment_data.team_id,
        assigned_by=assignment_data.assigned_by,
        assignment_reason=assignment_data.assignment_reason,
        assigned_to=assignment_data.assigned_to,
    )

    error = result.get("error")

    if error == "complaint_not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complaint not found.",
        )

    if error == "team_not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The selected team does not exist or is inactive.",
        )

    if error == "complaint_not_ready_for_assignment":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "The complaint cannot be assigned in its current status: "
                f"{result.get('current_status')}."
            ),
        )

    if error == "complaint_already_assigned_to_team":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The complaint is already assigned to this team.",
        )

    return result


@router.get("/{complaint_number}")
def get_team_assignment_history(
    complaint_number: str,
) -> dict[str, Any]:
    """Retrieve assignment and reassignment history."""

    result = fetch_assignment_history(complaint_number)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complaint not found.",
        )

    return result
