
from typing import Any

from psycopg.types.json import Jsonb

from app.database.connection import get_db_connection


def create_bulk_request(
    *,
    source_file_name: str,
    uploaded_by: str,
    total_rows: int,
) -> dict[str, Any]:
    """Create a record for an uploaded CSV or Excel file."""

    with get_db_connection() as connection:
        request = connection.execute(
            """
            INSERT INTO bulk_requests (
                source_file_name,
                uploaded_by,
                total_rows,
                request_status
            )
            VALUES (%s, %s, %s, 'VALIDATING')
            RETURNING
                bulk_request_id,
                source_file_name,
                uploaded_by,
                total_rows,
                valid_rows,
                invalid_rows,
                request_status,
                uploaded_at,
                completed_at
            """,
            (source_file_name, uploaded_by, total_rows),
        ).fetchone()

        return dict(request)


def create_bulk_request_rows(
    *,
    bulk_request_id: int,
    rows: list[dict[str, Any]],
) -> None:
    """Store the original data for each uploaded row."""

    with get_db_connection() as connection:
        for row in rows:
            connection.execute(
                """
                INSERT INTO bulk_request_rows (
                    bulk_request_id,
                    row_number,
                    row_data,
                    validation_status
                )
                VALUES (%s, %s, %s, 'PENDING')
                """,
                (
                    bulk_request_id,
                    row["row_number"],
                    Jsonb(row["row_data"]),
                ),
            )


def update_bulk_request_row(
    *,
    bulk_request_id: int,
    row_number: int,
    validation_status: str,
    validation_errors: list[str] | None = None,
    complaint_id: int | None = None,
) -> None:
    """Save the validation result for one uploaded row."""

    with get_db_connection() as connection:
        connection.execute(
            """
            UPDATE bulk_request_rows
            SET validation_status = %s,
                validation_errors = %s,
                complaint_id = %s
            WHERE bulk_request_id = %s
              AND row_number = %s
            """,
            (
                validation_status,
                (
                    Jsonb(validation_errors)
                    if validation_errors is not None
                    else None
                ),
                complaint_id,
                bulk_request_id,
                row_number,
            ),
        )


def finish_bulk_request(
    *,
    bulk_request_id: int,
    valid_rows: int,
    invalid_rows: int,
) -> dict[str, Any] | None:
    """Store final counts and processing status for a bulk request."""

    if valid_rows == 0:
        request_status = "FAILED"
    elif invalid_rows > 0:
        request_status = "PARTIALLY_PROCESSED"
    else:
        request_status = "PROCESSED"

    with get_db_connection() as connection:
        request = connection.execute(
            """
            UPDATE bulk_requests
            SET valid_rows = %s,
                invalid_rows = %s,
                request_status = %s,
                completed_at = CURRENT_TIMESTAMP
            WHERE bulk_request_id = %s
            RETURNING
                bulk_request_id,
                source_file_name,
                uploaded_by,
                total_rows,
                valid_rows,
                invalid_rows,
                request_status,
                uploaded_at,
                completed_at
            """,
            (
                valid_rows,
                invalid_rows,
                request_status,
                bulk_request_id,
            ),
        ).fetchone()

        return dict(request) if request is not None else None


def get_bulk_request(
    bulk_request_id: int,
) -> dict[str, Any] | None:
    """Retrieve the summary for a bulk request."""

    with get_db_connection() as connection:
        request = connection.execute(
            """
            SELECT
                bulk_request_id,
                source_file_name,
                uploaded_by,
                total_rows,
                valid_rows,
                invalid_rows,
                request_status,
                uploaded_at,
                completed_at
            FROM bulk_requests
            WHERE bulk_request_id = %s
            """,
            (bulk_request_id,),
        ).fetchone()

        return dict(request) if request is not None else None


def get_bulk_request_rows(
    bulk_request_id: int,
) -> list[dict[str, Any]] | None:
    """Retrieve row-level results, including linked complaint details."""

    with get_db_connection() as connection:
        request = connection.execute(
            """
            SELECT bulk_request_id
            FROM bulk_requests
            WHERE bulk_request_id = %s
            """,
            (bulk_request_id,),
        ).fetchone()

        if request is None:
            return None

        rows = connection.execute(
            """
            SELECT
                br.bulk_row_id,
                br.bulk_request_id,
                br.row_number,
                br.row_data,
                br.validation_status,
                br.validation_errors,
                br.complaint_id,
                c.complaint_number,
                c.complaint_status,
                c.priority,
                c.reported_issue AS registered_reported_issue,
                it.issue_type_name,
                br.created_at
            FROM bulk_request_rows AS br
            LEFT JOIN complaints AS c
                ON c.complaint_id = br.complaint_id
            LEFT JOIN issue_types AS it
                ON it.issue_type_id = c.issue_type_id
            WHERE br.bulk_request_id = %s
            ORDER BY br.row_number
            """,
            (bulk_request_id,),
        ).fetchall()

        return [dict(row) for row in rows]
