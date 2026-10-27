
from typing import Any

from app.database.connection import get_db_connection


def get_machine_by_serial_number(
    serial_number: str,
) -> dict[str, Any] | None:
    """Find a machine using its unique serial number."""

    query = """
        SELECT
            machine_id,
            serial_number,
            model_number,
            batch_number,
            manufacturing_date,
            created_at,
            updated_at
        FROM machines
        WHERE serial_number = %s
    """

    with get_db_connection() as connection:
        row = connection.execute(
            query,
            (serial_number,),
        ).fetchone()

    return dict(row) if row is not None else None
