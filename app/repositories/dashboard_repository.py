
from app.database.connection import get_db_connection


def get_dashboard_summary() -> dict:
    query = """
        SELECT
            COUNT(*) AS total_complaints,
            COUNT(*) FILTER (
                WHERE complaint_status <> 'CLOSED'
            ) AS open_complaints,
            COUNT(*) FILTER (
                WHERE complaint_status = 'CLOSED'
            ) AS closed_complaints,
            COUNT(*) FILTER (
                WHERE is_repeat_complaint = TRUE
            ) AS repeat_complaints
        FROM complaints;
    """

    with get_db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            row = cursor.fetchone()

    return dict(row)


def get_status_counts() -> list[dict]:
    query = """
        SELECT
            complaint_status AS status,
            COUNT(*) AS count
        FROM complaints
        GROUP BY complaint_status
        ORDER BY complaint_status;
    """

    with get_db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()

    return [dict(row) for row in rows]


def get_priority_counts() -> list[dict]:
    query = """
        SELECT
            priority,
            COUNT(*) AS count
        FROM complaints
        GROUP BY priority
        ORDER BY
            CASE priority
                WHEN 'CRITICAL' THEN 1
                WHEN 'HIGH' THEN 2
                WHEN 'MEDIUM' THEN 3
                WHEN 'LOW' THEN 4
                ELSE 5
            END;
    """

    with get_db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()

    return [dict(row) for row in rows]


def get_decision_counts() -> list[dict]:
    query = """
        WITH latest_decisions AS (
            SELECT DISTINCT ON (cd.complaint_id)
                cd.complaint_id,
                cd.decision_type
            FROM complaint_decisions cd
            ORDER BY
                cd.complaint_id,
                cd.decided_at DESC NULLS LAST,
                cd.decision_id DESC
        )
        SELECT
            decision_type,
            COUNT(*) AS count
        FROM latest_decisions
        GROUP BY decision_type
        ORDER BY decision_type;
    """

    with get_db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()

    return [dict(row) for row in rows]


def get_team_workload() -> list[dict]:
    query = """
        WITH latest_assignments AS (
            SELECT DISTINCT ON (ca.complaint_id)
                ca.complaint_id,
                ca.team_id,
                ca.assignment_status,
                ca.assigned_to,
                ca.assigned_at
            FROM complaint_assignments ca
            ORDER BY
                ca.complaint_id,
                ca.assigned_at DESC NULLS LAST,
                ca.assignment_id DESC
        )
        SELECT
            t.team_id,
            t.team_name,
            COUNT(la.complaint_id) FILTER (
                WHERE c.complaint_status <> 'CLOSED'
            ) AS open_complaints,
            COUNT(la.complaint_id) FILTER (
                WHERE c.complaint_status = 'CLOSED'
            ) AS closed_complaints,
            COUNT(la.complaint_id) AS total_assigned_complaints
        FROM teams t
        LEFT JOIN latest_assignments la
            ON la.team_id = t.team_id
        LEFT JOIN complaints c
            ON c.complaint_id = la.complaint_id
        WHERE t.is_active = TRUE
        GROUP BY t.team_id, t.team_name
        ORDER BY open_complaints DESC, t.team_name;
    """

    with get_db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()

    return [dict(row) for row in rows]


def get_recent_complaints(limit: int = 10) -> list[dict]:
    query = """
        SELECT
            c.complaint_id,
            c.complaint_number,
            m.serial_number,
            m.model_number,
            c.customer_name,
            c.reported_issue,
            c.priority,
            c.complaint_status,
            c.is_repeat_complaint,
            c.registered_at,
            COALESCE(
                inspection_issue.issue_type_name,
                complaint_issue.issue_type_name
            ) AS issue_type_name
        FROM complaints c
        JOIN machines m
            ON m.machine_id = c.machine_id
        LEFT JOIN issue_types complaint_issue
            ON complaint_issue.issue_type_id = c.issue_type_id
        LEFT JOIN LATERAL (
            SELECT it.issue_type_name
            FROM inspections i
            LEFT JOIN issue_types it
                ON it.issue_type_id = i.issue_type_id
            WHERE i.complaint_id = c.complaint_id
              AND i.issue_type_id IS NOT NULL
            ORDER BY
                i.inspected_at DESC NULLS LAST,
                i.inspection_id DESC
            LIMIT 1
        ) inspection_issue ON TRUE
        ORDER BY c.registered_at DESC, c.complaint_id DESC
        LIMIT %s;
    """

    with get_db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, (limit,))
            rows = cursor.fetchall()

    return [dict(row) for row in rows]
