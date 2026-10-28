
from fastapi import APIRouter, HTTPException, status

from app.schemas.testing import TestCreate
from app.services.testing_service import (
    record_test,
    fetch_test_history,
)

router = APIRouter(
    prefix="/api/v1/testing",
    tags=["Testing"],
)


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_test(test_data: TestCreate):
    result = record_test(test_data)

    if result.get("error") == "complaint_not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complaint not found.",
        )

    if result.get("error") == "invalid_complaint_status":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Testing is allowed only when the complaint status is "
                f"UNDER_TESTING. Current status: "
                f"{result.get('current_status')}."
            ),
        )

    return {
        "message": "Test result recorded successfully.",
        **result,
    }


@router.get("/{complaint_number}")
def get_testing_history(complaint_number: str):
    result = fetch_test_history(complaint_number)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complaint not found.",
        )

    return result
