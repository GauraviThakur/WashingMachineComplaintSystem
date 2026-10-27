
from typing import Any

from app.repositories.machine_repository import (
    get_machine_by_serial_number,
)


def find_machine_by_serial_number(
    serial_number: str,
) -> dict[str, Any] | None:
    """Validate and retrieve a machine by serial number."""

    normalized_serial_number = serial_number.strip().upper()

    if not normalized_serial_number:
        return None

    return get_machine_by_serial_number(normalized_serial_number)
