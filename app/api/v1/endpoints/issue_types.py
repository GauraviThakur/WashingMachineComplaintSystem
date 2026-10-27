
from fastapi import APIRouter, Query

from app.schemas.issue_type import IssueTypeResponse
from app.services.issue_type_service import list_issue_types


router = APIRouter(
    prefix="/issue-types",
    tags=["Issue Types"],
)


@router.get("/")
def get_issue_types(
    category_id: int | None = Query(default=None, ge=1),
) -> dict:
    """Return active issue types, optionally filtered by category."""

    issue_types = list_issue_types(category_id)

    return {
        "message": "Issue types retrieved successfully",
        "total": len(issue_types),
        "category_id": category_id,
        "issue_types": [
            issue_type.model_dump(mode="json")
            for issue_type in issue_types
        ],
    }
