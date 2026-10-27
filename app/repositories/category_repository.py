
from typing import Any

from app.database.connection import get_db_connection


def get_all_categories() -> list[dict[str, Any]]:
    """Retrieve all active complaint categories."""

    query = """
        SELECT
            category_id,
            category_name,
            description,
            is_active,
            created_at
        FROM complaint_categories
        WHERE is_active = TRUE
        ORDER BY category_name
    """

    with get_db_connection() as connection:
        rows = connection.execute(query).fetchall()

    return [dict(row) for row in rows]
