
from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.schemas.team_assignment import (
    AutomaticTeamAssignmentCreate,
    TeamAssignmentCreate,
)
from app.services.team_assignment_service import (
    assign_complaint,
    assign_complaint_automatically,
    fetch_assignment_history,
)


router = APIRouter(
    prefix="/api/v1/team-assignments",
    tags=["Team Assignments"],
)


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_team_assignment(
    data: TeamAssignmentCreate,
) -> dict[str, Any]:
    result = assign_complaint(**data.model_dump())

    if result.get("error"):
        error = result["error"]

        if error == "complaint_not_found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Complaint was not found.",
            )

        if error == "team_not_found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Active team was not found.",
            )

        if error == "complaint_not_ready_for_assignment":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Complaint must be under inspection or already "
                    "assigned before a team can be assigned."
                ),
            )

        if error == "complaint_already_assigned_to_team":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Complaint is already assigned to this team.",
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Team assignment could not be completed.",
        )

    return {
        "message": "Complaint assigned successfully.",
        "data": result,
    }


@router.post("/automatic", status_code=status.HTTP_201_CREATED)
def create_automatic_team_assignment(
    data: AutomaticTeamAssignmentCreate,
) -> dict[str, Any]:
    result = assign_complaint_automatically(**data.model_dump())

    if result.get("error"):
        error = result["error"]

        if error == "complaint_not_found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Complaint was not found.",
            )

        if error == "complaint_not_ready_for_assignment":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Complaint must be under inspection or already "
                    "assigned before automatic assignment."
                ),
            )

        if error == "inspection_issue_type_missing":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "No inspection with an issue type was found. "
                    "Record an inspection with an issue type first."
                ),
            )

        if error == "primary_team_mapping_not_found":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "No active primary team mapping exists for the "
                    "inspection issue type."
                ),
            )

        if error == "team_not_found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Active team was not found.",
            )

        if error == "complaint_already_assigned_to_team":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Complaint is already assigned to this team.",
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Automatic team assignment could not be completed.",
        )

    return {
        "message": "Complaint assigned automatically based on inspection findings.",
        "data": result,
    }


@router.get("/{complaint_number}")
def get_team_assignment_history(
    complaint_number: str,
) -> dict[str, Any]:
    result = fetch_assignment_history(complaint_number)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complaint was not found.",
        )

    return {
        "message": "Team assignment history retrieved successfully.",
        "data": result,
    }
