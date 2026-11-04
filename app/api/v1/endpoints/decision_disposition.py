
from fastapi import APIRouter, HTTPException, status

from app.schemas.decision_disposition import (
    DecisionCreate,
    DispositionCreate,
    PhysicalCompletionCreate,
)

from app.services.decision_disposition_service import (
    create_decision,
    create_disposition,
    create_physical_completion,
    fetch_decision_disposition_history,
)


router = APIRouter(
    prefix="/api/v1/decision-disposition",
    tags=["Decision and Disposition"],
)


def handle_workflow_error(result: dict) -> None:
    error = result.get("error")

    if not error:
        return

    if error == "complaint_not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complaint not found.",
        )

    if error == "invalid_complaint_status":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "The operation is not allowed for the current complaint "
                f"status: {result.get('current_status')}."
            ),
        )

    error_messages = {
        "decision_already_recorded": (
            "A decision has already been recorded."
        ),
        "rejection_reason_required": (
            "A rejection reason is required."
        ),
        "decision_not_found": (
            "Record a decision before recording disposition."
        ),
        "disposition_not_found": (
            "Record a disposition before recording physical completion."
        ),
        "disposition_already_recorded": (
            "A disposition has already been recorded."
        ),
        "invalid_rejected_disposition": (
            "Rejected machines must use SCRAP."
        ),
        "invalid_accepted_disposition": (
            "Accepted machines must use RETURN_TO_STOCK "
            "or RETURN_TO_DEALER."
        ),
        "invalid_disposition": (
            "The recorded disposition is not supported."
        ),
        "invalid_completion_type": (
            "The physical completion type does not match "
            "the recorded disposition. "
            f"Expected: {result.get('expected_completion_type')}."
        ),
        "completion_reference_required": (
            "A reference number is required for dispatch "
            "and stock transfer completion."
        ),
        "physical_completion_already_recorded": (
            "Physical completion has already been recorded."
        ),
    }

    if error in error_messages:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=error_messages[error],
        )

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="An unexpected workflow error occurred.",
    )


@router.post(
    "/decision",
    status_code=status.HTTP_201_CREATED,
)
def submit_decision(decision_data: DecisionCreate):
    result = create_decision(decision_data)
    handle_workflow_error(result)

    return {
        "message": "Complaint decision recorded successfully.",
        **result,
    }


@router.post(
    "/disposition",
    status_code=status.HTTP_201_CREATED,
)
def submit_disposition(disposition_data: DispositionCreate):
    result = create_disposition(disposition_data)
    handle_workflow_error(result)

    return {
        "message": (
            "Complaint disposition recorded successfully. "
            "Physical completion is pending."
        ),
        **result,
    }


@router.post(
    "/physical-completion",
    status_code=status.HTTP_201_CREATED,
)
def submit_physical_completion(
    completion_data: PhysicalCompletionCreate,
):
    result = create_physical_completion(completion_data)
    handle_workflow_error(result)

    return {
        "message": (
            "Physical completion recorded successfully. "
            "Complaint closed."
        ),
        **result,
    }


@router.get("/{complaint_number}")
def get_decision_disposition(complaint_number: str):
    result = fetch_decision_disposition_history(complaint_number)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complaint not found.",
        )

    return result
