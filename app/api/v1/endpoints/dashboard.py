
from fastapi import APIRouter, Query

from app.services.dashboard_service import (
    fetch_dashboard_summary,
    fetch_status_counts,
    fetch_priority_counts,
    fetch_decision_counts,
    fetch_team_workload,
    fetch_recent_complaints,
)


router = APIRouter(
    prefix="/api/v1/dashboard",
    tags=["Dashboard"],
)


@router.get("/summary")
def dashboard_summary():
    return {
        "message": "Dashboard summary retrieved successfully",
        "data": fetch_dashboard_summary(),
    }


@router.get("/status-counts")
def dashboard_status_counts():
    return {
        "message": "Complaint status counts retrieved successfully",
        "data": fetch_status_counts(),
    }


@router.get("/priority-counts")
def dashboard_priority_counts():
    return {
        "message": "Complaint priority counts retrieved successfully",
        "data": fetch_priority_counts(),
    }


@router.get("/decision-counts")
def dashboard_decision_counts():
    return {
        "message": "Complaint decision counts retrieved successfully",
        "data": fetch_decision_counts(),
    }


@router.get("/team-workload")
def dashboard_team_workload():
    return {
        "message": "Team workload retrieved successfully",
        "data": fetch_team_workload(),
    }


@router.get("/recent-complaints")
def dashboard_recent_complaints(
    limit: int = Query(default=10, ge=1, le=100),
):
    return {
        "message": "Recent complaints retrieved successfully",
        "data": fetch_recent_complaints(limit=limit),
    }
