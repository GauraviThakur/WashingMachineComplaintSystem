
from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.schemas.inspection import InspectionCreate
from app.services.inspection_service import (
    fetch_complaint_inspections,
    record_inspection,
)

router = APIRouter(
    prefix="/inspections",
    tags=["Inspections"],
)


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_inspection_endpoint(
    inspection_data: InspectionCreate,
) -> dict[str, Any]:
    """Record a new inspection for a complaint."""

    result = record_inspection(inspection_data)

    error = result.get("error")

    if not error:
        return result

    if error == "complaint_not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complaint not found.",
        )

    if error == "complaint_not_ready_for_inspection":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "This complaint is not ready for inspection. "
                f"Current status: {result.get('current_status')}."
            ),
        )

    if error == "invalid_issue_type":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The selected issue type does not exist or is inactive.",
        )

    if error == "invalid_inspection_outcome":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The supplied inspection outcome is invalid.",
        )

    if error == "issue_type_required_for_team_assignment":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "An issue type is required when the inspection outcome "
                "is ISSUE_IDENTIFIED or REPAIR_REQUIRED."
            ),
        )

    if error == "primary_team_mapping_not_found":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "No active primary team mapping exists for the selected "
                "issue type. Configure a primary team mapping first."
            ),
        )

    if error == "complaint_already_has_active_assignment":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This complaint already has an active team assignment.",
        )

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="An unexpected error occurred while recording the inspection.",
    )


@router.get("/{complaint_number}")
def get_inspections_endpoint(
    complaint_number: str,
) -> dict[str, Any]:
    """Retrieve inspection history for a complaint."""

    result = fetch_complaint_inspections(complaint_number)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complaint not found.",
        )

    return result
