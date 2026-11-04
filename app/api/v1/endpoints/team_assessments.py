
from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.schemas.team_assessment import TeamAssessmentCreate
from app.services.team_assessment_service import (
    fetch_pending_team_assessments,
    fetch_team_assessment_history,
    record_team_assessment,
)


router = APIRouter(
    prefix="/api/v1/team-assessments",
    tags=["Team Assessment"],
)


@router.get("/pending")
def get_pending_assessments() -> dict[str, Any]:
    result = fetch_pending_team_assessments()

    return {
        "message": "Pending team assessments retrieved successfully.",
        "data": result,
    }


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_team_assessment(
    data: TeamAssessmentCreate,
) -> dict[str, Any]:
    result = record_team_assessment(data)

    if result.get("error") == "complaint_not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complaint not found.",
        )

    if result.get("error") == "complaint_not_ready_for_assessment":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Team assessment can only be submitted when the "
                "complaint is ASSIGNED. Current status: "
                f"{result.get('current_status')}"
            ),
        )

    if result.get("error") == "active_assignment_not_found":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No active team assignment exists for this complaint.",
        )

    if result.get("error") == "assignment_already_assessed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This team assignment has already been assessed.",
        )

    if result.get("error") == "invalid_assessment_outcome":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid team assessment outcome.",
        )

    return {
        "message": "Team assessment submitted successfully.",
        "data": result,
    }


@router.get("/{complaint_number}")
def get_team_assessment(
    complaint_number: str,
) -> dict[str, Any]:
    result = fetch_team_assessment_history(complaint_number)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complaint not found.",
        )

    return result
