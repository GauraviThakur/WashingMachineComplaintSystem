
from fastapi import APIRouter, HTTPException, status

from app.schemas.rework import ReworkCreate
from app.services.rework_service import (
    fetch_rework_history,
    record_rework,
)

router = APIRouter(
    prefix="/api/v1/rework",
    tags=["Rework Management"],
)


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_rework(data: ReworkCreate):
    result = record_rework(data)

    if result.get("error") == "complaint_not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complaint not found.",
        )

    if result.get("error") == "invalid_complaint_status":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Rework can only be recorded when the complaint "
                "is ASSIGNED or UNDER_REWORK. Current status: "
                f"{result.get('current_status')}"
            ),
        )

    if result.get("error") == "active_assignment_not_found":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No active team assignment exists for this complaint.",
        )

    return {
        "message": "Rework attempt recorded successfully.",
        "data": result,
    }


@router.get("/{complaint_number}")
def get_rework(complaint_number: str):
    result = fetch_rework_history(complaint_number)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complaint not found.",
        )

    return result
