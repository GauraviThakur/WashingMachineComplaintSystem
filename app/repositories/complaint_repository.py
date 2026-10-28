
from typing import Any

from app.database.connection import get_db_connection


ALLOWED_STATUS_TRANSITIONS = {
    "REGISTERED": {"UNDER_INSPECTION"},
    "UNDER_INSPECTION": {"ASSIGNED"},
    "ASSIGNED": {"UNDER_REWORK"},
    "UNDER_REWORK": {"UNDER_TESTING"},
    "UNDER_TESTING": {"AWAITING_DECISION"},
    "AWAITING_DECISION": {
        "UNDER_REWORK",
        "AWAITING_DISPOSITION",
        "AWAITING_DISPATCH",
    },
    "AWAITING_DISPOSITION": set(),
    "AWAITING_DISPATCH": set(),
    "CLOSED": set(),
}


def register_complaint(
    *,
    complaint_number: str,
    serial_number: str,
    customer_name: str,
    customer_contact: str | None,
    dealer_email: str,
    reported_issue: str,
    issue_type_id: int | None,
    registered_by: str,
) -> dict[str, Any]:
    """Register a complaint and record its initial history."""

    with get_db_connection() as connection:
        machine = connection.execute(
            """
            SELECT machine_id, serial_number
            FROM machines
            WHERE serial_number = %s
            FOR UPDATE
            """,
            (serial_number,),
        ).fetchone()

        if machine is None:
            return {"error": "machine_not_found"}

        machine_id = machine["machine_id"]

        active_complaint = connection.execute(
            """
            SELECT
                complaint_id,
                complaint_number,
                complaint_status
            FROM complaints
            WHERE machine_id = %s
              AND complaint_status <> 'CLOSED'
            ORDER BY registered_at DESC
            LIMIT 1
            """,
            (machine_id,),
        ).fetchone()

        if active_complaint is not None:
            return {
                "error": "active_complaint_exists",
                "existing_complaint": dict(active_complaint),
            }

        previous_complaint = connection.execute(
            """
            SELECT complaint_id, complaint_number
            FROM complaints
            WHERE machine_id = %s
              AND complaint_status = 'CLOSED'
            ORDER BY closed_at DESC NULLS LAST,
                     registered_at DESC
            LIMIT 1
            """,
            (machine_id,),
        ).fetchone()

        if issue_type_id is not None:
            issue_type = connection.execute(
                """
                SELECT it.issue_type_id
                FROM issue_types AS it
                INNER JOIN complaint_categories AS c
                    ON c.category_id = it.category_id
                WHERE it.issue_type_id = %s
                  AND it.is_active = TRUE
                  AND c.is_active = TRUE
                """,
                (issue_type_id,),
            ).fetchone()

            if issue_type is None:
                return {"error": "invalid_issue_type"}

        previous_complaint_id = (
            previous_complaint["complaint_id"]
            if previous_complaint is not None
            else None
        )

        is_repeat_complaint = previous_complaint is not None

        complaint = connection.execute(
            """
            INSERT INTO complaints (
                complaint_number,
                machine_id,
                previous_complaint_id,
                customer_name,
                customer_contact,
                dealer_email,
                reported_issue,
                issue_type_id,
                priority,
                complaint_status,
                is_repeat_complaint
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s,
                'MEDIUM', 'REGISTERED', %s
            )
            RETURNING
                complaint_id,
                complaint_number,
                machine_id,
                previous_complaint_id,
                customer_name,
                customer_contact,
                dealer_email,
                reported_issue,
                issue_type_id,
                priority,
                complaint_status,
                is_repeat_complaint,
                registered_at,
                created_at,
                updated_at
            """,
            (
                complaint_number,
                machine_id,
                previous_complaint_id,
                customer_name,
                customer_contact,
                dealer_email,
                reported_issue,
                issue_type_id,
                is_repeat_complaint,
            ),
        ).fetchone()

        connection.execute(
            """
            INSERT INTO complaint_history (
                complaint_id,
                previous_status,
                new_status,
                changed_by,
                reason
            )
            VALUES (%s, NULL, 'REGISTERED', %s, %s)
            """,
            (
                complaint["complaint_id"],
                registered_by,
                "Complaint registered after the returned machine "
                "and dealer complaint email were received.",
            ),
        )

        result = dict(complaint)
        result["serial_number"] = machine["serial_number"]
        result["previous_complaint_number"] = (
            previous_complaint["complaint_number"]
            if previous_complaint is not None
            else None
        )

        return result


