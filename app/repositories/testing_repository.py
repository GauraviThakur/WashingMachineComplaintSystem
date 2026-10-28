
from typing import Any

from app.database.connection import get_db_connection


def create_test_record(
    *,
    complaint_number: str,
    tested_by: str,
    test_type: str,
    test_result: str,
    test_observations: str,
    test_notes: str | None,
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

        if current_status != "UNDER_TESTING":
            return {
                "error": "invalid_complaint_status",
                "current_status": current_status,
            }

        previous_test = connection.execute(
            """
            SELECT COALESCE(MAX(test_number), 0) AS last_test
            FROM complaint_tests
            WHERE complaint_id = %s
            """,
            (complaint_id,),
        ).fetchone()

        test_number = previous_test["last_test"] + 1

        test_record = connection.execute(
            """
            INSERT INTO complaint_tests (
                complaint_id,
                test_number,
                tested_by,
                test_type,
                test_result,
                test_observations,
                test_notes
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING
                test_id,
                complaint_id,
                test_number,
                tested_by,
                test_type,
                test_result,
                test_observations,
                test_notes,
                tested_at,
                created_at
            """,
            (
                complaint_id,
                test_number,
                tested_by,
                test_type,
                test_result,
                test_observations,
                test_notes,
            ),
        ).fetchone()

        if test_result == "PASS":
            new_status = "AWAITING_DECISION"
            history_reason = (
                f"Test attempt {test_number} passed. "
                "Complaint moved to awaiting decision."
            )
        else:
            new_status = "UNDER_REWORK"
            history_reason = (
                f"Test attempt {test_number} failed. "
                "Complaint returned for corrective rework."
            )

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
                tested_by,
                history_reason,
            ),
        )

        return {
            "complaint_number": complaint["complaint_number"],
            "complaint_status": new_status,
            "test_record": dict(test_record),
        }


def get_test_history(
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

        test_records = connection.execute(
            """
            SELECT
                test_id,
                test_number,
                tested_by,
                test_type,
                test_result,
                test_observations,
                test_notes,
                tested_at,
                created_at
            FROM complaint_tests
            WHERE complaint_id = %s
            ORDER BY test_number
            """,
            (complaint["complaint_id"],),
        ).fetchall()

        return {
            "complaint_number": complaint["complaint_number"],
            "complaint_status": complaint["complaint_status"],
            "test_attempts": [
                dict(record) for record in test_records
            ],
        }
