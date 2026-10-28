
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

    return result


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
