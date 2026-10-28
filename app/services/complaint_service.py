
from datetime import datetime
import secrets
from typing import Any

from app.repositories.complaint_repository import register_complaint


def create_complaint(
    complaint_data: dict[str, Any],
) -> dict[str, Any]:
    """Validate registration essentials and create a complaint."""

    serial_number = str(
        complaint_data.get("serial_number", "")
    ).strip().upper()

    if not serial_number:
        return {"error": "machine_not_found"}

    # Generate a readable, unique complaint reference.
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
        reported_issue=complaint_data["reported_issue"],
        issue_type_id=complaint_data.get("issue_type_id"),
        registered_by=complaint_data["registered_by"],
    )

    return result
