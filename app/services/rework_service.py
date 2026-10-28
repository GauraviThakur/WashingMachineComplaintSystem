
from typing import Any

from app.repositories.rework_repository import (
    create_rework_attempt,
    get_rework_history,
)
from app.schemas.rework import ReworkCreate


def record_rework(data: ReworkCreate) -> dict[str, Any]:
    rework_data = data.model_dump()

    rework_data["complaint_number"] = (
        rework_data["complaint_number"].strip().upper()
    )
    rework_data["performed_by"] = rework_data["performed_by"].strip()
    rework_data["rework_action"] = rework_data["rework_action"].strip()

    if rework_data["parts_replaced"] is not None:
        rework_data["parts_replaced"] = (
            rework_data["parts_replaced"].strip() or None
        )

    if rework_data["rework_notes"] is not None:
        rework_data["rework_notes"] = (
            rework_data["rework_notes"].strip() or None
        )

    return create_rework_attempt(**rework_data)


def fetch_rework_history(
    complaint_number: str,
) -> dict[str, Any] | None:
    return get_rework_history(complaint_number.strip().upper())
