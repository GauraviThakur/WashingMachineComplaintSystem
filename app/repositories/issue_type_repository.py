
from typing import Any

from app.database.connection import get_db_connection


def get_issue_types(
    category_id: int | None = None,
) -> list[dict[str, Any]]:
    """Retrieve active issue types, optionally filtered by category."""

    query = """
        SELECT
            it.issue_type_id,
            it.category_id,
            c.category_name,
            it.issue_type_name,
            it.description,
            it.is_active,
            it.created_at
        FROM issue_types AS it
        INNER JOIN complaint_categories AS c
            ON c.category_id = it.category_id
        WHERE it.is_active = TRUE
          AND c.is_active = TRUE
    """

    parameters: tuple[int, ...] = ()

    if category_id is not None:
        query += " AND it.category_id = %s"
        parameters = (category_id,)

    query += " ORDER BY c.category_name, it.issue_type_name"

    with get_db_connection() as connection:
        rows = connection.execute(query, parameters).fetchall()

    return [dict(row) for row in rows]
