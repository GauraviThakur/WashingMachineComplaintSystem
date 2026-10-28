
from typing import Any

from app.repositories.inspection_repository import (
    create_inspection,
    get_inspections_by_complaint,
)
from app.schemas.inspection import InspectionCreate


def record_inspection(data: InspectionCreate) -> dict[str, Any]:
    """Validate and record an inspection for a registered complaint."""
    inspection_data = data.model_dump()

    inspection_data["complaint_number"] = (
        inspection_data["complaint_number"].strip().upper()
    )

    inspection_data["inspected_by"] = (
        inspection_data["inspected_by"].strip()
    )

    return create_inspection(**inspection_data)


def fetch_complaint_inspections(
    complaint_number: str,
) -> dict[str, Any] | None:
    """Retrieve all inspections recorded for a complaint."""
    normalized_complaint_number = complaint_number.strip().upper()

    return get_inspections_by_complaint(normalized_complaint_number)
