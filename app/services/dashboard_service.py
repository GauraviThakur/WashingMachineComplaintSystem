
from app.repositories.dashboard_repository import (
    get_dashboard_summary,
    get_status_counts,
    get_priority_counts,
    get_decision_counts,
    get_team_workload,
    get_recent_complaints,
)


def fetch_dashboard_summary() -> dict:
    return get_dashboard_summary()


def fetch_status_counts() -> list[dict]:
    return get_status_counts()


def fetch_priority_counts() -> list[dict]:
    return get_priority_counts()


def fetch_decision_counts() -> list[dict]:
    return get_decision_counts()


def fetch_team_workload() -> list[dict]:
    return get_team_workload()


def fetch_recent_complaints(limit: int = 10) -> list[dict]:
    return get_recent_complaints(limit=limit)
