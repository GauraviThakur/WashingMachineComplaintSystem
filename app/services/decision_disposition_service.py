
from app.repositories.decision_disposition_repository import (
    record_complaint_decision,
    record_complaint_disposition,
    get_decision_disposition_history,
)
from app.schemas.decision_disposition import (
    DecisionCreate,
    DispositionCreate,
)


def create_decision(decision_data: DecisionCreate) -> dict:
    return record_complaint_decision(
        complaint_number=decision_data.complaint_number.strip().upper(),
        decision_type=decision_data.decision_type,
        decision_reason=decision_data.decision_reason,
        rejection_reason=decision_data.rejection_reason,
        decided_by=decision_data.decided_by,
    )


def create_disposition(disposition_data: DispositionCreate) -> dict:
    return record_complaint_disposition(
        complaint_number=disposition_data.complaint_number.strip().upper(),
        disposition_type=disposition_data.disposition_type,
        disposition_reason=disposition_data.disposition_reason,
        recorded_by=disposition_data.recorded_by,
    )


def fetch_decision_disposition_history(
    complaint_number: str,
) -> dict | None:
    return get_decision_disposition_history(
        complaint_number.strip().upper()
    )
