
from typing import Any

from app.database.connection import get_db_connection


def record_complaint_decision(
    *,
    complaint_number: str,
    decision_type: str,
    decision_reason: str,
    rejection_reason: str | None,
    decided_by: str,
) -> dict[str, Any]:
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

        if not complaint:
            return {"error": "complaint_not_found"}

        complaint_id = complaint["complaint_id"]
        current_status = complaint["complaint_status"]

        if current_status != "AWAITING_DECISION":
            return {
                "error": "invalid_complaint_status",
                "current_status": current_status,
            }

        existing_decision = connection.execute(
            """
            SELECT decision_id
            FROM complaint_decisions
            WHERE complaint_id = %s
            """,
            (complaint_id,),
        ).fetchone()

        if existing_decision:
            return {"error": "decision_already_recorded"}

        if decision_type == "REJECTED":
            if not rejection_reason or len(rejection_reason.strip()) < 3:
                return {"error": "rejection_reason_required"}

        decision = connection.execute(
            """
            INSERT INTO complaint_decisions (
                complaint_id,
                decision_type,
                decision_reason,
                rejection_reason,
                decided_by
            )
            VALUES (%s, %s, %s, %s, %s)
            RETURNING
                decision_id,
                decision_type,
                decision_reason,
                rejection_reason,
                decided_by,
                decided_at
            """,
            (
                complaint_id,
                decision_type,
                decision_reason,
                rejection_reason,
                decided_by,
            ),
        ).fetchone()

        if decision_type == "ACCEPTED":
            new_status = "AWAITING_DISPOSITION"
        else:
            new_status = "AWAITING_DISPOSITION"

        connection.execute(
            """
            UPDATE complaints
            SET complaint_status = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE complaint_id = %s
            """,
            (new_status, complaint_id),
        )

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
                complaint_id,
                current_status,
                new_status,
                decided_by,
                (
                    f"Final decision recorded: {decision_type}. "
                    f"Reason: {decision_reason}"
                ),
            ),
        )

        return {
            "complaint_number": complaint["complaint_number"],
            "previous_status": current_status,
            "complaint_status": new_status,
            "decision": dict(decision),
        }


def record_complaint_disposition(
    *,
    complaint_number: str,
    disposition_type: str,
    disposition_reason: str,
    recorded_by: str,
) -> dict[str, Any]:
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

        if not complaint:
            return {"error": "complaint_not_found"}

        complaint_id = complaint["complaint_id"]
        current_status = complaint["complaint_status"]

        if current_status != "AWAITING_DISPOSITION":
            return {
                "error": "invalid_complaint_status",
                "current_status": current_status,
            }

        decision = connection.execute(
            """
            SELECT decision_type
            FROM complaint_decisions
            WHERE complaint_id = %s
            """,
            (complaint_id,),
        ).fetchone()

        if not decision:
            return {"error": "decision_not_found"}

        if decision["decision_type"] == "REJECTED":
            if disposition_type not in ("SCRAP", "HOLD", "OTHER"):
                return {
                    "error": "invalid_rejected_disposition",
                    "message": (
                        "Rejected machines must use SCRAP, HOLD, or OTHER "
                        "as their disposition."
                    ),
                }

        elif decision["decision_type"] == "ACCEPTED":
            if disposition_type not in (
                "RETURN_TO_STOCK",
                "RETURN_TO_DEALER",
                "HOLD",
                "OTHER",
            ):
                return {
                    "error": "invalid_accepted_disposition",
                    "message": (
                        "Accepted machines cannot use SCRAP through this "
                        "workflow. Choose a permitted disposition."
                    ),
                }

        existing_disposition = connection.execute(
            """
            SELECT disposition_id
            FROM complaint_dispositions
            WHERE complaint_id = %s
            """,
            (complaint_id,),
        ).fetchone()

        if existing_disposition:
            return {"error": "disposition_already_recorded"}

        disposition = connection.execute(
            """
            INSERT INTO complaint_dispositions (
                complaint_id,
                disposition_type,
                disposition_reason,
                recorded_by
            )
            VALUES (%s, %s, %s, %s)
            RETURNING
                disposition_id,
                disposition_type,
                disposition_reason,
                recorded_by,
                recorded_at
            """,
            (
                complaint_id,
                disposition_type,
                disposition_reason,
                recorded_by,
            ),
        ).fetchone()

        new_status = "CLOSED"

        connection.execute(
            """
            UPDATE complaints
            SET complaint_status = %s,
                closed_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE complaint_id = %s
            """,
            (new_status, complaint_id),
        )

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
                complaint_id,
                current_status,
                new_status,
                recorded_by,
                (
                    f"Final disposition recorded: {disposition_type}. "
                    f"Complaint closed. Reason: {disposition_reason}"
                ),
            ),
        )

        return {
            "complaint_number": complaint["complaint_number"],
            "previous_status": current_status,
            "complaint_status": new_status,
            "disposition": dict(disposition),
        }


def get_decision_disposition_history(
    complaint_number: str,
) -> dict[str, Any] | None:
    with get_db_connection() as connection:
        complaint = connection.execute(
            """
            SELECT complaint_id, complaint_number, complaint_status
            FROM complaints
            WHERE complaint_number = %s
            """,
            (complaint_number,),
        ).fetchone()

        if not complaint:
            return None

        decision = connection.execute(
            """
            SELECT
                decision_id,
                decision_type,
                decision_reason,
                rejection_reason,
                decided_by,
                decided_at
            FROM complaint_decisions
            WHERE complaint_id = %s
            """,
            (complaint["complaint_id"],),
        ).fetchone()

        disposition = connection.execute(
            """
            SELECT
                disposition_id,
                disposition_type,
                disposition_reason,
                recorded_by,
                recorded_at
            FROM complaint_dispositions
            WHERE complaint_id = %s
            """,
            (complaint["complaint_id"],),
        ).fetchone()

        return {
            "complaint_number": complaint["complaint_number"],
            "complaint_status": complaint["complaint_status"],
            "decision": dict(decision) if decision else None,
            "disposition": (
                dict(disposition) if disposition else None
            ),
        }
