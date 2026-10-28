
from fastapi import APIRouter, HTTPException, status

from app.repositories.complaint_repository import (
    get_complaint_by_number,
    get_machine_complaint_history,
    update_complaint_status,
)
from app.schemas.complaint import ComplaintCreate
from app.schemas.complaint_workflow import ComplaintStatusUpdate
from app.services.complaint_service import create_complaint


router = APIRouter(
    prefix="/complaints",
    tags=["Complaints"],
)


@router.post("/", status_code=status.HTTP_201_CREATED)
def register_new_complaint(
    complaint_data: ComplaintCreate,
) -> dict:
    """Register a complaint for a returned washing machine."""

    result = create_complaint(
        complaint_data=complaint_data.model_dump()
    )

    error = result.get("error")

    if error == "machine_not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "message": "Machine not found. Verify the serial number.",
                "status": "not_found",
            },
        )

    if error == "active_complaint_exists":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": (
                    "An active complaint already exists for this machine."
                ),
                "existing_complaint": result["existing_complaint"],
            },
        )

    if error == "invalid_issue_type":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "The selected issue type is invalid or inactive."
            },
        )

    return {
        "message": "Complaint registered successfully",
        "complaint": result,
    }


@router.get("/machine/{serial_number}/history")
def get_machine_history(serial_number: str) -> dict:
    """Retrieve all complaints associated with a machine serial number."""

    history = get_machine_complaint_history(
        serial_number=serial_number
    )

    if history is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "message": "Machine not found. Verify the serial number.",
                "serial_number": serial_number,
            },
        )

    return {
        "message": "Machine complaint history retrieved successfully",
        "history": history,
    }


@router.get("/{complaint_number}")
def get_complaint(complaint_number: str) -> dict:
    """Retrieve a complaint using its complaint number."""

    complaint = get_complaint_by_number(
        complaint_number=complaint_number.strip()
    )

    if complaint is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "message": "Complaint not found.",
                "complaint_number": complaint_number,
            },
        )

    return {
        "message": "Complaint retrieved successfully",
        "complaint": complaint,
    }


@router.patch("/{complaint_number}/status")
def change_complaint_status(
    complaint_number: str,
    status_data: ComplaintStatusUpdate,
) -> dict:
    """Change a complaint's status and record the reason in its history."""

    result = update_complaint_status(
        complaint_number=complaint_number.strip(),
        new_status=status_data.new_status,
        changed_by=status_data.changed_by,
        reason=status_data.reason,
    )

    error = result.get("error")

    if error == "complaint_not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "message": "Complaint not found.",
                "complaint_number": complaint_number,
            },
        )

    if error == "invalid_status_transition":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "This complaint status transition is not allowed.",
                "current_status": result["current_status"],
                "requested_status": result["requested_status"],
                "allowed_statuses": result["allowed_statuses"],
            },
        )

    return {
        "message": "Complaint status updated successfully",
        "complaint": result,
    }
