
from datetime import datetime
import secrets
from typing import Any

from app.repositories.complaint_repository import register_complaint
from app.repositories.issue_type_repository import get_issue_type_by_id
from app.services.priority_service import determine_complaint_priority


def create_complaint(
    complaint_data: dict[str, Any],
) -> dict[str, Any]:
    """Create a complaint with automatically assigned priority."""

    serial_number = str(
        complaint_data.get("serial_number", "")
    ).strip().upper()

    if not serial_number:
        return {"error": "machine_not_found"}

    issue_type_id = complaint_data.get("issue_type_id")
    issue_type_name = None

    if issue_type_id is not None:
        issue_type = get_issue_type_by_id(issue_type_id)

        if issue_type is not None:
            issue_type_name = issue_type["issue_type_name"]

    reported_issue = complaint_data["reported_issue"]

    priority = determine_complaint_priority(
        reported_issue=reported_issue,
        issue_type_name=issue_type_name,
    )

    complaint_number = (
        f"CMP-{datetime.now().strftime('%Y%m%d')}-"
        f"{secrets.token_hex(4).upper()}"
    )

    result = register_complaint(
        complaint_number=complaint_number,
        serial_number=serial_number,
        customer_name=complaint_data["customer_name"],
        customer_contact=complaint_data.get("customer_contact"),
        dealer_email=complaint_data["dealer_email"],
        reported_issue=reported_issue,
        issue_type_id=issue_type_id,
        priority=priority,
        registered_by=complaint_data.get("registered_by", "system"),
        bulk_request_id=complaint_data.get("bulk_request_id"),
    )

    return result