def get_complaint_by_number(
    complaint_number: str,
) -> dict[str, Any] | None:
    """Retrieve complaint details using its complaint number."""

    with get_db_connection() as connection:
        complaint = connection.execute(
            """
            SELECT
                c.complaint_id,
                c.complaint_number,
                c.machine_id,
                m.serial_number,
                m.model_number,
                m.batch_number,
                c.previous_complaint_id,
                previous.complaint_number AS previous_complaint_number,
                c.customer_name,
                c.customer_contact,
                c.dealer_email,
                c.reported_issue,
                c.issue_type_id,
                it.issue_type_name,
                cc.category_id,
                cc.category_name,
                c.priority,
                c.complaint_status,
                c.is_repeat_complaint,
                c.registered_at,
                c.closed_at,
                c.created_at,
                c.updated_at
            FROM complaints AS c
            INNER JOIN machines AS m
                ON m.machine_id = c.machine_id
            LEFT JOIN complaints AS previous
                ON previous.complaint_id = c.previous_complaint_id
            LEFT JOIN issue_types AS it
                ON it.issue_type_id = c.issue_type_id
            LEFT JOIN complaint_categories AS cc
                ON cc.category_id = it.category_id
            WHERE c.complaint_number = %s
            """,
            (complaint_number,),
        ).fetchone()

        if complaint is None:
            return None

        return dict(complaint)


def get_machine_complaint_history(
    serial_number: str,
) -> dict[str, Any] | None:
    """Return all complaints registered for a machine, oldest first."""

    normalized_serial = serial_number.strip().upper()

    with get_db_connection() as connection:
        machine = connection.execute(
            """
            SELECT machine_id, serial_number, model_number, batch_number
            FROM machines
            WHERE serial_number = %s
            """,
            (normalized_serial,),
        ).fetchone()

        if machine is None:
            return None

        complaints = connection.execute(
            """
            SELECT
                c.complaint_id,
                c.complaint_number,
                c.complaint_status,
                c.priority,
                c.reported_issue,
                c.issue_type_id,
                it.issue_type_name,
                c.is_repeat_complaint,
                c.previous_complaint_id,
                previous.complaint_number AS previous_complaint_number,
                c.registered_at,
                c.closed_at
            FROM complaints AS c
            LEFT JOIN issue_types AS it
                ON it.issue_type_id = c.issue_type_id
            LEFT JOIN complaints AS previous
                ON previous.complaint_id = c.previous_complaint_id
            WHERE c.machine_id = %s
            ORDER BY c.registered_at ASC, c.complaint_id ASC
            """,
            (machine["machine_id"],),
        ).fetchall()

        return {
            "machine_id": machine["machine_id"],
            "serial_number": machine["serial_number"],
            "model_number": machine["model_number"],
            "batch_number": machine["batch_number"],
            "total_complaints": len(complaints),
            "complaints": [dict(row) for row in complaints],
        }


def update_complaint_status(
    *,
    complaint_number: str,
    new_status: str,
    changed_by: str,
    reason: str,
) -> dict[str, Any]:
    """Validate a status transition and record its audit history."""

    with get_db_connection() as connection:
        complaint = connection.execute(
            """
            SELECT complaint_id, complaint_number, complaint_status
            FROM complaints
            WHERE complaint_number = %s
            FOR UPDATE
            """,
            (complaint_number,),
        ).fetchone()

        if complaint is None:
            return {"error": "complaint_not_found"}

        previous_status = complaint["complaint_status"]

        permitted_statuses = ALLOWED_STATUS_TRANSITIONS.get(
            previous_status,
            set(),
        )

        if new_status not in permitted_statuses:
            return {
                "error": "invalid_status_transition",
                "current_status": previous_status,
                "requested_status": new_status,
                "allowed_statuses": sorted(permitted_statuses),
            }

        updated_complaint = connection.execute(
            """
            UPDATE complaints
            SET complaint_status = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE complaint_id = %s
            RETURNING
                complaint_id,
                complaint_number,
                complaint_status,
                updated_at
            """,
            (
                new_status,
                complaint["complaint_id"],
            ),
        ).fetchone()

        connection.execute(
            """
            INSERT INTO complaint_history (
                complaint_id,
                previous_status,
                new_status,
                changed_by,
                reason
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                complaint["complaint_id"],
                previous_status,
                new_status,
                changed_by,
                reason,
            ),
        )

        return dict(updated_complaint)
