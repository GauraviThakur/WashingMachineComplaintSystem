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

        if current_status not in (
            "AWAITING_DECISION",
            "AWAITING_QUALITY_REVIEW",
        ):
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

        # Validate the disposition against the quality decision.
        if decision["decision_type"] == "REJECTED":
            if disposition_type != "SCRAP":
                return {
                    "error": "invalid_rejected_disposition",
                    "message": (
                        "Rejected machines must use SCRAP "
                        "as their disposition."
                    ),
                }

        elif decision["decision_type"] == "ACCEPTED":
            if disposition_type not in (
                "RETURN_TO_STOCK",
                "RETURN_TO_DEALER",
            ):
                return {
                    "error": "invalid_accepted_disposition",
                    "message": (
                        "Accepted machines must use RETURN_TO_STOCK "
                        "or RETURN_TO_DEALER."
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

        # A disposition does not close the complaint.
        # The complaint must wait for its physical action.
        status_mapping = {
            "RETURN_TO_DEALER": "AWAITING_DISPATCH",
            "RETURN_TO_STOCK": "AWAITING_STOCK_TRANSFER",
            "SCRAP": "AWAITING_SCRAP",
        }

        new_status = status_mapping[disposition_type]

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
                recorded_by,
                (
                    f"Final disposition recorded: {disposition_type}. "
                    f"Physical completion is pending. "
                    f"Reason: {disposition_reason}"
                ),
            ),
        )

        return {
            "complaint_number": complaint["complaint_number"],
            "previous_status": current_status,
            "complaint_status": new_status,
            "disposition": dict(disposition),
        }


def record_physical_completion(
    *,
    complaint_number: str,
    completion_type: str,
    reference_number: str | None,
    completion_details: str | None,
    completed_by: str,
) -> dict[str, Any]:
    with get_db_connection() as connection:
        complaint = connection.execute(
            """
            SELECT
                complaint_id,
                complaint_number,
                complaint_status,
                bulk_request_id
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
        bulk_request_id = complaint["bulk_request_id"]

        disposition = connection.execute(
            """
            SELECT
                disposition_id,
                disposition_type
            FROM complaint_dispositions
            WHERE complaint_id = %s
            """,
            (complaint_id,),
        ).fetchone()

        if not disposition:
            return {"error": "disposition_not_found"}

        # Each disposition has exactly one permitted physical action.
        action_mapping = {
            "RETURN_TO_DEALER": {
                "completion_type": "DISPATCH",
                "status": "AWAITING_DISPATCH",
            },
            "RETURN_TO_STOCK": {
                "completion_type": "STOCK_TRANSFER",
                "status": "AWAITING_STOCK_TRANSFER",
            },
            "SCRAP": {
                "completion_type": "SCRAP",
                "status": "AWAITING_SCRAP",
            },
        }

        expected_action = action_mapping.get(
            disposition["disposition_type"]
        )

        if not expected_action:
            return {"error": "invalid_disposition"}

        if completion_type != expected_action["completion_type"]:
            return {
                "error": "invalid_completion_type",
                "expected_completion_type": (
                    expected_action["completion_type"]
                ),
            }

        if current_status != expected_action["status"]:
            return {
                "error": "invalid_complaint_status",
                "current_status": current_status,
                "expected_status": expected_action["status"],
            }

        if completion_type in ("DISPATCH", "STOCK_TRANSFER"):
            if not reference_number or not reference_number.strip():
                return {"error": "completion_reference_required"}

        existing_completion = connection.execute(
            """
            SELECT completion_id
            FROM complaint_physical_completions
            WHERE complaint_id = %s
            """,
            (complaint_id,),
        ).fetchone()

        if existing_completion:
            return {"error": "physical_completion_already_recorded"}

        completion = connection.execute(
            """
            INSERT INTO complaint_physical_completions (
                complaint_id,
                disposition_id,
                completion_type,
                reference_number,
                completion_details,
                completed_by
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING
                completion_id,
                completion_type,
                reference_number,
                completion_details,
                completed_by,
                completed_at
            """,
            (
                complaint_id,
                disposition["disposition_id"],
                completion_type,
                (
                    reference_number.strip()
                    if reference_number
                    else None
                ),
                completion_details,
                completed_by,
            ),
        ).fetchone()

        # Close only after physical completion has been recorded.
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
                completed_by,
                (
                    f"Physical action completed: {completion_type}. "
                    f"Reference: {reference_number or 'Not provided'}. "
                    "Complaint closed after physical completion."
                ),
            ),
        )

        bulk_completion_status = None

        # Update the parent request only when this complaint
        # originated from a bulk upload.
        if bulk_request_id is not None:

            # Lock the parent row so concurrent complaint closures
            # cannot calculate the parent completion status incorrectly.
            bulk_request = connection.execute(
                """
                SELECT invalid_rows
                FROM bulk_requests
                WHERE bulk_request_id = %s
                FOR UPDATE
                """,
                (bulk_request_id,),
            ).fetchone()

            if bulk_request is not None:
                remaining_complaints = connection.execute(
                    """
                    SELECT COUNT(*) AS open_complaints
                    FROM complaints
                    WHERE bulk_request_id = %s
                      AND complaint_status <> 'CLOSED'
                    """,
                    (bulk_request_id,),
                ).fetchone()

                open_complaint_count = remaining_complaints[
                    "open_complaints"
                ]

                if open_complaint_count == 0:
                    if bulk_request["invalid_rows"] > 0:
                        bulk_completion_status = "COMPLETED_WITH_ERRORS"
                    else:
                        bulk_completion_status = "COMPLETED"

                    connection.execute(
                        """
                        UPDATE bulk_requests
                        SET complaint_completion_status = %s,
                            complaints_completed_at = CURRENT_TIMESTAMP
                        WHERE bulk_request_id = %s
                        """,
                        (
                            bulk_completion_status,
                            bulk_request_id,
                        ),
                    )

                else:
                    bulk_completion_status = "IN_PROGRESS"

                    connection.execute(
                        """
                        UPDATE bulk_requests
                        SET complaint_completion_status = %s,
                            complaints_completed_at = NULL
                        WHERE bulk_request_id = %s
                        """,
                        (
                            bulk_completion_status,
                            bulk_request_id,
                        ),
                    )

        return {
            "complaint_number": complaint["complaint_number"],
            "previous_status": current_status,
            "complaint_status": new_status,
            "physical_completion": dict(completion),
            "bulk_request_id": bulk_request_id,
            "bulk_complaint_completion_status": (
                bulk_completion_status
            ),
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

        complaint_id = complaint["complaint_id"]

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
            (complaint_id,),
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
            (complaint_id,),
        ).fetchone()

        physical_completion = connection.execute(
            """
            SELECT
                completion_id,
                completion_type,
                reference_number,
                completion_details,
                completed_by,
                completed_at
            FROM complaint_physical_completions
            WHERE complaint_id = %s
            """,
            (complaint_id,),
        ).fetchone()

        return {
            "complaint_number": complaint["complaint_number"],
            "complaint_status": complaint["complaint_status"],
            "decision": dict(decision) if decision else None,
            "disposition": (
                dict(disposition) if disposition else None
            ),
            "physical_completion": (
                dict(physical_completion)
                if physical_completion
                else None
            ),
        }