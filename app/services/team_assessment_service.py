
from typing import Any

from app.repositories.team_assessment_repository import (
    get_pending_team_assessments,
    submit_team_assessment,
    get_team_assessment_history,
)
from app.schemas.team_assessment import TeamAssessmentCreate


def fetch_pending_team_assessments() -> dict[str, Any]:
    """Fetch complaints waiting for team assessment."""

    return get_pending_team_assessments()


def record_team_assessment(
    data: TeamAssessmentCreate,
) -> dict[str, Any]:
    """Validate and record a team's technical assessment."""

    assessment_data = data.model_dump()

    assessment_data["complaint_number"] = (
        assessment_data["complaint_number"].strip().upper()
    )

    assessment_data["assessed_by"] = (
        assessment_data["assessed_by"].strip()
    )

    assessment_data["assessment_findings"] = (
        assessment_data["assessment_findings"].strip()
    )

    assessment_data["recommended_action"] = (
        assessment_data["recommended_action"].strip()
    )

    return submit_team_assessment(**assessment_data)


def fetch_team_assessment_history(
    complaint_number: str,
) -> dict[str, Any] | None:
    """Fetch assessment history for a complaint."""

    return get_team_assessment_history(
        complaint_number.strip().upper()
    )
